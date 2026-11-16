import { useEffect, useState } from "react";
import {
  Activity, BarChart3, Droplets, HeartPulse, Info, Leaf, Play, RefreshCw, Sparkles,
} from "lucide-react";
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api, ModelCard, PredictionOut } from "../lib/api";

type SampleCases = Record<string, { positive: Record<string, unknown>; negative: Record<string, unknown> }>;

const MODEL_ICONS: Record<string, typeof Activity> = {
  heart: HeartPulse,
  wdbc: Sparkles,
  ckd: Droplets,
  pima: Activity,
  ilpd: Leaf,
};

function pct(x: number) {
  return `${(x * 100).toFixed(1)}%`;
}

export default function ModelsPage() {
  const [models, setModels] = useState<ModelCard[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [values, setValues] = useState<Record<string, string>>({});
  const [result, setResult] = useState<PredictionOut | null>(null);
  const [samples, setSamples] = useState<SampleCases | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.get<{ models: ModelCard[] }>("/models").then((r) => setModels(r.models)).catch((e) => setError(String(e)));
    fetch("/sample_cases.json")
      .then((r) => (r.ok ? r.json() : null))
      .then((j) => setSamples(j))
      .catch(() => setSamples(null));
  }, []);

  const model = models.find((m) => m.model_key === selected);

  function loadExample(which: "positive" | "negative") {
    if (!samples || !model) return;
    const row = samples[model.model_key]?.[which];
    if (!row) return;
    const next: Record<string, string> = {};
    for (const f of model.feature_schema) {
      const v = row[f.feature];
      next[f.feature] = v === null || v === undefined ? "" : String(v);
    }
    setValues(next);
  }

  async function run(e: React.FormEvent) {
    e.preventDefault();
    if (!model) return;
    setBusy(true);
    setError("");
    setResult(null);
    try {
      const payload: Record<string, unknown> = {};
      for (const f of model.feature_schema) {
        const v = values[f.feature];
        if (v !== undefined && v !== "") payload[f.feature] = Number.isNaN(Number(v)) ? v : Number(v);
      }
      const out = await api.post<PredictionOut>("/predictions/tabular", { model_key: model.model_key, values: payload });
      setResult(out);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  const baselineData = model ? [
    { name: "Model", value: model.performance.roc_auc, color: "#4dd0c4" },
    { name: "Baseline", value: model.performance.baseline_roc_auc ?? 0.5, color: "#5b6b8c" },
  ] : [];

  return (
    <div className="space-y-6 max-w-6xl">
      <header className="animate-in">
        <div className="flex items-center gap-2 text-xs text-accent uppercase tracking-[0.18em] mb-2">
          <BarChart3 className="w-3.5 h-3.5" /> Model registry
        </div>
        <h1 className="text-3xl font-semibold tracking-tight">Disease risk models</h1>
        <p className="text-sm text-muted mt-2 max-w-3xl">
          One panel per genuinely trained model, with held-out-test metrics, the exact dataset it was trained on,
          and below-surface honesty about what the score is not. Pick a tile to run a real inference.
        </p>
      </header>

      <section className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {models.map((m) => {
          const Icon = MODEL_ICONS[m.model_key] ?? Activity;
          const active = selected === m.model_key;
          return (
            <button
              key={m.model_key}
              onClick={() => { setSelected(m.model_key); setResult(null); setValues({}); }}
              className={`card card-hover text-left animate-in ${active ? "border-accent/60 bg-accent/[0.06]" : ""}`}
            >
              <div className="flex items-start justify-between">
                <span className="grid place-items-center w-9 h-9 rounded-xl bg-accent/10 border border-accent/20">
                  <Icon className="w-4 h-4 text-accent" />
                </span>
                <span className="text-[10px] uppercase tracking-wider text-muted">{m.system}</span>
              </div>
              <div className="font-semibold mt-3">{m.human_task}</div>
              <div className="text-xs text-muted mt-1 truncate">{m.dataset.name}</div>
              <div className="mt-3 meter"><span style={{ width: `${m.performance.roc_auc * 100}%` }} /></div>
              <div className="mt-3 flex flex-wrap gap-1.5 text-[11px]">
                <span className="stat-chip">ROC-AUC {m.performance.roc_auc.toFixed(3)}</span>
                <span className="stat-chip">PR-AUC {m.performance.pr_auc.toFixed(3)}</span>
                <span className="stat-chip">Sens {m.performance.recall_sensitivity.toFixed(2)}</span>
                <span className="stat-chip">Spec {m.performance.specificity.toFixed(2)}</span>
              </div>
            </button>
          );
        })}
      </section>

      {model && (
        <section className="grid lg:grid-cols-2 gap-6">
          <div className="card">
            <h2 className="font-semibold mb-1 flex items-center gap-2">
              <Activity className="w-4 h-4 text-accent" /> {model.human_task} — inputs
            </h2>
            <p className="text-xs text-muted mb-3">
              Features required by the exact model (trained on {model.dataset.documented_records} records —
              <a className="text-accent hover:underline" href={model.dataset.source_url} target="_blank" rel="noreferrer"> source</a>).
              Blank fields are imputed by the training pipeline and explicitly reported below.
            </p>
            <div className="flex flex-wrap gap-2 mb-3 text-xs">
              <button className="btn-ghost" onClick={() => loadExample("positive")}>Load positive example row</button>
              <button className="btn-ghost" onClick={() => loadExample("negative")}>Load negative example row</button>
              <span className="text-muted self-center text-[11px]">(real de-identified public dataset records)</span>
            </div>
            <form onSubmit={run} className="space-y-3 max-h-[460px] overflow-auto pr-2">
              {model.feature_schema.map((f) => (
                <div key={f.feature} className="grid grid-cols-2 gap-3 items-center">
                  <label className="text-sm" title={f.hint}>
                    {f.label} {f.unit && !f.label.includes(f.unit) && <span className="text-muted text-xs">({f.unit})</span>}
                  </label>
                  {f.options ? (
                    <select
                      className="bg-black/30 border border-white/10 rounded-xl px-2 py-2 text-sm"
                      value={values[f.feature] ?? ""}
                      onChange={(e) => setValues({ ...values, [f.feature]: e.target.value })}
                    >
                      <option value="">— leave blank (imputed) —</option>
                      {Object.entries(f.options).map(([k, label]) => (
                        <option key={k} value={k}>{label}</option>
                      ))}
                    </select>
                  ) : (
                    <input
                      type="number" step={f.step ?? "any"} min={f.min ?? undefined} max={f.max ?? undefined}
                      className="bg-black/30 border border-white/10 rounded-xl px-2 py-2 text-sm"
                      value={values[f.feature] ?? ""}
                      onChange={(e) => setValues({ ...values, [f.feature]: e.target.value })}
                      placeholder={`${f.min ?? "?"}–${f.max ?? "?"}`}
                    />
                  )}
                </div>
              ))}
              <button disabled={busy} className="btn-primary">
                {busy ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                {busy ? "Running model…" : "Run prediction"}
              </button>
            </form>
          </div>

          <div className="space-y-4">
            <div className="card">
              <h2 className="font-semibold mb-3 flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-accent" /> Held-out test: model vs baseline
              </h2>
              <div className="h-32">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={baselineData} layout="vertical" margin={{ left: 8, right: 24 }}>
                    <XAxis type="number" domain={[0, 1]} hide />
                    <YAxis type="category" dataKey="name" width={62} tick={{ fontSize: 11, fill: "#93a1b8" }} />
                    <Tooltip
                      formatter={(v: number) => [v.toFixed(3), "ROC-AUC"]}
                      contentStyle={{ background: "#111a2e", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 12, fontSize: 12 }}
                    />
                    <Bar dataKey="value" radius={[0, 6, 6, 0]}>
                      {baselineData.map((d) => <Cell key={d.name} fill={d.color} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <p className="text-[11px] text-muted mt-1">
                Baseline = stratified-random dummy classifier on the same held-out split.
                Scores are dataset-specific research indicators, not validated probabilities.
              </p>
            </div>

            {error && <div className="card text-danger text-sm">{error}</div>}
            {result && (
              <>
                <div className="card animate-in">
                  <div className="text-xs text-muted uppercase tracking-wide mb-1">Model output</div>
                  <div className="flex items-end justify-between gap-4">
                    <div className="text-4xl font-semibold text-gradient">{pct(result.probability)}</div>
                    <span className="stat-chip">{result.model_name}</span>
                  </div>
                  <div className="meter mt-3"><span style={{ width: `${result.probability * 100}%` }} /></div>
                  <p className="text-xs text-muted mt-3">{result.probability_interpretation}</p>
                  {result.imputed_features.length > 0 && (
                    <p className="text-xs text-warn mt-2">
                      Imputed (not provided by you): {result.imputed_features.join(", ")} — the model used the
                      training-set imputation strategy; these fields were NOT estimated from any other input.
                    </p>
                  )}
                </div>

                {result.explanation && (
                  <div className="card">
                    <div className="font-semibold mb-1 flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-accent" /> Explanation — {result.explanation.method}
                    </div>
                    <ResponsiveContainer width="100%" height={8 * result.explanation.top_features.length + 40}>
                      <BarChart data={result.explanation.top_features.map((t) => ({
                        name: t.feature.replace(/^(num|cat)__/, ""), v: t.contribution,
                      }))} layout="vertical" margin={{ left: 80, right: 20 }}>
                        <XAxis type="number" hide />
                        <YAxis type="category" dataKey="name" width={100} tick={{ fontSize: 10, fill: "#93a1b8" }} />
                        <Tooltip
                          formatter={(v: number) => [v.toFixed(4), "SHAP contribution"]}
                          contentStyle={{ background: "#111a2e", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 12, fontSize: 12 }}
                        />
                        <Bar dataKey="v" radius={[0, 4, 4, 0]}>
                          {result.explanation.top_features.map((t, i) => (
                            <Cell key={i} fill={t.contribution > 0 ? "#4dd0c4" : "#f2726f"} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                    <p className="text-xs text-muted mt-2 flex items-start gap-1.5">
                      <Info className="w-3.5 h-3.5 shrink-0 mt-0.5" /> {result.explanation.note}
                    </p>
                  </div>
                )}

                <div className="card">
                  <div className="font-semibold mb-1">Dataset & limitations</div>
                  <p className="text-xs text-muted">{model.dataset.name}</p>
                  <ul className="text-xs text-muted list-disc pl-4 mt-2 space-y-1">
                    {model.limitations.slice(0, 5).map((l) => <li key={l}>{l}</li>)}
                  </ul>
                  <p className="text-xs text-muted mt-2">{result.safe_harbour}</p>
                </div>
              </>
            )}
          </div>
        </section>
      )}
    </div>
  );
}
