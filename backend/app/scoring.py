"""
AI Lead Scoring Engine.

Design choice: the NUMBER is computed by a transparent, rule-based model so the
score is consistent, explainable and works without an API key. Gemini is then used
to write a human-friendly REASON for the score (see ai_service.py).

Score = base + year + goal + AI level + branch + referral bonus   (capped at 100)
The weights encode one growth hypothesis: the students who benefit most from a
"first AI project" workshop are final-year students who are beginners and want
placements or projects - so they are the most likely to show up and convert.
"""

YEAR_POINTS = {"Final Year": 25, "Third Year": 17, "Second Year": 8, "First Year": 3}
GOAL_POINTS = {
    "Placement preparation": 25,
    "Building AI projects": 24,
    "Learning AI fundamentals": 16,
    "Exploring AI careers": 10,
}
LEVEL_POINTS = {"Beginner": 20, "Intermediate": 15, "Advanced": 8}


def _branch_points(branch: str) -> int:
    if branch in ("CSE", "IT", "AI & ML / Data Science"):
        return 15
    if branch in ("ECE", "EEE"):
        return 10
    return 6


def compute_score(student: dict) -> dict:
    """Return {'score': int, 'category': str, 'breakdown': [(label, points), ...]}."""
    parts = [
        ("Base", 5),
        (f"Year: {student['year']}", YEAR_POINTS.get(student["year"], 0)),
        (f"Goal: {student['career_goal']}", GOAL_POINTS.get(student["career_goal"], 0)),
        (f"AI level: {student['ai_level']}", LEVEL_POINTS.get(student["ai_level"], 0)),
        (f"Branch: {student['branch']}", _branch_points(student["branch"])),
    ]
    # Students who arrive through a friend's referral trust the invite more.
    if student.get("referred_by"):
        parts.append(("Referred by a peer", 5))

    score = min(100, sum(p for _, p in parts))
    return {"score": score, "category": category_for(score), "breakdown": parts}


def category_for(score: int) -> str:
    if score >= 75:
        return "High Intent"
    if score >= 50:
        return "Medium Intent"
    return "Low Intent"
