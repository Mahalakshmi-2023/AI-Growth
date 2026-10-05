# AI GrowthOS: AI-Powered Student Acquisition & Conversion Platform

Built for the **NxtWave Growth Intern Challenge**: get **500 final-year engineering students** to register for the free workshop *"Build Your First AI Project in 60 Minutes"* in **7 days** with a **₹2,000** budget.

**Stack:** React + Tailwind CSS · Python FastAPI · SQLite · Google Gemini API · Recharts

```
Student discovers workshop → Landing page → Registration → AI persona → AI lead score
        → Personalised message → Referral code → Leaderboard → Admin analytics + AI insights
```

---

## 1. Folder structure

```
ai-growthos/
├── README.md
├── .gitignore
├── backend/
│   ├── requirements.txt
│   ├── .env.example            <- copy to .env
│   ├── smoke_test.py           <- automated end-to-end test
│   └── app/
│       ├── main.py             <- API endpoints
│       ├── database.py         <- SQLite schema + connection
│       ├── schemas.py          <- input validation
│       ├── scoring.py          <- lead scoring engine (0-100)
│       ├── ai_service.py       <- Gemini calls + fallback simulation
│       ├── analytics.py        <- dashboard + leaderboard queries
│       └── seed.py             <- simulated demo data
└── frontend/
    ├── package.json
    ├── vite.config.js          <- proxies /api to the backend
    ├── tailwind.config.js
    └── src/
        ├── App.jsx, main.jsx, api.js, index.css
        └── pages/ Landing.jsx · Welcome.jsx · Leaderboard.jsx · Admin.jsx
```

## 2. How each feature works

| # | Feature | Where | How |
|---|---------|-------|-----|
| 1 | Landing page | `Landing.jsx` | Hero, intro, why join, benefits, how it works, 8-field registration form with validation |
| 2 | Persona analyzer | `ai_service.analyze_student` | Gemini writes profile, pain point, motivation. Without a key, a rule-based simulation does it |
| 3 | Lead scoring | `scoring.py` | Transparent weighted model (year, goal, AI level, branch, referral) gives 0-100 and High/Medium/Low. Gemini explains the reason |
| 4 | Personalised outreach | `ai_service.py` | WhatsApp + email text that changes with **branch, goal and AI level** |
| 5 | Referral system | `main.py`, `analytics.py` | Unique code per student (e.g. `MAHA_AI2026`), `?ref=` links, click and signup tracking, leaderboard |
| 6 | Analytics dashboard | `Admin.jsx` | KPIs, goal progress, intent split, daily trend, channel conversion, colleges, branches, referral performance, lead table |
| 7 | AI campaign insights | `ai_service.generate_insights` | Gemini analyses the aggregated numbers. The fallback computes insights directly from the data |

**Design decisions worth knowing**
- The score *number* is rule-based so it is consistent, explainable and works offline. Gemini is used for language (persona, reason, messages, insights).
- Every AI call has a 12 s timeout and falls back automatically, so the product never breaks mid-demo. The UI labels which mode produced each result.
- Conversion rate = registrations ÷ landing-page visits, tracked per channel via `?src=whatsapp|instagram|linkedin` and `?ref=CODE`.
- The demo data is **simulated** (clearly flagged in the UI) so the dashboard can be shown before real traffic. Its channel conversion rates are my assumptions, not real results.

---

## 3. Windows installation (exact steps)

**Prerequisites:** install [Python 3.10+](https://www.python.org/downloads/) (tick *"Add Python to PATH"*) and [Node.js 18+ LTS](https://nodejs.org/). Check in a new terminal:

```powershell
python --version
node --version
```

### Backend (Terminal 1, PowerShell)

```powershell
cd ai-growthos\backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

*If activation is blocked:* run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then activate again. (In Command Prompt use `.venv\Scripts\activate.bat`.)

Optional: open `backend\.env` and paste your key after `GEMINI_API_KEY=` (free key: https://aistudio.google.com/apikey). Leave it empty to run in fallback simulation mode.

### Frontend (Terminal 2)

```powershell
cd ai-growthos\frontend
npm install
```

## 4. Run the project

**Terminal 1: backend**
```powershell
cd ai-growthos\backend
.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --port 8000
```
API docs: http://localhost:8000/docs

**Terminal 2: frontend**
```powershell
cd ai-growthos\frontend
npm run dev
```
Open **http://localhost:5173**

## 5. Testing steps

**Automated (backend, works offline):**
```powershell
cd ai-growthos\backend
python smoke_test.py
```
Expect `All checks passed.` It covers registration, scoring, personalisation, duplicate emails, validation, referrals, leaderboard, analytics and insights, using a temporary database.

**Manual checklist (browser):**
1. Open `/`, submit the form with a bad phone number such as `123`. You should see a clear error.
2. Register *Rahul Verma, CSE, Final Year, Beginner, Placement preparation*. You should land on the welcome page with a persona, a high-intent score (about 90) and a placement-focused message.
3. Register a second student as *Mechanical, Second Year, Advanced, Exploring AI careers*. The score is lower and the message is different.
4. Copy Rahul's referral link, open it in a private window and register a friend. Rahul's referral count becomes 1 and he appears on `/leaderboard`.
5. Open `/admin`, click **Load demo data**. Charts, AI insights and the lead table fill up.
6. Add `?src=whatsapp` to the landing URL, register, and check the channel appears in the dashboard.
7. Stop the backend and submit the form. You should get a friendly "cannot reach the server" message.

## 6. 3-minute demo video flow

| Time | Show | Say |
|------|------|-----|
| 0:00-0:20 | Problem slide or landing hero | "500 final-year students in 7 days on ₹2,000 means ads won't work. We need organic, targeted growth. So I built GrowthOS." |
| 0:20-0:50 | Landing page scroll, then fill the form | "Messaging is built around the student's real pain: placements without a project." |
| 0:50-1:30 | Welcome page | "Instantly the student gets an AI persona, a workshop-fit score with a reason, and a message personalised by branch, goal and AI level." Register a Mechanical student to show the message change. |
| 1:30-2:00 | Referral code, leaderboard | "Every student becomes an ambassador. This is the zero-cost growth loop, with college-vs-college competition." |
| 2:00-2:40 | Admin dashboard | "Funnel, intent split, channel conversion, top colleges. The AI insights tell the team where to put the ₹2,000." Flag that the data shown is simulated. |
| 2:40-3:00 | Close | "Next: WhatsApp API sending, admin login, A/B-tested copy." |

## 7. Why this solves NxtWave's growth problem

- **The budget rules out paid reach.** ₹2,000 cannot buy 500 sign-ups through ads, so growth has to come from referrals and community channels. GrowthOS builds the referral loop in from the first screen.
- **Not every lead is equal.** Scoring shows the team which registrants are most likely to attend and later convert, so limited follow-up effort goes to high-intent students first.
- **Generic messages get ignored.** Outreach is personalised by branch, goal and AI level, which fits how students actually decide.
- **Spend gets measured.** Per-channel visit-to-registration tracking shows which channel deserves the budget, and the insights panel turns the numbers into actions.

## 8. Known limitations and next steps

- The admin dashboard has **no login**. Add authentication before any real deployment.
- Lead scoring weights are a hypothesis, not trained on real data. Once attendance and enrolment data exists, refit them.
- Outreach messages are generated but not sent. Next step is WhatsApp Business API / email integration.
- No rate limiting or email verification on registration.
- Gemini model names change over time, so set `GEMINI_MODEL` in `.env` if the default stops working.
