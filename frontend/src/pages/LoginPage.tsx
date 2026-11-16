import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { BrainCircuit, LockKeyhole, Mail, ShieldAlert } from "lucide-react";
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
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen grid place-items-center p-6">
      <div className="card hero-gradient w-full max-w-md animate-in relative overflow-hidden">
        <div className="absolute -right-14 -top-16 w-52 h-52 rounded-full bg-accent/10 blur-3xl" />
        <div className="relative">
          <div className="flex items-center gap-3 mb-6">
            <span className="grid place-items-center w-11 h-11 rounded-2xl bg-accent/15 border border-accent/30">
              <BrainCircuit className="w-6 h-6 text-accent" />
            </span>
            <div>
              <h1 className="text-2xl font-semibold tracking-tight text-gradient">HealthSignal</h1>
              <p className="text-[11px] text-muted">multimodal intelligence · prototype</p>
            </div>
          </div>
          <p className="text-sm text-muted mb-6">
            Multimodal AI health-intelligence research prototype — hackathon demonstration build.
          </p>
          <form onSubmit={submit} className="space-y-4">
            <div>
              <label className="text-xs text-muted flex items-center gap-1.5"><Mail className="w-3.5 h-3.5" /> Email</label>
              <input className="w-full mt-1 bg-black/30 border border-white/10 rounded-xl px-3 py-2.5 text-sm"
                value={email} onChange={(e) => setEmail(e.target.value)} />
            </div>
            <div>
              <label className="text-xs text-muted flex items-center gap-1.5"><LockKeyhole className="w-3.5 h-3.5" /> Password</label>
              <input type="password" className="w-full mt-1 bg-black/30 border border-white/10 rounded-xl px-3 py-2.5 text-sm"
                value={password} onChange={(e) => setPassword(e.target.value)} />
            </div>
            {error && <div className="text-danger text-sm">{error}</div>}
            <button disabled={busy} className="btn-primary w-full justify-center py-2.5">
              {busy ? "Signing in…" : "Sign in"}
            </button>
          </form>
          <div className="mt-6 text-xs text-muted space-y-1 bg-black/20 rounded-xl p-3 border border-white/5">
            <div className="font-medium text-slate-300">Demo accounts</div>
            <div>patient.demo@healthsignal.dev</div>
            <div>clinician.demo@healthsignal.dev</div>
            <div>researcher.demo@healthsignal.dev</div>
            <div>admin.demo@healthsignal.dev</div>
            <div>password: healthsignal-demo-pw-2026</div>
          </div>
          <p className="mt-5 text-xs text-muted flex items-start gap-1.5">
            <ShieldAlert className="w-3.5 h-3.5 shrink-0 mt-0.5 text-warn" />
            All demo data is synthetic or drawn from public de-identified datasets. HealthSignal is not a
            diagnostic device and nothing here is medical advice.
          </p>
        </div>
      </div>
    </div>
  );
}
