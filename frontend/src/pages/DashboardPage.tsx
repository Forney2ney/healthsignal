import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Activity, ArrowRight, Database, Droplets, FlaskConical, Gauge, HeartPulse,
  Layers3, Plus, ScanLine, ShieldCheck, UserRound, Wind,
} from "lucide-react";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api, ProfileOut } from "../lib/api";

type Completeness = {
  profile_id: number; is_synthetic: boolean; measurement_count: number;
  questionnaire_answers: number; imaging_studies: number; model_outputs: number;
  groups: Record<string, string[]>;
};
type Measurement = { kind: string; value: number; unit: string; observed_at: string };

const SYSTEM_META: Record<string, { label: string; icon: typeof Activity; color: string }> = {
  body: { label: "General", icon: UserRound, color: "#93a1b8" },
  cardiovascular: { label: "Heart & vessels", icon: HeartPulse, color: "#f2726f" },
  metabolic: { label: "Metabolic", icon: Droplets, color: "#f0a94c" },
  liver: { label: "Liver", icon: FlaskConical, color: "#c084fc" },
  kidney: { label: "Kidneys", icon: Activity, color: "#4dd0c4" },
  blood: { label: "Blood", icon: ShieldCheck, color: "#9f8ef2" },
  inflammatory: { label: "Immunity", icon: Wind, color: "#7dd3fc" },
};

const MEASUREMENT_KINDS = [
  "age", "height_cm", "weight_kg", "systolic_bp", "diastolic_bp", "heart_rate", "spo2", "temperature_c",
  "glucose_fasting", "glucose_random", "hba1c", "total_cholesterol", "hdl", "ldl", "triglycerides",
  "creatinine", "urea", "alt", "ast", "bilirubin_total", "albumin", "hemoglobin", "wbc", "platelets", "egfr",
];

