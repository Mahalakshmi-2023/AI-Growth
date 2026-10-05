"""
AI layer: persona, score reason, personalised outreach, campaign insights.

Every function tries Google Gemini first. If there is no API key, the call fails,
or Gemini returns something unusable, we silently fall back to a deterministic
simulation so the product never breaks during a demo.
"""
import json
import os

import requests

GEMINI_TIMEOUT = 12  # seconds - keep registration snappy


# --------------------------------------------------------------------------- #
# Gemini plumbing
# --------------------------------------------------------------------------- #
def gemini_enabled() -> bool:
    return bool(os.getenv("GEMINI_API_KEY", "").strip())


def _call_gemini(prompt: str):
    """Call Gemini and parse its JSON answer. Returns None on ANY problem."""
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        return None
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    try:
        resp = requests.post(
            url,
            headers={"x-goog-api-key": key, "Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.7,
                    "responseMimeType": "application/json",  # ask for clean JSON
                },
            },
            timeout=GEMINI_TIMEOUT,
        )
        resp.raise_for_status()
        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(text)
    except Exception as exc:  # network error, quota, bad JSON ... -> fallback
        print(f"[ai_service] Gemini unavailable, using fallback: {exc}")
        return None


# --------------------------------------------------------------------------- #
# Student analysis (persona + score reason + outreach) - ONE Gemini call
# --------------------------------------------------------------------------- #
GOAL_INFO = {
    "Placement preparation": {
        "pain": "Placement season is close and the resume has no practical AI project to talk about in interviews.",
        "motivation": "Stand out in interviews and improve job opportunities with a real, demo-able project.",
        "hook": "Since you are preparing for placements, this workshop gives you a project you can put on your resume and explain in interviews.",
        "subject": "A resume-ready AI project in 60 minutes",
    },
    "Building AI projects": {
        "pain": "Has the curiosity to build but no guided path from idea to a working AI project.",
        "motivation": "Ship a portfolio-ready AI project instead of only watching tutorials.",
        "hook": "You want to build AI projects - in this workshop you will go from zero to a working one in a single hour, live.",
        "subject": "Build your first AI project, live, in 60 minutes",
    },
    "Learning AI fundamentals": {
        "pain": "AI feels huge and confusing, and it is unclear where to start.",
        "motivation": "Build a solid foundation by learning through doing, not theory dumps.",
        "hook": "AI fundamentals make most sense when you build something - we will learn the core ideas by creating a small project together.",
        "subject": "Learn AI basics by building something in 60 minutes",
    },
    "Exploring AI careers": {
        "pain": "Unsure whether an AI career is the right path and what the work really looks like.",
        "motivation": "Try AI hands-on for one hour before committing months to it.",
        "hook": "Wondering if AI is the right career for you? Spend 60 minutes building a real project and find out first-hand.",
        "subject": "Try an AI career for 60 minutes - free",
    },
}

LEVEL_LINE = {
    "Beginner": "No prior AI experience needed - everything is step by step.",
    "Intermediate": "You already know the basics, so we will focus on putting it together end to end.",
    "Advanced": "You will move fast - the focus is on shipping something deployable, not theory.",
}

BRANCH_HOOK = {
    "CSE": "Your coding background means you will pick this up faster than you expect.",
    "IT": "Your coding background means you will pick this up faster than you expect.",
    "AI & ML / Data Science": "You have studied the theory - now package it into a project recruiters can actually click and try.",
    "ECE": "AI plus electronics/signals is a rare combination that employers value.",
    "EEE": "AI plus electrical/embedded knowledge is a rare combination that employers value.",
    "Mechanical": "AI skills will set you apart from most peers in core branches.",
    "Civil": "AI skills will set you apart from most peers in core branches.",
    "Other": "AI skills will set you apart from most peers in your branch.",
}


def _first_name(name: str) -> str:
    return name.strip().split()[0].title() if name.strip() else "there"


