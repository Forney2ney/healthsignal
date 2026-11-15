import { useEffect, useState } from "react";
import { api, ProfileOut } from "../lib/api";

type Completeness = {
  profile_id: number; is_synthetic: boolean; measurement_count: number;
  questionnaire_answers: number; imaging_studies: number; model_outputs: number;
  groups: Record<string, string[]>;
};
type Measurement = { kind: string; value: number; unit: string; observed_at: string };

const SYSTEM_OF_GROUP: Record<string, string> = {
  body: "General", cardiovascular: "Heart & vessels", metabolic: "Metabolic",
  liver: "Liver", kidney: "Kidneys", blood: "Blood", inflammatory: "Immunity",
};

export default function DashboardPage() {
  const [profiles, setProfiles] = useState<ProfileOut[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [completeness, setCompleteness] = useState<Completeness | null>(null);
  const [measurements, setMeasurements] = useState<Measurement[]>([]);
  const [newKind, setNewKind] = useState("systolic_bp");
  const [newValue, setNewValue] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    api.get<ProfileOut[]>("/profiles").then(setProfiles).catch((e) => setError(String(e)));
  }, []);

  useEffect(() => {
    if (selected == null) return;
    api.get<Completeness>(`/profiles/${selected}/completeness`).then(setCompleteness);
    api.get<Measurement[]>(`/profiles/${selected}/measurements`).then(setMeasurements);
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
      const list = await api.get<Measurement[]>(`/profiles/${selected}/measurements`);
      setMeasurements(list);
      const c = await api.get<Completeness>(`/profiles/${selected}/completeness`);
      setCompleteness(c);
    } catch (err) {
      setError(String(err instanceof Error ? err.message : err));
    }
  }

  return (
    <div className="space-y-6 max-w-6xl">
      <header>
        <h1 className="text-2xl font-semibold">Unified health dashboard</h1>
        <p className="text-sm text-muted">
          All information shown here is what you (or the demo seeder) actually entered. Nothing is invented;
          missing measurements are shown as missing.
        </p>
      </header>

      {error && <div className="text-danger text-sm">{error}</div>}

      <section className="card">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold">Profiles</h2>
          <button className="bg-accent/90 text-ink text-sm font-semibold px-3 py-1.5 rounded-lg" onClick={createProfile}>
            + New profile
          </button>
        </div>
        <div className="flex flex-wrap gap-2">
          {profiles.map((p) => (
            <button
              key={p.id}
              onClick={() => setSelected(p.id)}
              className={`px-3 py-2 rounded-lg text-sm border ${selected === p.id ? "border-accent text-accent bg-accent/10" : "border-white/10 hover:bg-white/5"}`}
            >
              #{p.id} {p.label} {p.is_synthetic && <span className="text-warn">· SYNTHETIC</span>}
            </button>
          ))}
          {profiles.length === 0 && <span className="text-sm text-muted">No profiles yet — create one or seed demo data.</span>}
        </div>
      </section>

      {completeness && (
        <>
          <section className="grid md:grid-cols-2 gap-6">
            <div className="card">
              <h2 className="font-semibold mb-3">Data completeness</h2>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div><div className="text-2xl font-semibold text-accent">{completeness.measurement_count}</div><div className="text-muted">measurements</div></div>
                <div><div className="text-2xl font-semibold text-accent">{completeness.model_outputs}</div><div className="text-muted">model outputs</div></div>
                <div><div className="text-2xl font-semibold text-accent">{completeness.imaging_studies}</div><div className="text-muted">imaging studies</div></div>
                <div><div className="text-2xl font-semibold text-accent">{completeness.questionnaire_answers}</div><div className="text-muted">questionnaire answers</div></div>
              </div>
              <div className="mt-4 space-y-2">
                {Object.entries(completeness.groups).map(([group, kinds]) => (
                  <div key={group} className="text-sm">
                    <span className="text-slate-300">{SYSTEM_OF_GROUP[group] ?? group}</span>:{" "}
                    {kinds.length ? <span className="text-muted">{kinds.join(", ")}</span> : <span className="text-warn">no data recorded</span>}
                  </div>
                ))}
              </div>
            </div>

            <div className="card">
              <h2 className="font-semibold mb-3">Add a measurement (validated)</h2>
              <form onSubmit={addMeasurement} className="flex flex-wrap gap-2 items-end">
                <div>
                  <label className="text-xs text-muted">Kind</label>
                  <select className="block bg-black/30 border border-white/10 rounded-lg px-2 py-1.5 text-sm mt-1"
                    value={newKind} onChange={(e) => setNewKind(e.target.value)}>
                    {["age","height_cm","weight_kg","systolic_bp","diastolic_bp","heart_rate","spo2","temperature_c",
                      "glucose_fasting","glucose_random","hba1c","total_cholesterol","hdl","ldl","triglycerides",
                      "creatinine","urea","alt","ast","bilirubin_total","albumin","hemoglobin","wbc","platelets","egfr"].map((k) => (
                      <option key={k} value={k}>{k}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-muted">Value</label>
                  <input className="block bg-black/30 border border-white/10 rounded-lg px-2 py-1.5 text-sm mt-1 w-32"
                    value={newValue} onChange={(e) => setNewValue(e.target.value)} />
                </div>
                <button className="bg-accent/90 text-ink text-sm font-semibold px-3 py-1.5 rounded-lg">Add</button>
              </form>
              {measurements.length > 0 && (
                <div className="mt-4 max-h-48 overflow-auto text-xs text-muted space-y-1">
                  {measurements.slice(-12).map((m, i) => (
                    <div key={i}>{m.kind}: <span className="text-slate-200">{m.value}</span> {m.unit} · {new Date(m.observed_at).toLocaleString()}</div>
                  ))}
                </div>
              )}
            </div>
          </section>

          <section className="card">
            <h2 className="font-semibold mb-1">Interactive body map</h2>
            <p className="text-xs text-muted mb-4">
              Systems light up only when you provide relevant measurements. An indicator means “data present for this system” —
              it never marks an organ as diseased.
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
    { key: "liver", label: "Liver", region: [70, 92, 24, 24], color: "#f0a94c" },
    { key: "kidney", label: "Kidneys", region: [112, 100, 20, 30], color: "#4dd0c4" },
    { key: "blood", label: "Blood", region: [84, 150, 32, 26], color: "#9f8ef2" },
    { key: "inflammatory", label: "Immunity", region: [84, 34, 32, 20], color: "#f7d774" },
  ];
  const active = new Set(Object.entries(groups).filter(([, kinds]) => kinds.length > 0).map(([k]) => k));
  return (
    <div className="flex flex-col md:flex-row gap-6 items-center">
      <svg viewBox="0 0 200 220" className="w-48 h-56">
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
            <g key={s.key}>
              <rect x={x} y={y} width={w} height={h} rx="6"
                fill={on ? s.color : "#1a2742"} opacity={on ? 0.85 : 0.9}
                stroke={on ? "#ffffff" : "#2b3a5c"} strokeWidth="1" />
              <text x={x + w / 2} y={y + h / 2 + 3} textAnchor="middle" fontSize="7" fill={on ? "#0b1220" : "#5b6b8c"}>
                {s.label.split(" ")[0]}
              </text>
            </g>
          );
        })}
      </svg>
      <div className="grid grid-cols-2 gap-2 text-sm">
        {systems.map((s) => (
          <div key={s.key} className="flex items-center gap-2">
            <span className="inline-block w-3 h-3 rounded-full" style={{ background: active.has(s.key) ? s.color : "#1a2742", border: "1px solid #2b3a5c" }} />
            <span className={active.has(s.key) ? "text-slate-200" : "text-muted"}>{s.label}</span>
            <span className="text-xs text-muted">{active.has(s.key) ? `data (${groups[s.key].length})` : "no data"}</span>
          </div>
        ))}
      </div>
    </div>
  );
}