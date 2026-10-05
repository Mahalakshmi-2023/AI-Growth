// Thin wrapper around fetch so every page handles errors the same way.
async function request(path, options = {}) {
  let res;
  try {
    res = await fetch(`/api${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
  } catch {
    throw new Error("Cannot reach the server. Is the backend running on port 8000?");
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    // FastAPI validation errors come as a list: [{loc, msg}, ...]
    if (Array.isArray(data.detail)) {
      const msgs = data.detail.map((d) => `${d.loc?.slice(-1)[0]}: ${d.msg.replace("Value error, ", "")}`);
      throw new Error(msgs.join(" | "));
    }
    throw new Error(data.detail || "Something went wrong. Please try again.");
  }
  return data;
}

export const api = {
  health: () => request("/health"),
  trackVisit: (body) => request("/track-visit", { method: "POST", body: JSON.stringify(body) }),
  checkReferral: (code) => request(`/referral/${encodeURIComponent(code)}`),
  register: (body) => request("/register", { method: "POST", body: JSON.stringify(body) }),
  student: (id) => request(`/students/${id}`),
  leaderboard: (limit = 10) => request(`/leaderboard?limit=${limit}`),
  analytics: () => request("/analytics"),
  insights: () => request("/insights"),
  leads: (category) => request(`/leads${category ? `?category=${encodeURIComponent(category)}` : ""}`),
  seedDemo: () => request("/admin/seed-demo", { method: "POST" }),
  clearDemo: () => request("/admin/demo-data", { method: "DELETE" }),
};
