import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth";

export default function LoginPage() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("patient.demo@healthsignal.dev");
  const [password, setPassword] = useState("healthsignal-demo-pw-2026");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await login(email, password);
      nav("/dashboard");
    } catch (err) {
      setError(String(err instanceof Error ? err.message : err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen grid place-items-center p-6">
      <div className="card w-full max-w-md">
        <h1 className="text-2xl font-semibold mb-1">HealthSignal</h1>
        <p className="text-sm text-muted mb-6">
          Multimodal AI health-intelligence research prototype — hackathon demonstration build.
        </p>
        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="text-xs text-muted">Email</label>
            <input className="w-full mt-1 bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-sm"
              value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div>
            <label className="text-xs text-muted">Password</label>
            <input type="password" className="w-full mt-1 bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-sm"
              value={password} onChange={(e) => setPassword(e.target.value)} />
          </div>
          {error && <div className="text-danger text-sm">{error}</div>}
          <button disabled={busy} className="w-full bg-accent/90 hover:bg-accent text-ink font-semibold rounded-lg py-2 text-sm">
            {busy ? "Signing in…" : "Sign in"}
          </button>
        </form>
        <div className="mt-6 text-xs text-muted space-y-1">
          <div className="font-medium text-slate-300">Demo accounts (run backend/scripts/seed_demo.py)</div>
          <div>patient.demo@healthsignal.dev</div>
          <div>clinician.demo@healthsignal.dev</div>
          <div>researcher.demo@healthsignal.dev</div>
          <div>admin.demo@healthsignal.dev</div>
          <div>password: healthsignal-demo-pw-2026</div>
        </div>
        <p className="mt-6 text-xs text-muted">
          All demo data is synthetic or drawn from public de-identified datasets. HealthSignal is not a
          diagnostic device and nothing here is medical advice.
        </p>
      </div>
    </div>
  );
}