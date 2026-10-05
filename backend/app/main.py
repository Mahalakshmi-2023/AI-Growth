"""
AI GrowthOS - FastAPI backend.

Run:  uvicorn app.main:app --reload --port 8000
Docs: http://localhost:8000/docs
"""

import json
import os
import random
import re
import sqlite3
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()  # reads backend/.env

from . import ai_service, analytics, scoring  # noqa: E402
from .database import get_db, init_db  # noqa: E402
from .schemas import CHANNELS, RegisterIn, VisitIn  # noqa: E402


app = FastAPI(title="AI GrowthOS API", version="1.0.0")


# --------------------------------------------------------------------------- #
# CORS
# --------------------------------------------------------------------------- #
# Allow the local React development server and the deployed Vercel frontend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        os.getenv("FRONTEND_URL", ""),
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def normalize_channel(src: Optional[str]) -> str:
    """Map ?src=whatsapp -> 'WhatsApp'. Unknown values become 'Direct'."""
    if src:
        for ch in CHANNELS:
            if ch.lower() == src.strip().lower():
                return ch
    return "Direct"


def make_referral_code(db, name: str) -> str:
    """MAHA_AI2026 style. Adds a number if the code is already taken."""
    first = (
        re.sub(r"[^A-Z]", "", name.strip().split()[0].upper())[:10]
        or "STUDENT"
    )
    code = f"{first}_AI2026"

    while db.execute(
        "SELECT 1 FROM students WHERE referral_code = ?",
        (code,),
    ).fetchone():
        code = f"{first}{random.randint(10, 99)}_AI2026"

    return code


def row_to_student(row) -> dict:
    """Convert a DB row into the JSON the frontend expects."""
    d = dict(row)

    d["persona"] = json.loads(d["persona"]) if d.get("persona") else None
    d["outreach"] = json.loads(d["outreach"]) if d.get("outreach") else None

    d["referral_link"] = (
        f"{os.getenv('FRONTEND_URL', 'http://localhost:5173')}"
        f"/?ref={d['referral_code']}&src=referral"
    )

    return d


def student_with_referral_stats(db, row) -> dict:
    s = row_to_student(row)

    s["referral_count"] = db.execute(
        "SELECT COUNT(*) FROM students WHERE referred_by = ?",
        (s["referral_code"],),
    ).fetchone()[0]

    higher = db.execute(
        """SELECT COUNT(*) FROM (
               SELECT referred_by, COUNT(*) c
               FROM students
               WHERE referred_by IS NOT NULL
               GROUP BY referred_by
           )
           WHERE c > ?""",
        (s["referral_count"],),
    ).fetchone()[0]

    s["rank"] = higher + 1 if s["referral_count"] > 0 else None

    return s


# --------------------------------------------------------------------------- #
# Public endpoints
# --------------------------------------------------------------------------- #
@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "gemini_enabled": ai_service.gemini_enabled(),
    }


@app.post("/api/track-visit")
def track_visit(visit: VisitIn):
    """Called once per browser session when the landing page loads."""
    ref = visit.ref.strip().upper() if visit.ref else None
    channel = "Referral" if ref else normalize_channel(visit.src)

    with get_db() as db:
        db.execute(
            "INSERT INTO visits (channel, ref) VALUES (?, ?)",
            (channel, ref),
        )

    return {"ok": True}


@app.get("/api/referral/{code}")
def check_referral(code: str):
    """Lets the landing page show 'Invited by <name>' when a ?ref= link is opened."""
    with get_db() as db:
        row = db.execute(
            "SELECT name, college FROM students WHERE referral_code = ?",
            (code.strip().upper(),),
        ).fetchone()

    if not row:
        raise HTTPException(404, "Unknown referral code")

    return {
        "name": row["name"],
        "college": row["college"],
    }


