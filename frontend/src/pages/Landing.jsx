import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../api.js";

const BRANCHES = ["CSE", "IT", "AI & ML / Data Science", "ECE", "EEE", "Mechanical", "Civil", "Other"];
const YEARS = ["Final Year", "Third Year", "Second Year", "First Year"];
const LEVELS = ["Beginner", "Intermediate", "Advanced"];
const GOALS = ["Placement preparation", "Building AI projects", "Learning AI fundamentals", "Exploring AI careers"];

const WHY = [
  { icon: "💼", title: "Stand out in placements", text: "Recruiters ask for projects, not certificates. Leave with one you can demo and explain." },
  { icon: "🛠️", title: "Build, don't just watch", text: "No theory marathon. You build a working AI project live, step by step." },
  { icon: "🚀", title: "Zero experience needed", text: "Never written an AI line of code? Perfect. The workshop starts from the very beginning." },
];

const BENEFITS = [
  "A working AI project for your resume and GitHub",
  "Clear understanding of how real AI applications are built",
  "Live, guided build you can follow along on your laptop",
  "A roadmap for what to learn next in AI",
  "100% free, 60 minutes, online",
];

const STEPS = [
  { n: "1", title: "Register", text: "Fill the 1-minute form below." },
  { n: "2", title: "Get your AI plan", text: "See your personalised student profile and workshop message instantly." },
  { n: "3", title: "Join & build", text: "Attend the live session and build your first AI project in 60 minutes." },
  { n: "4", title: "Invite friends", text: "Share your referral code and climb the college leaderboard." },
];

const empty = { name: "", email: "", phone: "", college: "", branch: "", year: "", ai_level: "", career_goal: "" };

