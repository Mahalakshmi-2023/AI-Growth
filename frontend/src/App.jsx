import { Link, NavLink, Route, Routes } from "react-router-dom";
import Landing from "./pages/Landing.jsx";
import Welcome from "./pages/Welcome.jsx";
import Leaderboard from "./pages/Leaderboard.jsx";
import Admin from "./pages/Admin.jsx";

function Navbar() {
  const link = ({ isActive }) =>
    `text-sm font-medium transition ${isActive ? "text-brand-600" : "text-slate-600 hover:text-slate-900"}`;
  return (
    <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/80 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <Link to="/" className="flex items-center gap-2 text-lg font-extrabold text-slate-900">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-brand-600 text-sm text-white">AI</span>
          GrowthOS
        </Link>
        <nav className="flex items-center gap-5">
          <NavLink to="/" end className={link}>Workshop</NavLink>
          <NavLink to="/leaderboard" className={link}>Leaderboard</NavLink>
          <NavLink to="/admin" className={link}>Admin</NavLink>
        </nav>
      </div>
    </header>
  );
}

export default function App() {
  return (
    <>
      <Navbar />
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/welcome/:id" element={<Welcome />} />
        <Route path="/leaderboard" element={<Leaderboard />} />
        <Route path="/admin" element={<Admin />} />
        <Route path="*" element={<div className="p-10 text-center text-slate-500">Page not found.</div>} />
      </Routes>
    </>
  );
}