export default function DashboardPage() {
  const [profiles, setProfiles] = useState<ProfileOut[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [completeness, setCompleteness] = useState<Completeness | null>(null);
  const [measurements, setMeasurements] = useState<Measurement[]>([]);
  const [newKind, setNewKind] = useState("systolic_bp");
  const [newValue, setNewValue] = useState("");
  const [error, setError] = useState("");
  const nav = useNavigate();

  useEffect(() => {
    api.get<ProfileOut[]>("/profiles").then((list) => {
      setProfiles(list);
      if (list.length) setSelected((prev) => prev ?? list[0].id);
    }).catch((e) => setError(String(e)));
  }, []);

  useEffect(() => {
    if (selected == null) return;
    api.get<Completeness>(`/profiles/${selected}/completeness`).then(setCompleteness).catch((e) => setError(String(e)));
    api.get<Measurement[]>(`/profiles/${selected}/measurements`).then(setMeasurements).catch((e) => setError(String(e)));
  }, [selected]);

  async function createProfile() {
    const label = `Profile ${profiles.length + 1} (manually entered)`;
    const p = await api.post<ProfileOut>("/profiles", { label, is_synthetic: false });
    setProfiles((prev) => [...prev, p]);
    setSelected(p.id);
  }

  async function addMeasurement(e: React.FormEvent) {
    e.preventDefault();
    if (selected == null || newValue === "") return;
    try {
      await api.post(`/profiles/${selected}/measurements`, { kind: newKind, value: Number(newValue) });
      setNewValue("");
      const [list, c] = await Promise.all([
        api.get<Measurement[]>(`/profiles/${selected}/measurements`),
        api.get<Completeness>(`/profiles/${selected}/completeness`),
      ]);
      setMeasurements(list);
      setCompleteness(c);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  const chartData = useMemo(() => {
    if (!completeness) return [];
    return Object.entries(completeness.groups).map(([key, kinds]) => ({
      name: SYSTEM_META[key]?.label ?? key,
      count: kinds.length,
      color: SYSTEM_META[key]?.color ?? "#4dd0c4",
    }));
  }, [completeness]);

  const activeProfile = profiles.find((p) => p.id === selected);

  return (
    <div className="space-y-6 max-w-6xl">
      {/* Hero */}
      <section className="card hero-gradient animate-in relative overflow-hidden">
        <div className="absolute -right-16 -top-20 w-64 h-64 rounded-full bg-accent/10 blur-3xl" />
        <div className="relative flex flex-col md:flex-row md:items-center justify-between gap-5">
          <div>
            <div className="flex items-center gap-2 text-xs text-accent uppercase tracking-[0.18em] mb-2">
              <Layers3 className="w-3.5 h-3.5" /> Unified health dashboard
            </div>
            <h1 className="text-3xl font-semibold tracking-tight">
              All your signals, <span className="text-gradient">one evidence trail.</span>
            </h1>
            <p className="text-sm text-muted mt-2 max-w-2xl">
              Every value here was entered by you or the clearly-labelled demo seeder. Nothing is invented;
              missing measurements stay missing and are disclosed at prediction time.
            </p>
            <div className="flex flex-wrap gap-2 mt-4">
              <span className="stat-chip"><Database className="w-3.5 h-3.5" /> {completeness?.measurement_count ?? 0} measurements</span>
              <span className="stat-chip"><Activity className="w-3.5 h-3.5" /> {completeness?.model_outputs ?? 0} model outputs</span>
              <span className="stat-chip"><ScanLine className="w-3.5 h-3.5" /> {completeness?.imaging_studies ?? 0} imaging studies</span>
              {activeProfile?.is_synthetic && (
                <span className="stat-chip border-warn/30 text-warn"><ShieldCheck className="w-3.5 h-3.5" /> SYNTHETIC DEMO</span>
              )}
            </div>
          </div>
          <div className="flex flex-col gap-2 shrink-0">
            <button onClick={() => nav("/models")} className="btn-primary justify-center">
              <Activity className="w-4 h-4" /> Explore models <ArrowRight className="w-3.5 h-3.5" />
            </button>
            <button className="btn-ghost justify-center" onClick={createProfile}>
              <Plus className="w-4 h-4" /> New manual profile
            </button>
          </div>
        </div>
      </section>

      {error && <div className="card text-danger text-sm">{error}</div>}

      {/* Profile selector */}
      <section className="card">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold flex items-center gap-2"><UserRound className="w-4 h-4 text-accent" /> Profiles</h2>
          <button className="btn-ghost" onClick={createProfile}><Plus className="w-3.5 h-3.5" /> New profile</button>
        </div>
        <div className="flex flex-wrap gap-2">
          {profiles.map((p) => (
            <button
              key={p.id}
              onClick={() => setSelected(p.id)}
              className={`px-3.5 py-2 rounded-xl text-sm border transition ${
                selected === p.id ? "border-accent text-accent bg-accent/10" : "border-white/10 hover:bg-white/5"
              }`}
            >
              #{p.id} {p.label} {p.is_synthetic && <span className="text-warn">· SYNTHETIC</span>}
            </button>
          ))}
          {profiles.length === 0 && <span className="text-sm text-muted">No profiles yet — create one or seed demo data.</span>}
        </div>
      </section>

      {completeness && (
        <>
          {/* Completeness overview */}
          <section className="grid lg:grid-cols-5 gap-6">
            <div className="card lg:col-span-3">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-semibold flex items-center gap-2"><Gauge className="w-4 h-4 text-accent" /> Data completeness by system</h2>
                <span className="text-xs text-muted">counts reflect entered measurements only</span>
              </div>
              <div className="space-y-3">
                {chartData.map((d) => {
                  const max = Math.max(...chartData.map((x) => x.count), 1);
                  return (
                    <div key={d.name} className="grid grid-cols-[110px_1fr_28px] items-center gap-3">
                      <span className="text-xs text-slate-300">{d.name}</span>
                      <div className="meter"><span style={{ width: `${(d.count / max) * 100}%`, background: d.color }} /></div>
                      <span className="text-xs text-muted text-right">{d.count}</span>
                    </div>
                  );
                })}
              </div>
              <div className="mt-5 h-40">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ top: 4, right: 8, bottom: 0, left: -24 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" vertical={false} />
                    <XAxis dataKey="name" tick={{ fontSize: 9, fill: "#93a1b8" }} interval={0} angle={-18} textAnchor="end" height={44} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 10, fill: "#93a1b8" }} />
                    <Tooltip
                      cursor={{ fill: "rgba(255,255,255,0.04)" }}
                      contentStyle={{ background: "#111a2e", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 12, fontSize: 12 }}
                    />
                    <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                      {chartData.map((d) => <Cell key={d.name} fill={d.color} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="card lg:col-span-2">
              <h2 className="font-semibold mb-1">Add a measurement</h2>
              <p className="text-xs text-muted mb-4">Units and plausible ranges are validated server-side.</p>
              <form onSubmit={addMeasurement} className="flex flex-wrap gap-2 items-end">
                <div>
                  <label className="text-xs text-muted">Kind</label>
                  <select className="block bg-black/30 border border-white/10 rounded-xl px-2 py-2 text-sm mt-1 max-w-[190px]"
                    value={newKind} onChange={(e) => setNewKind(e.target.value)}>
                    {MEASUREMENT_KINDS.map((k) => <option key={k} value={k}>{k}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-muted">Value</label>
                  <input className="block bg-black/30 border border-white/10 rounded-xl px-2 py-2 text-sm mt-1 w-28"
                    value={newValue} onChange={(e) => setNewValue(e.target.value)} />
                </div>
                <button className="btn-primary"><Plus className="w-3.5 h-3.5" /> Add</button>
              </form>
              {measurements.length > 0 && (
                <div className="mt-5 max-h-64 overflow-auto text-xs text-muted space-y-1.5 pr-1">
                  {measurements.slice(-14).reverse().map((m, i) => (
                    <div key={i} className="flex justify-between border-b border-white/5 pb-1">
                      <span>{m.kind}</span>
                      <span className="text-slate-200">{m.value} {m.unit}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </section>

          {/* Non-diagnostic body system overview */}
          <section className="card">
            <h2 className="font-semibold mb-1">Body-system data map</h2>
            <p className="text-xs text-muted mb-4">
              Systems light up only when you provide relevant measurements. An indicator means “data present for this
              system” — it never marks an organ as diseased and is not a diagnosis.
            </p>
            <BodyMap groups={completeness.groups} />
          </section>
        </>
      )}
    </div>
  );
}

function BodyMap({ groups }: { groups: Record<string, string[]> }) {
  const systems: { key: string; label: string; region: [number, number, number, number]; color: string }[] = [
    { key: "cardiovascular", label: "Heart & vessels", region: [84, 62, 32, 32], color: "#f2726f" },
    { key: "metabolic", label: "Metabolic", region: [84, 108, 32, 28], color: "#f0a94c" },
    { key: "liver", label: "Liver", region: [70, 92, 24, 24], color: "#c084fc" },
    { key: "kidney", label: "Kidneys", region: [112, 100, 20, 30], color: "#4dd0c4" },
    { key: "blood", label: "Blood", region: [84, 150, 32, 26], color: "#9f8ef2" },
    { key: "inflammatory", label: "Immunity", region: [84, 34, 32, 20], color: "#7dd3fc" },
  ];
  const active = new Set(Object.entries(groups).filter(([, kinds]) => kinds.length > 0).map(([k]) => k));
  return (
    <div className="flex flex-col md:flex-row gap-8 items-center">
      <svg viewBox="0 0 200 220" className="w-44 h-52 drop-shadow-[0_0_28px_rgba(77,208,196,0.12)]">
        <g fill="none" stroke="#2b3a5c" strokeWidth="1.2">
          <circle cx="100" cy="24" r="14" fill="#1a2742" stroke="#33456e" />
          <rect x="82" y="42" width="36" height="80" rx="10" fill="#16203a" />
          <rect x="66" y="52" width="14" height="60" rx="7" fill="#16203a" />
          <rect x="120" y="52" width="14" height="60" rx="7" fill="#16203a" />
          <rect x="82" y="122" width="15" height="70" rx="7" fill="#16203a" />
          <rect x="103" y="122" width="15" height="70" rx="7" fill="#16203a" />
        </g>
        {systems.map((s) => {
          const on = active.has(s.key);
          const [x, y, w, h] = s.region;
          return (
            <g key={s.key} className="transition-all duration-500">
              <rect x={x} y={y} width={w} height={h} rx="6"
                fill={on ? s.color : "#1a2742"} opacity={on ? 0.9 : 0.9}
                stroke={on ? "#ffffff" : "#2b3a5c"} strokeWidth="1" />
              <text x={x + w / 2} y={y + h / 2 + 3} textAnchor="middle" fontSize="7" fill={on ? "#0b1220" : "#5b6b8c"}>
                {s.label.split(" ")[0]}
              </text>
            </g>
          );
        })}
      </svg>
      <div className="grid sm:grid-cols-2 gap-3 text-sm flex-1">
        {systems.map((s) => {
          const Icon = SYSTEM_META[s.key]?.icon ?? Activity;
          const on = active.has(s.key);
          return (
            <div key={s.key} className={`flex items-center gap-3 px-3 py-2 rounded-xl border ${on ? "bg-white/5 border-white/10" : "border-transparent"}`}>
              <span className="grid place-items-center w-8 h-8 rounded-lg" style={{ background: on ? `${s.color}22` : "rgba(255,255,255,0.04)" }}>
                <Icon className="w-4 h-4" style={{ color: on ? s.color : "#5b6b8c" }} />
              </span>
              <div className="flex-1">
                <div className={on ? "text-slate-200" : "text-muted"}>{s.label}</div>
                <div className="text-[11px] text-muted">{on ? `${groups[s.key].length} measurements` : "no data"}</div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
