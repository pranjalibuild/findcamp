"""
remind.py — Railway cron job
Runs daily at 8am UTC via Railway cron schedule: 0 8 * * *
Checks camps table and sends 48h and 24h reminders before registration opens.
"""

import os
import sqlite3
import resend
from datetime import datetime, timedelta, timezone

DB_PATH = "findcamp.db"
RESEND_API_KEY = os.environ["RESEND_API_KEY"]
FROM_EMAIL = "Findcamp <hello@findcamp.co>"

resend.api_key = RESEND_API_KEY


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def send_reminder(to_email: str, camp_name: str, reg_date: str, hours_until: int):
    urgency = "tomorrow" if hours_until <= 24 else "in 2 days"
    subject = f"⏰ {camp_name} registration opens {urgency}!"

    html_body = f"""
    <div style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:24px;">
      <h1 style="color:#2d6a4f;">⏰ Registration opens {urgency}!</h1>
      <p style="color:#333;font-size:16px;">
        <strong>{camp_name}</strong> registration opens on <strong>{reg_date}</strong>.
      </p>
      <p style="color:#555;">Spots fill up fast — make sure you're ready to register as soon as it opens.</p>
      <div style="background:#f0f7f4;border-radius:8px;padding:16px;margin:24px 0;">
        <p style="margin:0;color:#2d6a4f;font-weight:bold;">✅ Quick checklist:</p>
        <ul style="color:#555;margin:8px 0;">
          <li>Check if you got a reply to your enquiry email</li>
          <li>Have your payment method ready</li>
          <li>Set an alarm for 8am on registration day</li>
          <li>Visit the camp website early — spots go fast</li>
        </ul>
      </div>
      <hr style="border:none;border-top:1px solid #eee;margin:24px 0;">
      <p style="color:#999;font-size:13px;">Sent by <a href="https://findcamp.co" style="color:#2d6a4f;">findcamp.co</a> · Find camps before they fill up.</p>
    </div>
    """

    resend.Emails.send({
        "from": FROM_EMAIL,
        "to": to_email,
        "subject": subject,
        "html": html_body
    })
    print(f"Sent {hours_until}h reminder to {to_email} for {camp_name}")


def run():
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    in_24h = (now + timedelta(hours=24)).date().isoformat()
    in_48h = (now + timedelta(hours=48)).date().isoformat()

    with get_db() as conn:
        camps = conn.execute("""
            SELECT * FROM camps
            WHERE registration_open_date IS NOT NULL
            AND (reminder_48h_sent = 0 OR reminder_24h_sent = 0)
        """).fetchall()

        for camp in camps:
            reg_date = camp["registration_open_date"]

            if reg_date == in_48h and not camp["reminder_48h_sent"]:
                try:
                    send_reminder(camp["email"], camp["camp_name"], reg_date, 48)
                    conn.execute("UPDATE camps SET reminder_48h_sent = 1 WHERE id = ?", (camp["id"],))
                    conn.commit()
                except Exception as e:
                    print(f"Error sending 48h reminder: {e}")

            if reg_date == in_24h and not camp["reminder_24h_sent"]:
                try:
                    send_reminder(camp["email"], camp["camp_name"], reg_date, 24)
                    conn.execute("UPDATE camps SET reminder_24h_sent = 1 WHERE id = ?", (camp["id"],))
                    conn.commit()
                except Exception as e:
                    print(f"Error sending 24h reminder: {e}")

    print(f"Reminder check complete at {now.isoformat()}")


if __name__ == "__main__":
    run()
