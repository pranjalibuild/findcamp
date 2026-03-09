# Findcamp

**Find camps before they fill up.**

[findcamp.co](https://findcamp.co)

Every year, parents miss camp registration because they didn't know it was opening. Spots fill within hours. Findcamp solves that — find nearby camps, send enquiries, and get reminded before registration opens. No setup required.

---

## What it does

1. **Finds real camps near you** — enter a postal code or zip, your child's age, and camp type. Findcamp uses Claude AI with live web search to find camps in real time.
2. **Sends you an email with everything you need** — camp details, contact info, distance, registration status, and pricing.
3. **Writes enquiry emails for you** — each result includes a ready-to-send email, pre-addressed to the camp and personalized with your child's age. Copy, fill in your name, send.
4. **Attaches ICS calendar reminders** — open the .ics files to add registration day events to your calendar.
5. **Emails you before registration opens** — automated 48h and 24h reminder emails so you never miss a spot.

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite + Tailwind (built with Lovable) |
| Backend | FastAPI (Python) |
| AI | Anthropic Claude API with web search tool |
| Email | Resend |
| Reminder cron | Railway (separate service, runs daily at 8am UTC) |
| Database | SQLite |
| Hosting | Netlify (frontend), Railway (backend) |
| Domain | Namecheap, DNS verified via Resend |

---

## Architecture

```
User (findcamp.co)
    |
    v
React frontend (Netlify)
    |
    POST /search
    v
FastAPI backend (Railway)
    |
    +-- Rate limiting (3 searches per IP/email)
    |
    +-- Claude API (web_search tool)
    |       Finds camps, returns structured JSON
    |
    +-- Resend API
    |       Sends HTML email with camp cards,
    |       enquiry emails, ICS attachments
    |
    +-- SQLite
            Stores camps with registration dates
            for reminder cron job

Railway cron (noble-dream service)
    Runs daily at 8am UTC
    Checks for camps opening in 24h or 48h
    Sends reminder emails via Resend
```

---

## Running locally

**Prerequisites:** Python 3.10+, Node.js 18+

**Backend**

```bash
git clone https://github.com/pranjalibuild/findcamp
cd findcamp
pip install fastapi uvicorn anthropic resend python-dotenv
```

Create a `.env` file:

```
ANTHROPIC_API_KEY=your_key_here
RESEND_API_KEY=your_key_here
FROM_EMAIL=hello@yourdomain.com
```

```bash
uvicorn main:app --reload
```

**Frontend**

```bash
npm install
npm run dev
```

Update the API URL in the frontend to point to `http://localhost:8000`.

---

## API endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/search` | POST | Find camps and send results email |
| `/reset-email` | POST | Reset search gates for an email (testing) |
| `/health` | GET | Health check |

**Search request body:**
```json
{
  "email": "parent@example.com",
  "zip_or_postal": "V3E 2M1",
  "radius_km": 10,
  "age": 7,
  "season": "Summer",
  "camp_type": "Sports, Arts"
}
```

---

## Rate limiting

Findcamp uses three gates to protect against API cost overruns:

- 3 searches per IP address per 24 hours
- 3 searches per email address ever
- 50 searches per day across all users (~$7.50/day max API cost)

---

## Design decisions

**Why ICS files instead of Google Calendar API?**
No OAuth required. ICS works with every calendar app on every device. Faster to ship, less friction for users.

**Why copy-paste enquiry emails instead of Gmail drafts?**
No Google OAuth, no permissions, no setup. Parents can copy and send from any email client.

**Why SQLite instead of Postgres?**
Registration reminders are a lightweight read/write operation. SQLite on Railway is free and sufficient for this use case.

**Why a separate Railway service for cron?**
Keeps the API service stateless and the reminder logic independently deployable and debuggable.

---

## Deployment

**Backend (Railway)**
- Start command: `python3 -m uvicorn main:app --host 0.0.0.0 --port $PORT`
- Environment variables: `ANTHROPIC_API_KEY`, `RESEND_API_KEY`, `FROM_EMAIL`

**Cron (Railway — separate service)**
- Start command: `python3 remind.py`
- Cron schedule: `0 8 * * *` (8am UTC daily)
- Environment variables: `RESEND_API_KEY`, `FROM_EMAIL`

**Frontend (Netlify)**
- Build command: `npm run build`
- Publish directory: `dist`

---

## Built by

A product manager who got tired of missing camp registration.

Built in one day during Lovable's SheBuilds IWD 2026 hackathon.

---

## License

MIT
