"""
End-to-end smoke test. Run from the backend/ folder:   python smoke_test.py
Uses a temporary database, so it never touches your real growthos.db.
"""
import os
import tempfile

os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ["GEMINI_API_KEY"] = ""  # force fallback mode so the test is offline

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

PAYLOAD = {
    "name": "Rahul Verma", "email": "rahul@example.com", "phone": "9876543210",
    "college": "CBIT Hyderabad", "branch": "CSE", "year": "Final Year",
    "ai_level": "Beginner", "career_goal": "Placement preparation",
}


def check(label, cond):
    print(("PASS" if cond else "FAIL"), "-", label)
    if not cond:
        raise SystemExit(1)


with TestClient(app) as client:
    check("health endpoint", client.get("/api/health").json()["status"] == "ok")

    # 1. register + scoring + persona + outreach
    r = client.post("/api/register", json=PAYLOAD)
    check("register returns 200", r.status_code == 200)
    s = r.json()
    check("lead score is high for final-year beginner placement CSE", s["score"] >= 75 and s["category"] == "High Intent")
    check("persona generated", s["persona"]["pain_point"] and s["persona"]["motivation"])
    check("outreach mentions first name", s["outreach"]["whatsapp"].startswith("Hi Rahul"))
    check("referral code format", s["referral_code"] == "RAHUL_AI2026")

    # 2. duplicate email returns same record
    r2 = client.post("/api/register", json=PAYLOAD).json()
    check("duplicate email handled", r2["already_registered"] and r2["id"] == s["id"])

    # 3. validation errors
    bad = client.post("/api/register", json={**PAYLOAD, "email": "nope", "phone": "123"})
    check("validation rejects bad input (422)", bad.status_code == 422)

    # 4. outreach changes with profile
    other = client.post("/api/register", json={**PAYLOAD, "name": "Meera Nair", "email": "m@example.com",
                                                "branch": "Mechanical", "ai_level": "Advanced",
                                                "career_goal": "Exploring AI careers", "year": "Second Year"}).json()
    check("outreach differs by branch/goal/level", other["outreach"]["whatsapp"] != s["outreach"]["whatsapp"])
    check("low/medium intent for second-year explorer", other["category"] != "High Intent")

    # 5. referral flow
    client.post("/api/track-visit", json={"ref": s["referral_code"]})
    friend = client.post("/api/register", json={**PAYLOAD, "name": "Sneha Rao", "email": "sneha@example.com",
                                                 "ref": s["referral_code"]}).json()
    check("referred student channel = Referral", friend["channel"] == "Referral")
    lb = client.get("/api/leaderboard").json()["leaders"]
    check("leaderboard ranks ambassador #1", lb and lb[0]["code"] == s["referral_code"] and lb[0]["referrals"] == 1)
    me = client.get(f"/api/students/{s['id']}").json()
    check("student sees referral count + rank", me["referral_count"] == 1 and me["rank"] == 1)

    # 6. demo data + analytics + insights
    check("seed demo data", client.post("/api/admin/seed-demo").json()["created_students"] > 0)
    a = client.get("/api/analytics").json()
    check("analytics totals", a["total_registrations"] > 100 and sum(a["intent"].values()) == a["total_registrations"])
    check("conversion rate is a sane percentage", 0 < a["conversion_rate"] <= 100)
    ins = client.get("/api/insights").json()
    check("insights returned", len(ins["insights"]) >= 3)
    for i in ins["insights"]:
        print("   -", i["title"])
    leads = client.get("/api/leads", params={"category": "High Intent"}).json()["leads"]
    check("leads filter works", leads and all(l["category"] == "High Intent" for l in leads))
    cleared = client.delete("/api/admin/demo-data").json()
    check("demo data cleared", cleared["deleted_students"] > 0)

print("\nAll checks passed.")