def fallback_analysis(student: dict, scoring: dict) -> dict:
    """Deterministic 'AI simulation' that still personalises on branch, goal and level."""
    goal = GOAL_INFO[student["career_goal"]]
    first = _first_name(student["name"])
    level_text = {"Beginner": "beginner in AI", "Intermediate": "intermediate in AI", "Advanced": "advanced in AI"}[student["ai_level"]]

    profile = f"{student['year']} {student['branch']} student at {student['college']}, {level_text}, focused on {student['career_goal'].lower()}."

    reason_bits = []
    if student["year"] == "Final Year":
        reason_bits.append("final-year timeline creates urgency")
    elif student["year"] == "Third Year":
        reason_bits.append("still has time to build a strong portfolio")
    if student["ai_level"] == "Beginner":
        reason_bits.append("beginner level means this workshop fills a real gap")
    if student["career_goal"] in ("Placement preparation", "Building AI projects"):
        reason_bits.append(f"goal ({student['career_goal'].lower()}) matches the workshop outcome directly")
    if student.get("referred_by"):
        reason_bits.append("came through a peer referral")
    reason = (
        "Student " + "; ".join(reason_bits) + "." if reason_bits
        else "Interest is exploratory, so the workshop is a lower-priority fit for now."
    )
    reason = reason[0].upper() + reason[1:]

    whatsapp = (
        f"Hi {first},\n{goal['hook']} {BRANCH_HOOK[student['branch']]} "
        f"{LEVEL_LINE[student['ai_level']]}\nSave your seat for the free 'Build Your First AI Project in 60 Minutes' workshop."
    )
    email_body = (
        f"Hi {first},\n\nThanks for registering for 'Build Your First AI Project in 60 Minutes'.\n\n"
        f"{goal['hook']} {BRANCH_HOOK[student['branch']]} {LEVEL_LINE[student['ai_level']]}\n\n"
        "Tip: invite two friends from your college with your referral link - ambassadors who bring the most "
        "friends get featured on the leaderboard.\n\nSee you in the workshop!\nTeam NxtWave"
    )
    return {
        "persona": {"profile": profile, "pain_point": goal["pain"], "motivation": goal["motivation"]},
        "reason": reason,
        "outreach": {"whatsapp": whatsapp, "email_subject": goal["subject"], "email_body": email_body},
    }


def analyze_student(student: dict, scoring: dict) -> dict:
    """Return persona, score reason and outreach. Adds 'ai_source': 'gemini' | 'fallback'."""
    prompt = f"""You are a growth analyst at NxtWave, an Indian edtech company.
A student registered for the free workshop "Build Your First AI Project in 60 Minutes".

Student data:
- Name: {student['name']}
- College: {student['college']}
- Branch: {student['branch']}
- Year: {student['year']}
- AI experience: {student['ai_level']}
- Career goal: {student['career_goal']}
- Lead score (already computed, 0-100): {scoring['score']} ({scoring['category']})

Return ONLY JSON with exactly this shape:
{{
  "persona": {{"profile": "one sentence", "pain_point": "one sentence", "motivation": "one sentence"}},
  "reason": "one sentence explaining why this lead has this score",
  "outreach": {{
    "whatsapp": "3-4 short lines, starts with 'Hi <first name>,', references their branch, goal AND AI level, friendly, no emojis spam, ends with a call to register",
    "email_subject": "under 9 words",
    "email_body": "short email, 4-6 sentences, personalised, mentions inviting friends via referral link"
  }}
}}
Rules: never write a generic message; the text must clearly change with branch, goal and AI level."""
    data = _call_gemini(prompt)

    fb = fallback_analysis(student, scoring)
    if data:
        try:
            p, o = data["persona"], data["outreach"]
            result = {
                "persona": {k: str(p[k]).strip() for k in ("profile", "pain_point", "motivation")},
                "reason": str(data["reason"]).strip(),
                "outreach": {k: str(o[k]).strip() for k in ("whatsapp", "email_subject", "email_body")},
            }
            if all(result["persona"].values()) and result["reason"] and all(result["outreach"].values()):
                result["ai_source"] = "gemini"
                return result
        except (KeyError, TypeError):
            print("[ai_service] Gemini returned unexpected shape, using fallback")
    fb["ai_source"] = "fallback"
    return fb


