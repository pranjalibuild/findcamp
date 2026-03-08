"""
Findcamp API — main.py
Run with: python3 -m uvicorn main:app --reload
"""

import os
import re
import json
import base64
import sqlite3
import anthropic
import resend
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "findcamp.db"
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
RESEND_API_KEY = os.environ["RESEND_API_KEY"]
FROM_EMAIL = "Findcamp <hello@findcamp.co>"
DAILY_SEARCH_CAP = 50

resend.api_key = RESEND_API_KEY


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def setup_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                ip_address TEXT,
                searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS daily_counts (
                date TEXT PRIMARY KEY,
                count INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS camps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                camp_name TEXT,
                postal_code TEXT,
                registration_open_date TEXT,
                reminder_48h_sent INTEGER DEFAULT 0,
                reminder_24h_sent INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)


@app.on_event("startup")
def on_startup():
    setup_db()


def check_gates(email: str, ip: str):
    with get_db() as conn:
        row = conn.execute("""
            SELECT COUNT(*) as cnt FROM searches
            WHERE ip_address = ? AND searched_at > datetime('now', '-24 hours')
        """, (ip,)).fetchone()
        if row["cnt"] > 0:
            raise HTTPException(status_code=429, detail="You've already searched from this device today. Check back tomorrow!")

        row = conn.execute("SELECT COUNT(*) as cnt FROM searches WHERE email = ?", (email,)).fetchone()
        if row["cnt"] > 0:
            raise HTTPException(status_code=429, detail="We've already sent results to this email. Check your inbox!")

        today = datetime.utcnow().date().isoformat()
        conn.execute("INSERT OR IGNORE INTO daily_counts (date, count) VALUES (?, 0)", (today,))
        row = conn.execute("SELECT count FROM daily_counts WHERE date = ?", (today,)).fetchone()
        if row and row["count"] >= DAILY_SEARCH_CAP:
            raise HTTPException(status_code=503, detail="Findcamp is at capacity for today. Check back tomorrow!")


def record_search(email: str, ip: str):
    today = datetime.utcnow().date().isoformat()
    with get_db() as conn:
        conn.execute("INSERT INTO searches (email, ip_address) VALUES (?, ?)", (email, ip))
        conn.execute("UPDATE daily_counts SET count = count + 1 WHERE date = ?", (today,))
        conn.commit()


def search_camps(postal_code: str, radius_km: int, age: int, season: str, camp_type: str) -> list:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""
    Find {season} 2026 {camp_type} camps within {radius_km}km of postal code {postal_code} in Canada for a child aged {age}.

    Return a JSON array only — no other text. Each item must have these exact keys:
    - name: camp name (string)
    - address: full address (string or null)
    - website: URL (string or null)
    - contact_email: email address (string or null)
    - contact_phone: phone number (string or null)
    - age_range: e.g. "5-12" (string or null)
    - cost_per_week: e.g. "$350 CAD" (string or null)
    - registration_date: YYYY-MM-DD format (string or null)
    - registration_open: true or false (boolean)
    - distance_km: approximate km from {postal_code} (number or null)
    - notes: any important notes (string or null)

    Only include camps that accept age {age}. Sort by registration_date ascending, null dates at end.
    Return ONLY valid JSON array, nothing else.
    """

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=3000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": prompt}]
    )

    raw = " ".join(block.text for block in response.content if hasattr(block, "text"))

    match = re.search(r'\[.*\]', raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return [{"name": "Results", "notes": raw, "registration_date": None,
             "contact_email": None, "website": None, "address": None,
             "age_range": None, "cost_per_week": None, "registration_open": False,
             "distance_km": None, "contact_phone": None}]


def generate_ics(camp_name: str, reg_date_str: str) -> bytes:
    try:
        reg_date = datetime.strptime(reg_date_str, "%Y-%m-%d")
    except ValueError:
        return None

    uid = f"findcamp-{re.sub(r'[^a-z0-9]', '-', camp_name.lower())}-{reg_date_str}@findcamp.co"
    now = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    event_date = reg_date.strftime("%Y%m%d")

    ics = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Findcamp//findcamp.co//EN
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{now}
DTSTART;TZID=America/Vancouver:{event_date}T080000
DTEND;TZID=America/Vancouver:{event_date}T083000
SUMMARY:🏕️ {camp_name} registration opens today!
DESCRIPTION:Registration for {camp_name} opens today. Don't wait — spots fill fast!
BEGIN:VALARM
TRIGGER:-PT0M
ACTION:DISPLAY
DESCRIPTION:Camp registration opens now!
END:VALARM
END:VEVENT
END:VCALENDAR"""

    return ics.encode("utf-8")


