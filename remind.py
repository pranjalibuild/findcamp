"""
remind.py — Findcamp daily reminder script
Runs daily via Railway cron at 8am UTC.
Sends 48h and 24h reminders before camp registration opens.
"""

import os
import sqlite3
import resend
from datetime import datetime, timedelta

DB_PATH = "findcamp.db"
RESEND_API_KEY = os.environ["RESEND_API_KEY"]
FROM_EMAIL = "Findcamp <hello@findcamp.co>"

resend.api_key = RESEND_API_KEY


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def send_reminder(to_email: str, camp_name: str, reg_date: str, hours: int):
    urgency = "tomorrow" if hours == 48 else "TODAY"
    emoji = "⏰" if hours == 48 else "🚨"

    html_body = f"""
    <div style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:24px;">
      <h1 style="color:#2d6a4f;">{emoji} Camp registration opens {urgency}!</h1>
      <p style="color:#333;font-size:18px;">
        <strong>{camp_name}</strong> registration opens on <strong>{reg_date}</strong>.
      </p>
      <p style="color:#555;">Spots fill up fast — don't wait. Check your previous Findcamp email for the enquiry emails and website link.</p>
      <div style="background:#f0f7f4;border-radius:8px;padding:16px;margin:24px 0;">
        <p style="margin:0;color:#2d6a4f;font-weight:bold;">💡 Quick tip</p>
        <p style="margin:8px 0 0;color:#555;">If you haven't already, send your enquiry email now so you're top of mind when registration opens.</p>
      </div>
      <hr style="border:none;border-top:1px solid #eee;margin:24px 0;">
      <p style="color:#999;font-size:13px;">Sent by <a href="https://findcamp.co" style="color:#2d6a4f;">findcamp.co</a> · Find camps before they fill up.</p>
    </div>
    """

    resend.Emails.send({
        "from": FROM_EMAIL,
        "to": to_email,
        "subject": f"{emoji} {camp_name} registration opens {urgency}!",
        "html": html_body
    })
    print(f"Sent {hours}h reminder to {to_email} for {camp_name}")


def run():
    today = datetime.utcnow().date()
    date_48h = (today + timedelta(days=2)).strftime("%Y-%m-%d")
    date_24h = (today + timedelta(days=1)).strftime("%Y-%m-%d")

    with get_db() as conn:
        camps_48h = conn.execute("""
            SELECT * FROM camps WHERE registration_open_date = ? AND reminder_48h_sent = 0
        """, (date_48h,)).fetchall()

        for camp in camps_48h:
            try:
                send_reminder(camp["email"], camp["camp_name"], camp["registration_open_date"], 48)
                conn.execute("UPDATE camps SET reminder_48h_sent = 1 WHERE id = ?", (camp["id"],))
                conn.commit()
            except Exception as e:
                print(f"Failed 48h reminder for camp {camp['id']}: {e}")

        camps_24h = conn.execute("""
            SELECT * FROM camps WHERE registration_open_date = ? AND reminder_24h_sent = 0
        """, (date_24h,)).fetchall()

        for camp in camps_24h:
            try:
                send_reminder(camp["email"], camp["camp_name"], camp["registration_open_date"], 24)
                conn.execute("UPDATE camps SET reminder_24h_sent = 1 WHERE id = ?", (camp["id"],))
                conn.commit()
            except Exception as e:
                print(f"Failed 24h reminder for camp {camp['id']}: {e}")

    print(f"Done. {len(camps_48h)} 48h and {len(camps_24h)} 24h reminders sent.")


if __name__ == "__main__":
    run()
