import { useEffect, useState } from "react";
import { Bar, BarChart, Cell, ResponsiveContainer, XAxis, YAxis } from "recharts";
import { api, ModelCard, PredictionOut } from "../lib/api";

type SampleCases = Record<string, { positive: Record<string, unknown>; negative: Record<string, unknown> }>;

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
      setError(String(err instanceof Error ? err.message : err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6 max-w-6xl">
      <header>
        <h1 className="text-2xl font-semibold">Disease risk models</h1>
        <p className="text-sm text-muted">
          One panel per genuinely trained model, with held-out-test metrics, the exact dataset it was trained on,
          and below-surface honesty about what the score is not.
        </p>
      </header>

      <section className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {models.map((m) => (
          <button
            key={m.model_key}
            onClick={() => { setSelected(m.model_key); setResult(null); setValues({}); }}
            className={`card text-left ${selected === m.model_key ? "border-accent" : "hover:border-white/25"}`}
          >
            <div className="text-xs text-muted uppercase tracking-wide">{m.system}</div>
            <div className="font-semibold mt-1">{m.human_task}</div>
            <div className="text-xs text-muted mt-2">{m.model_name}</div>
            <div className="mt-3 flex flex-wrap gap-2 text-xs">
              <span className="stat-chip">ROC-AUC {m.performance.roc_auc.toFixed(3)}</span>
              <span className="stat-chip">PR-AUC {m.performance.pr_auc.toFixed(3)}</span>
              <span className="stat-chip"> Sens {m.performance.recall_sensitivity.toFixed(3)}</span>
              <span className="stat-chip"> Spec {m.performance.specificity.toFixed(3)}</span>
            </div>
          </button>
        ))}
      </section>

      {model && (
        <section className="grid lg:grid-cols-2 gap-6">
          <div className="card">
            <h2 className="font-semibold mb-1">{model.human_task} — inputs</h2>
            <p className="text-xs text-muted mb-3">
              Features required by the exact model (trained on {model.dataset.documented_records} records —
              <a className="text-accent" href={model.dataset.source_url} target="_blank" rel="noreferrer"> source</a>).
              Blank fields are imputed by the training pipeline and explicitly reported below.
            </p>
            <div className="flex gap-2 mb-3 text-xs">
              <button className="bg-white/10 px-2 py-1 rounded-lg" onClick={() => loadExample("positive")}>Load positive example row</button>
              <button className="bg-white/10 px-2 py-1 rounded-lg" onClick={() => loadExample("negative")}>Load negative example row</button>
              <span className="text-muted self-center">(real de-identified public dataset records)</span>
            </div>
            <form onSubmit={run} className="space-y-3 max-h-[480px] overflow-auto pr-2">
              {model.feature_schema.map((f) => (
                <div key={f.feature} className="grid grid-cols-2 gap-3 items-center">
                  <label className="text-sm" title={f.hint}>
                    {f.label} {f.unit && <span className="text-muted text-xs">({f.unit})</span>}
                  </label>
                  {f.options ? (
                    <select
                      className="bg-black/30 border border-white/10 rounded-lg px-2 py-1.5 text-sm"
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
                      className="bg-black/30 border border-white/10 rounded-lg px-2 py-1.5 text-sm"
                      value={values[f.feature] ?? ""}
                      onChange={(e) => setValues({ ...values, [f.feature]: e.target.value })}
                      placeholder={`${f.min ?? "?"}–${f.max ?? "?"}`}
                    />
                  )}
                </div>
              ))}
              <button disabled={busy} className="bg-accent/90 text-ink font-semibold text-sm px-4 py-2 rounded-lg">
                {busy ? "Running model…" : "Run prediction"}
              </button>
            </form>
          </div>

          <div className="space-y-4">
            {error && <div className="card text-danger text-sm">{error}</div>}
            {result && (
              <>
                <div className="card">
                  <div className="text-xs text-muted uppercase tracking-wide mb-1">Model output</div>
                  <div className="text-4xl font-semibold text-accent">{pct(result.probability)}</div>
                  <p className="text-xs text-muted mt-2">{result.probability_interpretation}</p>
                  {result.imputed_features.length > 0 && (
                    <p className="text-xs text-warn mt-2">
                      Imputed (not provided by you): {result.imputed_features.join(", ")} — the model used the
                      training-set imputation strategy; these fields were NOT estimated from any other input.
                    </p>
                  )}
                </div>

                {result.explanation && (
                  <div className="card">
                    <div className="font-semibold mb-1">Explanation — {result.explanation.method}</div>
                    <ResponsiveContainer width="100%" height={8 * result.explanation.top_features.length + 40}>
                      <BarChart data={result.explanation.top_features.map((t) => ({
                        name: t.feature.replace(/^(num|cat)__/, ""), v: t.contribution,
                      }))} layout="vertical" margin={{ left: 80, right: 20 }}>
                        <XAxis type="number" hide />
                        <YAxis type="category" dataKey="name" width={100} tick={{ fontSize: 10, fill: "#93a1b8" }} />
                        <Bar dataKey="v">
                          {result.explanation.top_features.map((t, i) => (
                            <Cell key={i} fill={t.contribution > 0 ? "#4dd0c4" : "#f2726f"} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                    <p className="text-xs text-muted mt-2">{result.explanation.note}</p>
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