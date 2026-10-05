"""Aggregations for the admin dashboard. Plain SQL so beginners can follow it."""
from .database import get_db

TARGET = 500  # campaign goal: registrations in 7 days


def _pct(part: float, whole: float) -> float:
    return round(100 * part / whole, 1) if whole else 0.0


def build_stats() -> dict:
    with get_db() as db:
        total = db.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        visits_total = db.execute("SELECT COUNT(*) FROM visits").fetchone()[0]

        # --- intent split -------------------------------------------------- #
        intent = {"High Intent": 0, "Medium Intent": 0, "Low Intent": 0}
        for r in db.execute("SELECT category, COUNT(*) c FROM students GROUP BY category"):
            if r["category"] in intent:
                intent[r["category"]] = r["c"]

        # --- channels: visits vs registrations -> conversion --------------- #
        visits_by = {r["channel"]: r["c"] for r in db.execute("SELECT channel, COUNT(*) c FROM visits GROUP BY channel")}
        regs_by = {}
        for r in db.execute(
            """SELECT channel, COUNT(*) c,
                      SUM(CASE WHEN category='High Intent' THEN 1 ELSE 0 END) hi
               FROM students GROUP BY channel"""
        ):
            regs_by[r["channel"]] = (r["c"], r["hi"] or 0)
        channels = []
        for ch in sorted(set(visits_by) | set(regs_by)):
            regs, hi = regs_by.get(ch, (0, 0))
            visits = max(visits_by.get(ch, 0), regs)  # a registration implies at least one visit
            channels.append({
                "channel": ch, "visits": visits, "registrations": regs,
                "conversion": _pct(regs, visits), "high_intent": hi,
            })
        channels.sort(key=lambda c: c["registrations"], reverse=True)

        # --- colleges ------------------------------------------------------ #
        top_colleges = [
            {"college": r["college"], "registrations": r["c"], "avg_score": round(r["a"] or 0)}
            for r in db.execute(
                """SELECT college, COUNT(*) c, AVG(score) a FROM students
                   GROUP BY college ORDER BY c DESC, a DESC LIMIT 8"""
            )
        ]

        # --- branch / year / goal ------------------------------------------ #
        by_branch = [
            {
                "branch": r["branch"], "registrations": r["c"], "avg_score": round(r["a"] or 0),
                "high_intent_rate": _pct(r["hi"] or 0, r["c"]),
            }
            for r in db.execute(
                """SELECT branch, COUNT(*) c, AVG(score) a,
                          SUM(CASE WHEN category='High Intent' THEN 1 ELSE 0 END) hi
                   FROM students GROUP BY branch ORDER BY c DESC"""
            )
        ]
        by_year = [
            {"year": r["year"], "registrations": r["c"], "avg_score": round(r["a"] or 0)}
            for r in db.execute("SELECT year, COUNT(*) c, AVG(score) a FROM students GROUP BY year ORDER BY c DESC")
        ]
        by_goal = [
            {"goal": r["career_goal"], "registrations": r["c"]}
            for r in db.execute("SELECT career_goal, COUNT(*) c FROM students GROUP BY career_goal ORDER BY c DESC")
        ]

        # --- daily registrations ------------------------------------------- #
        daily = [
            {"date": r["d"], "registrations": r["c"]}
            for r in db.execute(
                "SELECT date(created_at) d, COUNT(*) c FROM students GROUP BY d ORDER BY d"
            )
        ]

        # --- referrals ----------------------------------------------------- #
        referred = db.execute("SELECT COUNT(*) FROM students WHERE referred_by IS NOT NULL").fetchone()[0]
        ambassadors = db.execute(
            """SELECT COUNT(DISTINCT referred_by) FROM students WHERE referred_by IS NOT NULL"""
        ).fetchone()[0]

    days_active = max(1, len(daily))
    return {
        "total_registrations": total,
        "total_visits": max(visits_total, total),
        "conversion_rate": _pct(total, max(visits_total, total)),
        "intent": intent,
        "high_intent_rate": _pct(intent["High Intent"], total),
        "by_channel": channels,
        "top_colleges": top_colleges,
        "by_branch": by_branch,
        "by_year": by_year,
        "by_goal": by_goal,
        "daily": daily,
        "avg_per_day": round(total / days_active, 1),
        "referral": {
            "total_referred": referred,
            "referral_share": _pct(referred, total),
            "active_ambassadors": ambassadors,
        },
        "goal": {"target": TARGET, "current": total, "percent": min(100, _pct(total, TARGET))},
    }


def build_leaderboard(limit: int = 10) -> list:
    """Ambassadors ranked by successful referral registrations (ties: more link clicks)."""
    with get_db() as db:
        rows = db.execute(
            """
            SELECT s.name, s.college, s.referral_code,
                   (SELECT COUNT(*) FROM students r WHERE r.referred_by = s.referral_code) AS referrals,
                   (SELECT COUNT(*) FROM visits v WHERE v.ref = s.referral_code) AS clicks
            FROM students s
            WHERE referrals > 0
            ORDER BY referrals DESC, clicks DESC, s.id ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [
        {
            "rank": i + 1, "name": r["name"], "college": r["college"], "code": r["referral_code"],
            "referrals": r["referrals"], "clicks": max(r["clicks"], r["referrals"]),
        }
        for i, r in enumerate(rows)
    ]