export default function Landing() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const ref = params.get("ref");
  const src = params.get("src");

  const [form, setForm] = useState(empty);
  const [inviter, setInviter] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Count one visit per browser session, and show "Invited by ..." for referral links.
  useEffect(() => {
    const key = `visit:${ref || ""}:${src || ""}`;
    if (!sessionStorage.getItem(key)) {
      sessionStorage.setItem(key, "1");
      api.trackVisit({ ref, src }).catch(() => {});
    }
    if (ref) api.checkReferral(ref).then(setInviter).catch(() => setInviter(null));
  }, [ref, src]);

  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const student = await api.register({ ...form, ref, src });
      navigate(`/welcome/${student.id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      {/* HERO */}
      <section className="bg-gradient-to-b from-brand-900 via-brand-700 to-brand-600 text-white">
        <div className="mx-auto max-w-6xl px-4 py-16 text-center md:py-24">
          <span className="inline-block rounded-full bg-white/15 px-4 py-1 text-sm font-medium">
            Free live workshop · For engineering students
          </span>
          <h1 className="mx-auto mt-6 max-w-3xl text-4xl font-extrabold leading-tight md:text-6xl">
            Build Your First AI Project in 60 Minutes
          </h1>
          <p className="mx-auto mt-5 max-w-2xl text-lg text-indigo-100">
            Final-year placements are around the corner. Walk out of one hour with a real AI project you can show recruiters.
          </p>
          <a href="#register" className="mt-8 inline-block rounded-xl bg-white px-8 py-4 text-lg font-bold text-brand-700 shadow-lg transition hover:scale-105">
            Reserve my free seat →
          </a>
          <div className="mt-10 grid grid-cols-3 gap-3 text-sm md:mx-auto md:max-w-lg">
            {[["60 min", "Live session"], ["₹0", "Completely free"], ["0", "Experience needed"]].map(([a, b]) => (
              <div key={b} className="rounded-xl bg-white/10 px-3 py-3">
                <div className="text-xl font-bold">{a}</div>
                <div className="text-indigo-100">{b}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* INTRO */}
      <section className="mx-auto max-w-4xl px-4 py-16 text-center">
        <h2 className="text-3xl font-bold text-slate-900">What is this workshop?</h2>
        <p className="mt-4 text-lg text-slate-600">
          A hands-on, beginner-friendly session where you build a complete AI project from scratch, guided live. It is designed
          for engineering students who want practical AI experience, not slides.
        </p>
      </section>

      {/* WHY JOIN */}
      <section className="mx-auto max-w-6xl px-4 pb-16">
        <h2 className="text-center text-3xl font-bold text-slate-900">Why students join</h2>
        <div className="mt-8 grid gap-6 md:grid-cols-3">
          {WHY.map((w) => (
            <div key={w.title} className="card text-center">
              <div className="text-4xl">{w.icon}</div>
              <h3 className="mt-3 text-lg font-bold">{w.title}</h3>
              <p className="mt-2 text-slate-600">{w.text}</p>
            </div>
          ))}
        </div>
      </section>

      {/* BENEFITS */}
      <section className="bg-white py-16">
        <div className="mx-auto max-w-3xl px-4">
          <h2 className="text-center text-3xl font-bold text-slate-900">What you get</h2>
          <ul className="mt-8 space-y-3">
            {BENEFITS.map((b) => (
              <li key={b} className="flex items-start gap-3 rounded-xl bg-slate-50 px-4 py-3">
                <span className="mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-full bg-emerald-100 text-sm text-emerald-700">✓</span>
                <span className="font-medium text-slate-700">{b}</span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="mx-auto max-w-6xl px-4 py-16">
        <h2 className="text-center text-3xl font-bold text-slate-900">How it works</h2>
        <div className="mt-8 grid gap-6 md:grid-cols-4">
          {STEPS.map((s) => (
            <div key={s.n} className="card">
              <div className="grid h-10 w-10 place-items-center rounded-full bg-brand-600 font-bold text-white">{s.n}</div>
              <h3 className="mt-3 font-bold">{s.title}</h3>
              <p className="mt-1 text-sm text-slate-600">{s.text}</p>
            </div>
          ))}
        </div>
      </section>

      {/* REGISTRATION */}
      <section id="register" className="bg-gradient-to-b from-slate-50 to-brand-50 py-16">
        <div className="mx-auto max-w-2xl px-4">
          <h2 className="text-center text-3xl font-bold text-slate-900">Reserve your free seat</h2>
          <p className="mt-2 text-center text-slate-600">Takes about a minute. You will instantly get your personalised AI plan.</p>

          {inviter && (
            <div className="mt-6 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-center text-sm text-emerald-800">
              🎉 You were invited by <b>{inviter.name}</b> from {inviter.college}
            </div>
          )}

          <form onSubmit={onSubmit} className="card mt-6 space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="label">Full name</label>
                <input className="input" required value={form.name} onChange={set("name")} placeholder="Rahul Verma" />
              </div>
              <div>
                <label className="label">Email</label>
                <input className="input" type="email" required value={form.email} onChange={set("email")} placeholder="you@college.edu" />
              </div>
              <div>
                <label className="label">Phone number</label>
                <input className="input" required value={form.phone} onChange={set("phone")} placeholder="98765 43210" inputMode="tel" />
              </div>
              <div>
                <label className="label">College name</label>
                <input className="input" required value={form.college} onChange={set("college")} placeholder="Your college" />
              </div>
              <div>
                <label className="label">Branch</label>
                <select className="input" required value={form.branch} onChange={set("branch")}>
                  <option value="">Select branch</option>
                  {BRANCHES.map((b) => <option key={b}>{b}</option>)}
                </select>
              </div>
              <div>
                <label className="label">Year of study</label>
                <select className="input" required value={form.year} onChange={set("year")}>
                  <option value="">Select year</option>
                  {YEARS.map((y) => <option key={y}>{y}</option>)}
                </select>
              </div>
              <div>
                <label className="label">AI experience level</label>
                <select className="input" required value={form.ai_level} onChange={set("ai_level")}>
                  <option value="">Select level</option>
                  {LEVELS.map((l) => <option key={l}>{l}</option>)}
                </select>
              </div>
              <div>
                <label className="label">Career goal</label>
                <select className="input" required value={form.career_goal} onChange={set("career_goal")}>
                  <option value="">Select goal</option>
                  {GOALS.map((g) => <option key={g}>{g}</option>)}
                </select>
              </div>
            </div>

            {error && <div role="alert" className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}

            <button className="btn-primary w-full text-lg" disabled={loading}>
              {loading ? "Analysing your profile…" : "Register for free →"}
            </button>
            <p className="text-center text-xs text-slate-500">No spam. We only use your details to organise the workshop.</p>
          </form>
        </div>
      </section>

      <footer className="py-8 text-center text-sm text-slate-500">AI GrowthOS · Built for the NxtWave Growth Intern Challenge</footer>
    </main>
  );
}
