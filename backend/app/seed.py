"""
Demo data generator.

IMPORTANT: this data is SIMULATED so the dashboard can be demonstrated before real
traffic exists. Every row is flagged is_demo=1 and can be wiped from the dashboard.
The distributions below are assumptions for the demo, not real NxtWave results.
"""
import json
import random
from datetime import datetime, timedelta

from . import ai_service, scoring
from .database import get_db

COLLEGES = [
    ("Amrita Vishwa Vidyapeetham", 5), ("VIT Vellore", 5), ("SRM Institute of Science and Technology", 4),
    ("CBIT Hyderabad", 4), ("JNTU Hyderabad", 4), ("Vasavi College of Engineering", 3),
    ("KL University", 3), ("PSG College of Technology", 3), ("Anna University", 3),
    ("NIT Warangal", 2), ("Manipal Institute of Technology", 2), ("Sathyabama University", 2),
    ("GITAM University", 2), ("RV College of Engineering", 2), ("Kakatiya Institute of Technology", 1),
]
FIRST = ["Aarav", "Ananya", "Rahul", "Sneha", "Karthik", "Priya", "Rohan", "Divya", "Arjun", "Meera",
         "Vikram", "Lakshmi", "Sai", "Nikhil", "Pooja", "Harsha", "Tejaswini", "Aditya", "Kavya", "Manoj",
         "Ishita", "Varun", "Swathi", "Ravi", "Neha", "Charan", "Bhavana", "Dinesh", "Keerthi", "Yash"]
LAST = ["Reddy", "Sharma", "Nair", "Kumar", "Iyer", "Patel", "Rao", "Menon", "Gupta", "Singh", "Das", "Naidu"]

BRANCHES = [("CSE", 38), ("IT", 14), ("AI & ML / Data Science", 14), ("ECE", 17), ("EEE", 6), ("Mechanical", 7), ("Civil", 3), ("Other", 1)]
YEARS = [("Final Year", 62), ("Third Year", 24), ("Second Year", 10), ("First Year", 4)]
LEVELS = [("Beginner", 58), ("Intermediate", 32), ("Advanced", 10)]
GOALS = [("Placement preparation", 38), ("Building AI projects", 28), ("Learning AI fundamentals", 22), ("Exploring AI careers", 12)]

# (channel, share of registrations, visit->registration rate)  -- demo assumptions
CHANNEL_MODEL = [("Referral", 0.34, 0.34), ("WhatsApp", 0.30, 0.22), ("LinkedIn", 0.14, 0.13),
                 ("Instagram", 0.12, 0.07), ("Direct", 0.10, 0.10)]


def _pick(options):
    return random.choices([o for o, _ in options], weights=[w for _, w in options])[0]


def seed_demo_data(n: int = 140) -> dict:
    random.seed(2026)  # same demo data every time
    now = datetime.utcnow()
    made, used_emails, used_codes = [], set(), set()

    with get_db() as db:
        # Already seeded? Do nothing.
        if db.execute("SELECT 1 FROM students WHERE is_demo = 1 LIMIT 1").fetchone():
            return {"created_students": 0, "message": "Demo data already loaded."}
        used_codes = {r[0] for r in db.execute("SELECT referral_code FROM students")}
        used_emails = {r[0] for r in db.execute("SELECT email FROM students")}

        ambassadors: list[str] = []  # codes of students who can receive referrals
        channels = [c for c, _, _ in CHANNEL_MODEL]
        weights = [w for _, w, _ in CHANNEL_MODEL]

        for i in range(n):
            # Registrations ramp up across the 7 days (later days busier).
            day_offset = int(7 * (1 - random.random() ** 1.6))
            created = now - timedelta(days=day_offset, hours=random.randint(0, 23), minutes=random.randint(0, 59))

            name = f"{random.choice(FIRST)} {random.choice(LAST)}"
            s = {
                "name": name,
                "college": _pick(COLLEGES),
                "branch": _pick(BRANCHES),
                "year": _pick(YEARS),
                "ai_level": _pick(LEVELS),
                "career_goal": _pick(GOALS),
            }
            email = f"{name.lower().replace(' ', '.')}{i}@demo.example"
            while email in used_emails:
                email = f"x{i}{random.randint(0, 99)}@demo.example"
            used_emails.add(email)

            channel = random.choices(channels, weights=weights)[0]
            referred_by = None
            if channel == "Referral":
                if len(ambassadors) < 3:
                    channel = "WhatsApp"  # first few students cannot be referred yet
                else:
                    # A few ambassadors bring most referrals (realistic power-law).
                    referred_by = random.choices(ambassadors, weights=[1 / (k + 1) for k in range(len(ambassadors))])[0]
            s["referred_by"] = referred_by

            result = scoring.compute_score(s)
            ai = ai_service.fallback_analysis(s, result)  # no API calls for demo data

            first = "".join(c for c in name.split()[0].upper() if c.isalpha())
            code = f"{first}_AI2026"
            while code in used_codes:
                code = f"{first}{random.randint(10, 99)}_AI2026"
            used_codes.add(code)

            db.execute(
                """INSERT INTO students
                   (name,email,phone,college,branch,year,ai_level,career_goal,channel,referral_code,referred_by,
                    score,category,score_reason,persona,outreach,ai_source,is_demo,created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1,?)""",
                (name, email, str(random.randint(6000000000, 9999999999)), s["college"], s["branch"], s["year"],
                 s["ai_level"], s["career_goal"], channel, code, referred_by, result["score"], result["category"],
                 ai["reason"], json.dumps(ai["persona"]), json.dumps(ai["outreach"]), "fallback",
                 created.strftime("%Y-%m-%d %H:%M:%S")),
            )
            made.append(channel)
            # Higher-intent students are more likely to become ambassadors.
            if result["score"] >= 60 or random.random() < 0.15:
                ambassadors.append(code)  # insertion order: early joiners get more referrals

        # Visits per channel = registrations / conversion-rate (demo assumption).
        for channel, _, rate in CHANNEL_MODEL:
            if channel == "Referral":
                continue  # referral visits are created per-ambassador below
            regs = made.count(channel)
            for _ in range(int(regs / rate)):
                created = now - timedelta(days=random.randint(0, 6), hours=random.randint(0, 23))
                db.execute(
                    "INSERT INTO visits (channel, ref, is_demo, created_at) VALUES (?,?,1,?)",
                    (channel, None, created.strftime("%Y-%m-%d %H:%M:%S")),
                )
        # Give each ambassador some link clicks so the leaderboard shows clicks too.
        for code, count in db.execute(
            "SELECT referred_by, COUNT(*) FROM students WHERE is_demo=1 AND referred_by IS NOT NULL GROUP BY referred_by"
        ).fetchall():
            for _ in range(int(count / 0.34)):  # clicks include the ones that converted
                db.execute("INSERT INTO visits (channel, ref, is_demo) VALUES ('Referral', ?, 1)", (code,))

    return {"created_students": n, "message": f"Loaded {n} simulated demo students."}
