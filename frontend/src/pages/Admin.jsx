import { Fragment, useCallback, useEffect, useState } from "react";
import {
  Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, Pie, PieChart,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { api } from "../api.js";

const INTENT_COLORS = { "High Intent": "#10b981", "Medium Intent": "#f59e0b", "Low Intent": "#94a3b8" };
const BRAND = "#4f46e5";

function Kpi({ label, value, sub, accent }) {
  return (
    <div className="card !p-5">
      <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</div>
      <div className={`mt-1 text-3xl font-extrabold ${accent || "text-slate-900"}`}>{value}</div>
      {sub && <div className="mt-1 text-xs text-slate-500">{sub}</div>}
    </div>
  );
}

function ChartCard({ title, children, className = "" }) {
  return (
    <div className={`card ${className}`}>
      <h3 className="mb-4 font-bold text-slate-900">{title}</h3>
      <div className="h-64">{children}</div>
    </div>
  );
}

export default function Admin() {
  const [stats, setStats] = useState(null);
  const [insights, setInsights] = useState(null);
  const [leads, setLeads] = useState([]);
  const [filter, setFilter] = useState("");
  const [leaders, setLeaders] = useState([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [insightsLoading, setInsightsLoading] = useState(false);
  const [open, setOpen] = useState(null); // lead id whose message is expanded

  const loadInsights = useCallback(() => {
    setInsightsLoading(true);
    api.insights().then(setInsights).catch((e) => setError(e.message)).finally(() => setInsightsLoading(false));
  }, []);

  const loadAll = useCallback(() => {
    setError("");
    api.analytics().then(setStats).catch((e) => setError(e.message));
    api.leaderboard(5).then((d) => setLeaders(d.leaders)).catch(() => {});
    loadInsights();
  }, [loadInsights]);

  useEffect(loadAll, [loadAll]);
  useEffect(() => {
    api.leads(filter).then((d) => setLeads(d.leads)).catch((e) => setError(e.message));
  }, [filter, stats]); // reload table whenever the numbers change

  async function demo(action) {
    setBusy(true);
    try {
      await (action === "seed" ? api.seedDemo() : api.clearDemo());
      loadAll();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  if (error && !stats) {
    return <div className="mx-auto max-w-xl p-10 text-center text-red-600">{error}</div>;
  }
  if (!stats) return <div className="p-10 text-center text-slate-500">Loading dashboard…</div>;

  const intentData = Object.entries(stats.intent).map(([name, value]) => ({ name, value }));
  const hasDemo = leads.some((l) => l.is_demo);

  return (
    <main className="mx-auto max-w-6xl px-4 py-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900">Growth Dashboard</h1>
          <p className="text-sm text-slate-500">Goal: 500 registrations in 7 days on a ₹2,000 budget</p>
        </div>
        <div className="flex gap-2">
          <button className="btn-ghost" onClick={loadAll}>↻ Refresh</button>
          <button className="btn-ghost" disabled={busy} onClick={() => demo("seed")}>Load demo data</button>
          <button className="btn-ghost" disabled={busy} onClick={() => demo("clear")}>Clear demo data</button>
        </div>
      </div>

      {hasDemo && (
        <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-800">
          Showing <b>simulated demo data</b> mixed with any real registrations. Clear it before real campaign analysis.
        </div>
      )}
      {error && <div className="mt-4 rounded-xl bg-red-50 px-4 py-2 text-sm text-red-700">{error}</div>}

      {/* KPI ROW */}
      <div className="mt-6 grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
        <Kpi label="Registrations" value={stats.total_registrations} sub={`${stats.avg_per_day}/day avg`} />
        <Kpi label="High intent" value={stats.intent["High Intent"]} sub={`${stats.high_intent_rate}% of total`} accent="text-emerald-600" />
        <Kpi label="Medium intent" value={stats.intent["Medium Intent"]} accent="text-amber-600" />
        <Kpi label="Low intent" value={stats.intent["Low Intent"]} accent="text-slate-500" />
        <Kpi label="Conversion rate" value={`${stats.conversion_rate}%`} sub={`${stats.total_registrations} of ${stats.total_visits} visits`} accent="text-brand-600" />
        <Kpi label="Referral share" value={`${stats.referral.referral_share}%`} sub={`${stats.referral.active_ambassadors} active ambassadors`} accent="text-brand-600" />
      </div>

      {/* GOAL PROGRESS */}
      <div className="card mt-4 !p-5">
        <div className="flex justify-between text-sm font-semibold">
          <span>Progress to goal</span>
          <span>{stats.goal.current} / {stats.goal.target} ({stats.goal.percent}%)</span>
        </div>
        <div className="mt-2 h-3 overflow-hidden rounded-full bg-slate-100">
          <div className="h-full rounded-full bg-brand-600 transition-all" style={{ width: `${stats.goal.percent}%` }} />
        </div>
      </div>

      {/* AI INSIGHTS */}
      <section className="card mt-4 border-brand-100 bg-gradient-to-br from-brand-50 to-white">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-slate-900">✨ AI Campaign Insights</h2>
          <div className="flex items-center gap-3">
            {insights && (
              <span className="rounded-full bg-white px-2 py-0.5 text-xs text-slate-500 shadow-sm">
                {insights.source === "gemini" ? "Gemini" : "Rule-based fallback"}
              </span>
            )}
            <button className="btn-ghost" onClick={loadInsights} disabled={insightsLoading}>
              {insightsLoading ? "Analysing…" : "Regenerate"}
            </button>
          </div>
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          {insights?.insights.map((i, idx) => (
            <div key={idx} className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-slate-100">
              <div className="font-semibold text-slate-900">{i.title}</div>
              <p className="mt-1 text-sm text-slate-600">{i.text}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CHARTS */}
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <ChartCard title="Lead intent split">
          <ResponsiveContainer>
            <PieChart>
              <Pie data={intentData} dataKey="value" nameKey="name" innerRadius={55} outerRadius={90} paddingAngle={3} label>
                {intentData.map((d) => <Cell key={d.name} fill={INTENT_COLORS[d.name]} />)}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Registrations per day">
          <ResponsiveContainer>
            <LineChart data={stats.daily}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="date" tickFormatter={(d) => d.slice(5)} fontSize={12} />
              <YAxis allowDecimals={false} fontSize={12} />
              <Tooltip />
              <Line type="monotone" dataKey="registrations" stroke={BRAND} strokeWidth={3} dot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Channel performance (conversion %)">
          <ResponsiveContainer>
            <BarChart data={stats.by_channel}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="channel" fontSize={12} />
              <YAxis fontSize={12} unit="%" />
              <Tooltip formatter={(v, n) => (n === "conversion" ? `${v}%` : v)} />
              <Bar dataKey="conversion" name="conversion" fill={BRAND} radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Registrations by channel">
          <ResponsiveContainer>
            <BarChart data={stats.by_channel}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="channel" fontSize={12} />
              <YAxis allowDecimals={false} fontSize={12} />
              <Tooltip />
              <Legend />
              <Bar dataKey="visits" name="Visits" fill="#c7d2fe" radius={[6, 6, 0, 0]} />
              <Bar dataKey="registrations" name="Registrations" fill={BRAND} radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Top colleges">
          <ResponsiveContainer>
            <BarChart data={stats.top_colleges} layout="vertical" margin={{ left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis type="number" allowDecimals={false} fontSize={12} />
              <YAxis type="category" dataKey="college" width={140} fontSize={11} tickFormatter={(c) => (c.length > 20 ? c.slice(0, 19) + "…" : c)} />
              <Tooltip />
              <Bar dataKey="registrations" fill="#6366f1" radius={[0, 6, 6, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="High-intent rate by branch (%)">
          <ResponsiveContainer>
            <BarChart data={stats.by_branch}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="branch" fontSize={10} interval={0} tickFormatter={(b) => (b.length > 8 ? b.slice(0, 7) + "…" : b)} />
              <YAxis fontSize={12} unit="%" />
              <Tooltip />
              <Bar dataKey="high_intent_rate" name="High-intent %" fill="#10b981" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* REFERRAL PERFORMANCE */}
      <section className="card mt-4">
        <h2 className="font-bold text-slate-900">Referral performance</h2>
        <div className="mt-3 grid gap-4 md:grid-cols-3">
          <div className="rounded-xl bg-slate-50 p-4"><div className="text-2xl font-extrabold">{stats.referral.total_referred}</div><div className="text-sm text-slate-500">students joined via referral</div></div>
          <div className="rounded-xl bg-slate-50 p-4"><div className="text-2xl font-extrabold">{stats.referral.active_ambassadors}</div><div className="text-sm text-slate-500">active ambassadors</div></div>
          <div className="rounded-xl bg-slate-50 p-4"><div className="text-2xl font-extrabold">{stats.referral.referral_share}%</div><div className="text-sm text-slate-500">of all registrations</div></div>
        </div>
        {leaders.length > 0 && (
          <ul className="mt-4 divide-y divide-slate-100 text-sm">
            {leaders.map((l) => (
              <li key={l.code} className="flex items-center justify-between py-2">
                <span><b>#{l.rank}</b> {l.name} <span className="text-slate-400">· {l.college}</span></span>
                <span className="font-bold text-brand-600">{l.referrals} referrals</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* LEADS TABLE */}
      <section className="card mt-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="font-bold text-slate-900">Lead list (sorted by AI score)</h2>
          <select className="input !w-auto" value={filter} onChange={(e) => setFilter(e.target.value)}>
            <option value="">All leads</option>
            <option>High Intent</option>
            <option>Medium Intent</option>
            <option>Low Intent</option>
          </select>
        </div>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead className="text-xs uppercase text-slate-500">
              <tr>
                <th className="py-2 pr-3">Student</th><th className="pr-3">College</th><th className="pr-3">Branch / Year</th>
                <th className="pr-3">Channel</th><th className="pr-3">Score</th><th />
              </tr>
            </thead>
            <tbody>
              {leads.slice(0, 25).map((l) => (
                <Fragment key={l.id}>
                  <tr className="border-t border-slate-100">
                    <td className="py-2 pr-3 font-semibold">{l.name}</td>
                    <td className="pr-3 text-slate-600">{l.college}</td>
                    <td className="pr-3 text-slate-600">{l.branch} · {l.year}</td>
                    <td className="pr-3">{l.channel}</td>
                    <td className="pr-3">
                      <span className="rounded-full px-2 py-0.5 text-xs font-semibold text-white" style={{ background: INTENT_COLORS[l.category] }}>
                        {l.score} · {l.category.replace(" Intent", "")}
                      </span>
                    </td>
                    <td className="text-right">
                      <button className="text-xs font-medium text-brand-600" onClick={() => setOpen(open === l.id ? null : l.id)}>
                        {open === l.id ? "Hide" : "Message"}
                      </button>
                    </td>
                  </tr>
                  {open === l.id && (
                    <tr key={`${l.id}-m`}>
                      <td colSpan={6} className="pb-3">
                        <pre className="whitespace-pre-wrap rounded-xl bg-emerald-50 p-3 font-sans text-sm">{l.outreach?.whatsapp}</pre>
                        <p className="mt-1 text-xs text-slate-500">{l.score_reason}</p>
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))}
              {leads.length === 0 && (
                <tr><td colSpan={6} className="py-6 text-center text-slate-500">No leads yet. Register a student or load demo data.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