def send_results_email(to_email: str, camps: list, postal_code: str, radius_km: int, season: str, camp_type: str):
    camp_list_html = ""
    for i, camp in enumerate(camps, 1):
        reg_date = camp.get("registration_date")
        reg_status = "✅ Open now" if camp.get("registration_open") else f"📅 Opens {reg_date}" if reg_date else "📅 Date TBD"
        distance = f" · {camp.get('distance_km')}km away" if camp.get("distance_km") else ""

        camp_list_html += f"""
        <div style="background:#f9f9f9;border-radius:8px;padding:16px;margin-bottom:16px;">
          <h3 style="margin:0 0 8px;color:#2d6a4f;">{i}. {camp.get('name','Unknown')}</h3>
          <p style="margin:4px 0;color:#555;">📍 {camp.get('address','Address TBD')}{distance}</p>
          <p style="margin:4px 0;color:#555;">👧 Ages: {camp.get('age_range','TBD')} · 💰 {camp.get('cost_per_week','Cost TBD')}</p>
          <p style="margin:4px 0;color:#555;">{reg_status}</p>
          {f'<p style="margin:4px 0;"><a href="{camp.get("website")}" style="color:#2d6a4f;">Visit website →</a></p>' if camp.get('website') else ''}
          {f'<p style="margin:4px 0;color:#555;">✉️ {camp.get("contact_email")}</p>' if camp.get('contact_email') else ''}
          {f'<p style="margin:4px 0;color:#555;">📞 {camp.get("contact_phone")}</p>' if camp.get('contact_phone') else ''}
          {f'<p style="margin:4px 0;color:#777;font-size:13px;">{camp.get("notes")}</p>' if camp.get('notes') else ''}
        </div>"""

    enquiry_html = ""
    for camp in camps:
        if not camp.get("contact_email"):
            continue
        enquiry_html += f"""
        <div style="background:#f0f7f4;border-left:4px solid #2d6a4f;padding:16px;margin-bottom:16px;border-radius:0 8px 8px 0;">
          <p style="margin:0 0 4px;font-weight:bold;color:#2d6a4f;">✉️ {camp.get('name')}</p>
          <p style="margin:0 0 8px;font-size:13px;color:#555;">To: {camp.get('contact_email')} · Subject: Enquiry about {season} 2026 Camp Programs</p>
          <div style="background:white;padding:12px;border-radius:4px;font-size:13px;color:#333;line-height:1.6;white-space:pre-wrap;">Hi there,

I'm looking for a {season} 2026 {camp_type} camp for my child near {postal_code} and came across {camp.get('name')}. I'd love to learn more.

Could you please share:
- Available sessions and dates for {season} 2026
- Registration process and any waitlist options
- Cost per week and what's included

Thank you so much — looking forward to hearing from you!

[Your name]
[Your phone number]</div>
        </div>"""

    if not enquiry_html:
        enquiry_html = "<p style='color:#777;'>No contact emails found. Visit camp websites directly to enquire.</p>"

    camps_with_dates = [c for c in camps if c.get("registration_date")]
    calendar_note = ""
    if camps_with_dates:
        calendar_note = """
        <div style="background:#fff8e1;border-radius:8px;padding:16px;margin-bottom:24px;">
          <p style="margin:0;color:#555;">📅 <strong>Calendar reminders attached!</strong> Open the .ics files to add registration day events to your calendar. We'll also email you 48h and 24h before each registration opens.</p>
        </div>"""

    html_body = f"""
    <div style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:24px;">
      <h1 style="color:#2d6a4f;">🏕️ Your Findcamp Results</h1>
      <p style="color:#555;">{season} {camp_type} camps within {radius_km}km of {postal_code}</p>
      {calendar_note}
      <h2 style="color:#2d6a4f;border-bottom:2px solid #eee;padding-bottom:8px;">Camps Found</h2>
      {camp_list_html}
      <h2 style="color:#2d6a4f;border-bottom:2px solid #eee;padding-bottom:8px;margin-top:32px;">Ready-to-Send Enquiry Emails</h2>
      <p style="color:#555;font-size:14px;">Copy and send these to get answers fast. Most camps reply within 24 hours.</p>
      {enquiry_html}
      <hr style="border:none;border-top:1px solid #eee;margin:24px 0;">
      <p style="color:#999;font-size:13px;">Sent by <a href="https://findcamp.co" style="color:#2d6a4f;">findcamp.co</a> · Find camps before they fill up.</p>
    </div>"""

    attachments = []
    for camp in camps_with_dates:
        ics_data = generate_ics(camp["name"], camp["registration_date"])
        if ics_data:
            safe_name = re.sub(r'[^a-z0-9]', '-', camp["name"].lower())[:30]
            attachments.append({
                "filename": f"{safe_name}-registration.ics",
                "content": base64.b64encode(ics_data).decode("utf-8"),
                "type": "text/calendar"
            })

    email_params = {
        "from": FROM_EMAIL,
        "to": to_email,
        "subject": f"🏕️ Your {season} camp results near {postal_code}",
        "html": html_body,
    }
    if attachments:
        email_params["attachments"] = attachments

    resend.Emails.send(email_params)


def store_camps(email: str, postal_code: str, camps: list):
    with get_db() as conn:
        for camp in camps:
            if camp.get("registration_date"):
                conn.execute("""
                    INSERT INTO camps (email, camp_name, postal_code, registration_open_date)
                    VALUES (?, ?, ?, ?)
                """, (email, camp.get("name", "")[:200], postal_code, camp["registration_date"]))
        conn.commit()


class SearchRequest(BaseModel):
    email: str
    postal_code: str
    radius_km: int = 10
    age: int
    season: str
    camp_type: str


@app.post("/search")
async def search(request: Request, body: SearchRequest):
    ip = request.client.host
    check_gates(body.email, ip)
    camps = search_camps(body.postal_code, body.radius_km, body.age, body.season, body.camp_type)
    record_search(body.email, ip)
    send_results_email(body.email, camps, body.postal_code, body.radius_km, body.season, body.camp_type)
    store_camps(body.email, body.postal_code, camps)
    return {"status": "success", "message": f"Results sent to {body.email}"}


@app.get("/health")
def health():
    return {"status": "ok"}
