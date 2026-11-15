import { useEffect, useState } from "react";
import { api, ProfileOut } from "../lib/api";

type Report = {
  profile_id: number; profile_label: string; is_synthetic: boolean; generated_at: string;
  patient_provided: { measurements: Record<string, number> };
  model_outputs: {
    model_key: string; probability: number; interpretation: string;
    inputs: Record<string, unknown>; imputed_features: string[];
    performance: Record<string, number>; created_at: string;
  }[];
  missing: string[];
  limitations: string[];
  safe_harbour: string;
};

export default function ReportPage() {
  const [profiles, setProfiles] = useState<ProfileOut[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get<ProfileOut[]>("/profiles").then(setProfiles).catch((e) => setError(String(e)));
  }, []);

  async function generate() {
    if (selected == null) return;
    setError("");
    try {
      setReport(await api.get<Report>(`/reports/profile/${selected}`));
    } catch (err) {
      setError(String(err instanceof Error ? err.message : err));
    }
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <header>
        <h1 className="text-2xl font-semibold">Shareable health reports</h1>
        <p className="text-sm text-muted">
          Two versions are generated: a patient-readable summary, and a structured clinician report with the
          exact inputs, outputs, imputed fields and dataset limitations. Both state that they are AI-generated
          research outputs, not diagnoses.
        </p>
      </header>

      {error && <div className="card text-danger text-sm">{error}</div>}

      <div className="card flex flex-wrap gap-3 items-end">
        <div>
          <label className="text-xs text-muted">Profile</label>
          <select className="block bg-black/30 border border-white/10 rounded-lg px-2 py-1.5 text-sm mt-1"
            value={selected ?? ""} onChange={(e) => setSelected(Number(e.target.value))}>
            <option value="">— select —</option>
            {profiles.map((p) => (
              <option key={p.id} value={p.id}>#{p.id} {p.label}</option>
            ))}
          </select>
        </div>
        <button onClick={generate} className="bg-accent/90 text-ink font-semibold text-sm px-4 py-2 rounded-lg">
          Generate report
        </button>
        {selected != null && (
          <a className="bg-white/10 text-sm px-4 py-2 rounded-lg" href={`/api/reports/profile/${selected}/markdown`}
             target="_blank" rel="noreferrer">
            Download markdown
          </a>
        )}
      </div>

      {report && (
        <article className="card space-y-4">
          <div className="border-b border-white/10 pb-3">
            <div className="text-xs text-warn uppercase tracking-wide">AI-generated research report — not a medical diagnosis</div>
            <h2 className="text-xl font-semibold mt-1">
              {report.profile_label} {report.is_synthetic && <span className="text-warn text-sm">· SYNTHETIC</span>}
            </h2>
            <div className="text-xs text-muted">Generated {report.generated_at} · HealthSignal v0.1.0</div>
          </div>

          <section>
            <h3 className="font-semibold text-sm mb-1">Patient-provided measurements</h3>
            {Object.keys(report.patient_provided.measurements).length ? (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-sm">
                {Object.entries(report.patient_provided.measurements).map(([k, v]) => (
                  <div key={k} className="bg-black/20 rounded-lg px-2 py-1">{k}: <b>{v}</b></div>
                ))}
              </div>
            ) : <p className="text-sm text-muted">None recorded.</p>}
          </section>

          <section>
            <h3 className="font-semibold text-sm mb-1">Model outputs (research indicators)</h3>
            {report.model_outputs.length ? report.model_outputs.map((o) => (
              <div key={o.model_key + o.created_at} className="bg-black/20 rounded-lg p-3 text-sm mb-2">
                <div className="font-medium">{o.model_key} — {(o.probability * 100).toFixed(1)}%</div>
                <div className="text-xs text-muted">{o.interpretation}</div>
                {o.imputed_features.length > 0 && (
                  <div className="text-xs text-warn">imputed inputs: {o.imputed_features.join(", ")}</div>
                )}
                <div className="text-xs text-muted">
                  test ROC-AUC {o.performance?.roc_auc?.toFixed(3)} · n_test {o.performance?.n_test}
                </div>
              </div>
            )) : <p className="text-sm text-muted">None.</p>}
          </section>

          <section>
            <h3 className="font-semibold text-sm mb-1">Limitations</h3>
            <ul className="list-disc pl-5 text-xs text-muted space-y-1">
              {report.limitations.map((l) => <li key={l}>{l}</li>)}
            </ul>
          </section>

          <p className="text-xs text-warn border-t border-white/10 pt-3">{report.safe_harbour}</p>
        </article>
      )}
    </div>
  );
}