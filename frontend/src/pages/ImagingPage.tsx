import { ChangeEvent, useEffect, useState } from "react";
import { Image as ImageIcon, ScanLine, SlidersHorizontal, UploadCloud, Zap } from "lucide-react";
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../lib/api";

type Run = {
  study_id: number; model_key: string; model_name: string;
  labels: string[]; probabilities: Record<string, number>; highest_label: string | null;
  probability_interpretation: string;
  gradcam: { target_label: string; cam_explanation: string; overlay_png_b64: string } | null;
  inference_ms: number;
};

export default function ImagingPage() {
  const [status, setStatus] = useState<{ available: boolean } | null>(null);
  const [samples, setSamples] = useState<string[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [run, setRun] = useState<Run | null>(null);
  const [originalSrc, setOriginalSrc] = useState<string | null>(null);
  const [reveal, setReveal] = useState(50);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get<{ available: boolean }>("/imaging/status").then(setStatus).catch(() => setStatus({ available: false }));
    api.get<{ samples: string[] }>("/imaging/samples").then((r) => {
      setSamples(r.samples);
      if (r.samples.length) setSelected(r.samples[0]);
    }).catch(() => setSamples([]));
  }, []);

  async function runSample(file: string) {
    setBusy(true);
    setError("");
    setRun(null);
    setSelected(file);
    try {
      const out = await api.post<Run>("/imaging/analyze-sample", { model_key: "cxr_nih", sample_file: file });
      setRun(out);
      setOriginalSrc(`/api/imaging/samples/${file}`);
      setReveal(50);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function runUpload(file: File) {
    setBusy(true);
    setError("");
    setRun(null);
    try {
      const up = await api.upload<{ study_id: number }>("/imaging/upload", file);
      const out = await api.post<Run>(`/imaging/analyze/${up.study_id}`, { model_key: "cxr_nih" });
      setRun(out);
      setOriginalSrc(URL.createObjectURL(file));
      setReveal(50);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  const pathologyData = run
    ? Object.entries(run.probabilities)
        .sort((a, b) => b[1] - a[1])
        .map(([name, value]) => ({ name, value, color: value >= 0.5 ? "#f0a94c" : "#4dd0c4" }))
    : [];

  return (
    <div className="space-y-6 max-w-6xl">
      <header className="animate-in">
        <div className="flex items-center gap-2 text-xs text-accent uppercase tracking-[0.18em] mb-2">
          <ScanLine className="w-3.5 h-3.5" /> Vision model
        </div>
        <h1 className="text-3xl font-semibold tracking-tight">Medical image intelligence</h1>
        <p className="text-sm text-muted mt-2 max-w-3xl">
          Genuine pretrained chest X-ray model (DenseNet-121 trained on NIH ChestX-ray14, via torchxrayvision)
          with Grad-CAM overlays. Other modalities (CT/MRI/ultrasound) are intentionally not offered — no
          verified model is wired up for them.
        </p>
      </header>

      {error && <div className="card text-danger text-sm">{error}</div>}
      {status && !status.available && (
        <div className="card text-warn text-sm">
          Imaging dependencies are unavailable in this deployment. Download the model from the model page instead.
        </div>
      )}

      <section className="grid lg:grid-cols-3 gap-6">
        <div className="card lg:col-span-2">
          <h2 className="font-semibold mb-1 flex items-center gap-2">
            <ImageIcon className="w-4 h-4 text-accent" /> Public-domain sample X-rays
          </h2>
          <p className="text-xs text-muted mb-4">
            Real NIH ChestX-ray14 images redistributed by torchxrayvision for testing. Select one and run inference.
          </p>
          <div className="grid sm:grid-cols-2 gap-3">
            {samples.map((s) => (
              <button
                key={s}
                onClick={() => runSample(s)}
                disabled={busy}
                className={`group relative rounded-xl overflow-hidden border text-left transition disabled:opacity-60 ${
                  selected === s ? "border-accent/60 ring-2 ring-accent/20" : "border-white/10 hover:border-white/30"
                }`}
              >
                <img src={`/api/imaging/samples/${s}`} alt={s} className="w-full h-44 object-cover bg-black/50 group-hover:scale-[1.02] transition" />
                <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-ink via-ink/85 to-transparent px-3 pb-2.5 pt-7">
                  <div className="text-xs text-slate-200 truncate">{s}</div>
                  <div className="text-[10px] text-muted">NIH ChestX-ray14 · public domain</div>
                </div>
                <span className="absolute top-2 right-2 grid place-items-center w-8 h-8 rounded-lg bg-accent/90 text-ink opacity-0 group-hover:opacity-100 transition">
                  <Zap className="w-4 h-4" />
                </span>
              </button>
            ))}
          </div>
          {samples.length === 0 && <div className="text-sm text-muted">No sample images found. Run ml/scripts/fetch_samples.py.</div>}
        </div>

        <div className="card">
          <h2 className="font-semibold mb-1 flex items-center gap-2">
            <UploadCloud className="w-4 h-4 text-accent" /> Upload your own
          </h2>
          <p className="text-xs text-muted mb-4">PNG / JPEG / DICOM ≤ 10 MB</p>
          <label className="btn-ghost cursor-pointer w-full justify-center py-8 flex-col gap-2 border-dashed">
            <UploadCloud className="w-6 h-6 text-accent" />
            <span className="text-xs">Choose a chest X-ray…</span>
            <input
              type="file" accept=".png,.jpg,.jpeg,.dcm" className="hidden"
              onChange={(e: ChangeEvent<HTMLInputElement>) => e.currentTarget.files && runUpload(e.currentTarget.files[0])}
            />
          </label>
          <p className="text-xs text-muted mt-3">
            Uploads are validated (extension, MIME, magic bytes, size) before any model sees them. The model accepts
            chest X-rays only; other images produce meaningless output — do not interpret them.
          </p>
        </div>
      </section>

      {run && (
        <section className="space-y-6 animate-in">
          <div className="grid lg:grid-cols-2 gap-6">
            <div className="card">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-muted uppercase tracking-wide">Original image</span>
                <span className="stat-chip">{run.inference_ms} ms · CPU</span>
              </div>
              {originalSrc && <img src={originalSrc} alt="original X-ray" className="w-full max-h-80 object-contain rounded-xl bg-black/50" />}
            </div>
            <div className="card">
              <div className="text-xs text-muted uppercase tracking-wide mb-1">Highest-scoring pathology</div>
              <div className="text-2xl font-semibold text-gradient">{run.highest_label}</div>
              <p className="text-xs text-muted mt-3">{run.probability_interpretation}</p>
              <div className="mt-4 h-52">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={pathologyData} layout="vertical" margin={{ left: 4, right: 28, top: 0, bottom: 0 }}>
                    <XAxis type="number" domain={[0, 1]} hide />
                    <YAxis type="category" dataKey="name" width={92} tick={{ fontSize: 9, fill: "#93a1b8" }} />
                    <Tooltip
                      formatter={(v: number) => [`${(v * 100).toFixed(1)}%`, "Model score"]}
                      contentStyle={{ background: "#111a2e", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 12, fontSize: 12 }}
                    />
                    <Bar dataKey="value" radius={[0, 5, 5, 0]}>
                      {pathologyData.map((d) => <Cell key={d.name} fill={d.color} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {run.gradcam && originalSrc && (
            <div className="card">
              <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
                <div>
                  <div className="font-semibold flex items-center gap-2">
                    <SlidersHorizontal className="w-4 h-4 text-accent" />
                    Grad-CAM overlay for “{run.gradcam.target_label}”
                  </div>
                  <p className="text-xs text-muted mt-1">Drag the slider to compare the original with the model's attention map.</p>
                </div>
                <span className="stat-chip">interactive comparison</span>
              </div>
              <div className="relative w-full max-w-[520px] aspect-square mx-auto rounded-xl overflow-hidden bg-black/50 border border-white/10">
                <img src={originalSrc} alt="original" className="absolute inset-0 w-full h-full object-contain" />
                <img
                  src={`data:image/png;base64,${run.gradcam.overlay_png_b64}`}
                  alt="Grad-CAM overlay"
                  className="absolute inset-0 w-full h-full object-contain"
                  style={{ clipPath: `inset(0 ${100 - reveal}% 0 0)` }}
                />
                <div className="pointer-events-none absolute inset-y-0 w-0.5 bg-white/70" style={{ left: `${reveal}%` }} />
                <span className="pointer-events-none absolute top-2 left-2 text-[10px] bg-accent/80 text-ink px-2 py-1 rounded-full">Grad-CAM</span>
                <span className="pointer-events-none absolute top-2 right-2 text-[10px] bg-black/60 px-2 py-1 rounded-full">original</span>
              </div>
              <input
                type="range" min={0} max={100} value={reveal}
                onChange={(e) => setReveal(Number(e.target.value))}
                className="reveal-range w-full mt-4"
                aria-label="Reveal Grad-CAM overlay"
              />
              <p className="text-xs text-warn mt-3">{run.gradcam.cam_explanation}</p>
            </div>
          )}
        </section>
      )}
    </div>
  );
}
