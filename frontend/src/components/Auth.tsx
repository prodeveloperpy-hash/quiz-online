import { useState } from "react";
import { BookOpenCheck, CheckCircle2 } from "lucide-react";
import { api } from "../api";
import type { Role, User } from "../types";

type AuthResponse = { access_token: string; user: User };
export function Auth({ onSuccess }: { onSuccess: (token: string, user: User) => void }) {
  const [register, setRegister] = useState(false);
  const [form, setForm] = useState({ name: "", email: "", password: "", role: "student" as Role, department: "Computer Science", semester: 1 });
  const [error, setError] = useState(""); const [loading, setLoading] = useState(false);
  async function submit(e: React.FormEvent) {
    e.preventDefault(); setError(""); setLoading(true);
    try {
      const result = await api<AuthResponse>(register ? "/auth/register" : "/auth/login", { method: "POST", body: JSON.stringify(register ? form : { email: form.email, password: form.password }) });
      onSuccess(result.access_token, result.user);
    } catch (err) { setError((err as Error).message); } finally { setLoading(false); }
  }
  return <div className="auth-page">
    <section className="auth-hero"><div className="hero-content"><div className="logo-large"><BookOpenCheck /></div><p className="eyebrow">Smart university assessments</p><h1>Learning measured<br />with clarity.</h1><p>Create focused quizzes, take secure assessments and receive meaningful results—all in one place.</p><div className="hero-points"><span><CheckCircle2 /> Timed & secure</span><span><CheckCircle2 /> Instant objective results</span><span><CheckCircle2 /> Teacher-reviewed answers</span></div></div></section>
    <section className="auth-panel"><form className="auth-card" onSubmit={submit}><div><p className="eyebrow blue">Welcome</p><h2>{register ? "Create your account" : "Sign in to continue"}</h2><p className="muted">{register ? "Enter your academic information." : "Use your registered email and password."}</p></div>
      {register && <label>Full name<input required value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="Your full name" /></label>}
      <label>Email address<input required type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} placeholder="name@university.edu" /></label>
      <label>Password<input required minLength={6} type="password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} placeholder="Minimum 6 characters" /></label>
      {register && <><label>Account type<select value={form.role} onChange={e => setForm({ ...form, role: e.target.value as Role })}><option value="student">Student</option><option value="teacher">Teacher</option><option value="admin">Admin</option></select></label>
        {form.role === "student" && <div className="two-col"><label>Department<input required value={form.department} onChange={e => setForm({ ...form, department: e.target.value })} /></label><label>Semester<input required type="number" min="1" max="12" value={form.semester} onChange={e => setForm({ ...form, semester: +e.target.value })} /></label></div>}</>}
      {error && <div className="alert error">{error}</div>}<button className="primary wide" disabled={loading}>{loading ? "Please wait…" : register ? "Create account" : "Sign in"}</button>
      <p className="switch-auth">{register ? "Already registered?" : "New to Online Quiz?"} <button type="button" onClick={() => { setRegister(!register); setError(""); }}>{register ? "Sign in" : "Create account"}</button></p>
    </form></section>
  </div>;
}

