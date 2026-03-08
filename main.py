"""
Findcamp API — main.py
Step 1: Get this running locally first. 
Run with: uvicorn main:app --reload
Test with: curl -X POST http://localhost:8000/search -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "city": "Vancouver", "age": 7, "season": "Summer", "camp_type": "Sports"}'
"""

import os
import re
import sqlite3
import anthropic
import resend
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

app = FastAPI()

# ── Config ────────────────────────────────────────────────────────────────────
DB_PATH = "findcamp.db"
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
RESEND_API_KEY = os.environ["RESEND_API_KEY"]
FROM_EMAIL = "Findcamp <hello@findcamp.co>"
DAILY_SEARCH_CAP = 50

resend.api_key = RESEND_API_KEY


# ── Database helpers ──────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets you access columns by name
    return conn


def setup_db():
    """Run once on startup to create tables if they don't exist."""
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
                city TEXT,
                registration_open_date TEXT,
                reminder_48h_sent INTEGER DEFAULT 0,
                reminder_24h_sent INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)


@app.on_event("startup")
def on_startup():
    setup_db()


# ── Gate logic ────────────────────────────────────────────────────────────────
def check_gates(email: str, ip: str):
    """
    Three checks before any Claude API call:
    1. Has this IP searched in the last 24 hours?
    2. Has this email already searched?
    3. Have we hit today's daily cap?
    Raises HTTPException if any gate fails.
    """
    with get_db() as conn:

        # Gate 1: IP check — one search per IP per 24 hours
        row = conn.execute("""
            SELECT COUNT(*) as cnt FROM searches
            WHERE ip_address = ?
            AND searched_at > datetime('now', '-24 hours')
        """, (ip,)).fetchone()
        if row["cnt"] > 0:
            raise HTTPException(
                status_code=429,
                detail="You've already searched from this device today. Check back tomorrow!"
            )

        # Gate 2: Email check — one search per email ever
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM searches WHERE email = ?", (email,)
        ).fetchone()
        if row["cnt"] > 0:
            raise HTTPException(
                status_code=429,
                detail="We've already sent results to this email. Check your inbox!"
            )

        # Gate 3: Daily cap — max 50 searches per day total
        today = datetime.utcnow().date().isoformat()
        conn.execute("""
            INSERT OR IGNORE INTO daily_counts (date, count) VALUES (?, 0)
        """, (today,))
        row = conn.execute(
            "SELECT count FROM daily_counts WHERE date = ?", (today,)
        ).fetchone()
        if row and row["count"] >= DAILY_SEARCH_CAP:
            raise HTTPException(
                status_code=503,
                detail="Findcamp is at capacity for today. Check back tomorrow!"
            )


def record_search(email: str, ip: str):
    """Record the search and increment today's counter after a successful API call."""
    today = datetime.utcnow().date().isoformat()
    with get_db() as conn:
        conn.execute(
            "INSERT INTO searches (email, ip_address) VALUES (?, ?)", (email, ip)
        )
        conn.execute(
            "UPDATE daily_counts SET count = count + 1 WHERE date = ?", (today,)
        )
        conn.commit()


# ── Claude API call ───────────────────────────────────────────────────────────
def search_camps(postal_code: str, radius_km: int, age: int, season: str, camp_type: str) -> str:
    """
    Calls Claude API with web search enabled.
    Searches within the specified radius of the given postal code.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""
    Find {season} 2026 {camp_type} camps within {radius_km}km of postal code {postal_code} in Canada.
    
    Important: Only include camps that are genuinely within {radius_km}km of {postal_code}.
    If a camp's location is unclear, include it but note the uncertainty.

    For each camp return:
    - Camp name
    - Full address
    - Website URL
    - Contact email (if listed)
    - Age range
    - Cost per week (if listed)
    - Registration open date (format: YYYY-MM-DD if possible)
    - Whether registration is currently open
    - Approximate distance from {postal_code}

    Format results as a clear numbered list. Only include camps that accept age {age}.
    Sort by registration open date, earliest first. Put camps with unknown dates at the bottom.
    """

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": prompt}]
    )

    return " ".join(
        block.text for block in response.content
        if hasattr(block, "text")
    )


# ── Email sender ──────────────────────────────────────────────────────────────
def send_results_email(to_email: str, results: str, postal_code: str, radius_km: int, season: str, camp_type: str):
    """Send camp results to parent via Resend."""

    html_body = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 24px;">
      <h1 style="color: #2d6a4f;">🏕️ Your Findcamp Results</h1>
      <p style="color: #555;">Here are the <strong>{season} {camp_type} camps within {radius_km}km of {postal_code}</strong> we found for you.</p>
      <p style="color: #555;">We'll send you a reminder <strong>48 hours and 24 hours</strong> before each camp's registration opens so you never miss the window.</p>
      <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;">
      <div style="white-space: pre-wrap; color: #333; line-height: 1.7;">{results}</div>
      <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;">
      <p style="color: #999; font-size: 13px;">
        You're receiving this because you searched on <a href="https://findcamp.co">findcamp.co</a>.
        Questions? Reply to this email.
      </p>
    </div>
    """

    resend.Emails.send({
        "from": FROM_EMAIL,
        "to": to_email,
        "subject": f"🏕️ Your {season} camp results near {postal_code}",
        "html": html_body
    })


# ── Camp date parser ──────────────────────────────────────────────────────────
def extract_and_store_camps(email: str, postal_code: str, results: str):
    """
    Parse registration dates from results text and store in camps table.
    Simple regex approach — looks for YYYY-MM-DD dates near camp names.
    """
    lines = results.split("\n")
    current_camp = None

    with get_db() as conn:
        for line in lines:
            # Detect camp name lines (numbered list items)
            if re.match(r"^\*?\*?\d+\.", line.strip()):
                current_camp = line.strip()

            # Detect registration date lines
            date_match = re.search(r"(\d{4}-\d{2}-\d{2})", line)
            if date_match and current_camp:
                reg_date = date_match.group(1)
                conn.execute("""
                    INSERT INTO camps (email, camp_name, city, registration_open_date)
                    VALUES (?, ?, ?, ?)
                """, (email, current_camp[:200], postal_code, reg_date))
                current_camp = None  # reset after storing

        conn.commit()


# ── Main endpoint ─────────────────────────────────────────────────────────────
class SearchRequest(BaseModel):
    email: str
    postal_code: str           # e.g. "V3H 2M1" — used as geographic anchor
    radius_km: int = 10        # Default 10km, options: 5 / 10 / 20
    age: int
    season: str                # "Summer" | "Spring" | "Fall" | "Winter"
    camp_type: str             # "Sports" | "Arts" | "STEM" | "Outdoors" | "General"


@app.post("/search")
async def search(request: Request, body: SearchRequest):
    ip = request.client.host

    # Run all three gates before touching the Claude API
    check_gates(body.email, ip)

    # Call Claude — this is the only line that costs money
    results = search_camps(body.postal_code, body.radius_km, body.age, body.season, body.camp_type)

    # Record search only after successful API call
    record_search(body.email, ip)

    # Email results to parent
    send_results_email(body.email, results, body.postal_code, body.radius_km, body.season, body.camp_type)

    # Parse and store camp dates for reminders
    extract_and_store_camps(body.email, body.postal_code, results)

    return {"status": "success", "message": f"Results sent to {body.email}"}


@app.get("/health")
def health():
    return {"status": "ok"}