# --------------------------------------------------------------------------- #
# Campaign insights
# --------------------------------------------------------------------------- #
def fallback_insights(stats: dict) -> list:
    """Insights computed directly from the data (so they are always true to the numbers)."""
    total = stats["total_registrations"]
    if total == 0:
        return [{"type": "info", "title": "No data yet", "text": "Share the landing page or load demo data to see AI insights."}]

    out = []

    branches = [b for b in stats["by_branch"] if b["registrations"] >= 3]
    if branches:
        best = max(branches, key=lambda b: b["high_intent_rate"])
        out.append({
            "type": "branch",
            "title": f"{best['branch']} students are your strongest segment",
            "text": f"{best['high_intent_rate']}% of {best['branch']} registrants are high-intent "
                    f"(avg score {best['avg_score']}). Tailor outreach copy and college-group targeting to this branch first.",
        })

    chans = [c for c in stats["by_channel"] if c["visits"] >= 10]
    if chans:
        best = max(chans, key=lambda c: c["conversion"])
        worst = min(chans, key=lambda c: c["conversion"])
        out.append({
            "type": "channel",
            "title": f"{best['channel']} converts best ({best['conversion']}%)",
            "text": f"{best['channel']} turns visitors into registrations at {best['conversion']}% versus "
                    f"{worst['conversion']}% for {worst['channel']}. Put the ₹2,000 budget behind {best['channel']}-style distribution "
                    f"(e.g. boosting posts in college groups) rather than broad paid ads.",
        })

    ref = stats["referral"]
    if ref["referral_share"] > 0:
        out.append({
            "type": "referral",
            "title": f"Referrals drive {ref['referral_share']}% of registrations",
            "text": f"{ref['total_referred']} students joined through ambassador links. Recruit one ambassador per college "
                    "and reward the top 3 on the leaderboard - it costs almost nothing compared to ads.",
        })

    fy = next((y for y in stats["by_year"] if y["year"] == "Final Year"), None)
    if fy:
        share = round(100 * fy["registrations"] / total)
        out.append({
            "type": "year",
            "title": f"Final-year students are {share}% of sign-ups",
            "text": f"Final years average a lead score of {fy['avg_score']}. Keep focusing outreach on final-year placement "
                    "messaging - it is the most urgent audience for this workshop.",
        })

    goal = stats["goal"]
    pace_needed = max(0, goal["target"] - total)
    out.append({
        "type": "pace",
        "title": f"{total}/{goal['target']} registrations ({round(100*total/goal['target'])}% of goal)",
        "text": f"{pace_needed} more registrations needed. At the current average of {stats['avg_per_day']} per day, "
                f"you will hit about {round(stats['avg_per_day'] * 7)} in 7 days - "
                + ("on track." if stats['avg_per_day'] * 7 >= goal['target'] else "boost referral pushes and WhatsApp group sharing to close the gap."),
    })
    return out


def generate_insights(stats: dict) -> dict:
    """Ask Gemini to analyse the aggregated numbers; fall back to computed insights."""
    summary = {
        "total_registrations": stats["total_registrations"],
        "conversion_rate_percent": stats["conversion_rate"],
        "intent_split": stats["intent"],
        "by_channel": stats["by_channel"],
        "by_branch": stats["by_branch"],
        "by_year": stats["by_year"],
        "referral": stats["referral"],
        "top_colleges": stats["top_colleges"][:5],
        "target": stats["goal"],
    }
    prompt = f"""You are a growth analyst. Campaign: free workshop "Build Your First AI Project in 60 Minutes",
target 500 final-year engineering student registrations in 7 days, budget Rs 2000.
Here is the aggregated campaign data (JSON):
{json.dumps(summary)}

Return ONLY JSON: {{"insights": [{{"title": "short headline", "text": "1-2 sentences with a concrete, data-backed action"}}]}}
Give exactly 5 insights. Use only numbers present in the data. Never invent figures."""
    data = _call_gemini(prompt)
    if data:
        try:
            items = [
                {"type": "ai", "title": str(i["title"]).strip(), "text": str(i["text"]).strip()}
                for i in data["insights"][:6]
            ]
            if items:
                return {"source": "gemini", "insights": items}
        except (KeyError, TypeError):
            pass
    return {"source": "fallback", "insights": fallback_insights(stats)}