@app.post("/api/register")
def register(payload: RegisterIn):
    """
    Full growth pipeline in one call:
    register -> score -> AI persona -> personalised outreach -> referral code.
    """
    with get_db() as db:

        # Same email twice? Return the existing record instead of an error.
        existing = db.execute(
            "SELECT * FROM students WHERE email = ?",
            (payload.email,),
        ).fetchone()

        if existing:
            s = student_with_referral_stats(db, existing)
            s["already_registered"] = True
            return s

        # Valid referral code?
        # Credit the ambassador and mark the channel.
        referred_by = None

        if payload.ref:
            code = payload.ref.strip().upper()

            if db.execute(
                "SELECT 1 FROM students WHERE referral_code = ?",
                (code,),
            ).fetchone():
                referred_by = code

        channel = (
            "Referral"
            if referred_by
            else normalize_channel(payload.src)
        )

        student = payload.model_dump(exclude={"src", "ref"})
        student["referred_by"] = referred_by

        # 1) AI lead scoring (rule-based number)
        result = scoring.compute_score(student)

        # 2) AI persona + reason + outreach
        # Gemini, or fallback simulation
        ai = ai_service.analyze_student(student, result)

        code = make_referral_code(db, payload.name)

        try:
            cur = db.execute(
                """INSERT INTO students
                   (name, email, phone, college, branch, year, ai_level,
                    career_goal, channel, referral_code, referred_by,
                    score, category, score_reason, persona, outreach, ai_source)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    student["name"],
                    student["email"],
                    student["phone"],
                    student["college"],
                    student["branch"],
                    student["year"],
                    student["ai_level"],
                    student["career_goal"],
                    channel,
                    code,
                    referred_by,
                    result["score"],
                    result["category"],
                    ai["reason"],
                    json.dumps(ai["persona"]),
                    json.dumps(ai["outreach"]),
                    ai["ai_source"],
                ),
            )

        except sqlite3.IntegrityError:
            raise HTTPException(
                409,
                "This email is already registered.",
            )

        row = db.execute(
            "SELECT * FROM students WHERE id = ?",
            (cur.lastrowid,),
        ).fetchone()

        s = student_with_referral_stats(db, row)

        s["score_breakdown"] = [
            {"label": label, "points": points}
            for label, points in result["breakdown"]
        ]

        s["already_registered"] = False

        return s


@app.get("/api/students/{student_id}")
def get_student(student_id: int):
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM students WHERE id = ?",
            (student_id,),
        ).fetchone()

        if not row:
            raise HTTPException(
                404,
                "Student not found",
            )

        return student_with_referral_stats(db, row)


@app.get("/api/leaderboard")
def leaderboard(limit: int = Query(10, ge=1, le=50)):
    return {
        "leaders": analytics.build_leaderboard(limit)
    }


# --------------------------------------------------------------------------- #
# Admin endpoints (no auth in the MVP - see README "Next steps")
# --------------------------------------------------------------------------- #
@app.get("/api/analytics")
def get_analytics():
    return analytics.build_stats()


@app.get("/api/insights")
def get_insights():
    """Feature 7: AI campaign insights generated from the live numbers."""
    return ai_service.generate_insights(
        analytics.build_stats()
    )


@app.get("/api/leads")
def get_leads(
    category: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
):
    sql = "SELECT * FROM students"
    params: list = []

    if category in (
        "High Intent",
        "Medium Intent",
        "Low Intent",
    ):
        sql += " WHERE category = ?"
        params.append(category)

    sql += " ORDER BY score DESC, id DESC LIMIT ?"
    params.append(limit)

    with get_db() as db:
        return {
            "leads": [
                row_to_student(r)
                for r in db.execute(sql, params).fetchall()
            ]
        }


@app.post("/api/admin/seed-demo")
def seed_demo():
    """Load realistic demo data so the dashboard has something to show."""
    from .seed import seed_demo_data

    return seed_demo_data()


@app.delete("/api/admin/demo-data")
def clear_demo():
    with get_db() as db:
        s = db.execute(
            "DELETE FROM students WHERE is_demo = 1"
        ).rowcount

        v = db.execute(
            "DELETE FROM visits WHERE is_demo = 1"
        ).rowcount

    return {
        "deleted_students": s,
        "deleted_visits": v,
    }