import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api.js";

const MEDAL = ["🥇", "🥈", "🥉"];

export default function Leaderboard() {
  const [leaders, setLeaders] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.leaderboard(10).then((d) => setLeaders(d.leaders)).catch((e) => setError(e.message));
  }, []);

  return (
    <main className="mx-auto max-w-3xl px-4 py-10">
      <div className="text-center">
        <h1 className="text-3xl font-extrabold text-slate-900">🏆 Top College Ambassadors</h1>
        <p className="mt-2 text-slate-600">Students who brought the most friends to the workshop.</p>
      </div>

      {error && <div className="mt-6 rounded-xl bg-red-50 p-4 text-red-700">{error}</div>}
      {!leaders && !error && <div className="mt-10 text-center text-slate-500">Loading…</div>}

      {leaders && leaders.length === 0 && (
        <div className="card mt-8 text-center text-slate-600">
          No referrals yet. <Link to="/" className="font-semibold text-brand-600">Register</Link> and be the first ambassador!
        </div>
      )}

      {leaders && leaders.length > 0 && (
        <div className="card mt-8 overflow-hidden p-0">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3">Rank</th>
                <th className="px-4 py-3">Student</th>
                <th className="hidden px-4 py-3 sm:table-cell">College</th>
                <th className="px-4 py-3 text-right">Link clicks</th>
                <th className="px-4 py-3 text-right">Referrals</th>
              </tr>
            </thead>
            <tbody>
              {leaders.map((l) => (
                <tr key={l.code} className="border-t border-slate-100">
                  <td className="px-4 py-3 text-lg font-bold">{MEDAL[l.rank - 1] || `#${l.rank}`}</td>
                  <td className="px-4 py-3">
                    <div className="font-semibold">{l.name}</div>
                    <div className="text-xs text-slate-400">{l.code}</div>
                  </td>
                  <td className="hidden px-4 py-3 text-slate-600 sm:table-cell">{l.college}</td>
                  <td className="px-4 py-3 text-right text-slate-500">{l.clicks}</td>
                  <td className="px-4 py-3 text-right text-lg font-extrabold text-brand-600">{l.referrals}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
