import { FormEvent, useEffect, useState } from "react";
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
  const [run, setRun] = useState<Run | null>(null);
  const [originalSrc, setOriginalSrc] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.get<{ available: boolean }>("/imaging/status").then(setStatus).catch(() => setStatus({ available: false }));
    api.get<{ samples: string[] }>("/imaging/samples").then((r) => setSamples(r.samples));
  }, []);

  async function runSample(file: string, modelKey: string) {
    setBusy(true);
    setError("");
    setRun(null);
    try {
      const out = await api.post<Run>("/imaging/analyze-sample", { model_key: modelKey, sample_file: file });
      setRun(out);
      setOriginalSrc(`/api/imaging/samples/${file}`);
    } catch (err) {
      setError(String(err instanceof Error ? err.message : err));
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
    } catch (err) {
      setError(String(err instanceof Error ? err.message : err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6 max-w-6xl">
      <header>
        <h1 className="text-2xl font-semibold">Medical image intelligence</h1>
        <p className="text-sm text-muted">
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

      <section className="grid lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="font-semibold mb-3">Run on a public-domain sample X-ray</h2>
          <div className="space-y-3">
            {samples.map((s) => (
              <div key={s} className="flex items-center gap-3">
                <img src={`/api/imaging/samples/${s}`} alt={s} className="w-24 h-24 object-cover rounded-lg border border-white/10" />
                <div className="flex-1">
                  <div className="text-sm">{s}</div>
                  <div className="text-xs text-muted">NIH ChestX-ray14 sample (public domain)</div>
                </div>
                <button disabled={busy} onClick={() => runSample(s, "cxr_nih")}
                  className="bg-accent/90 text-ink text-sm font-semibold px-3 py-1.5 rounded-lg">
                  Run NIH model
                </button>
              </div>
            ))}
            {samples.length === 0 && <div className="text-sm text-muted">No sample images found. Run ml/scripts/fetch_samples.py.</div>}
          </div>
        </div>

        <div className="card">
          <h2 className="font-semibold mb-3">Upload your own image (PNG/JPEG/DICOM ≤ 10 MB)</h2>
          <input
            type="file" accept=".png,.jpg,.jpeg,.dcm"
            onChange={(e) => e.target.files && runUpload(e.target.files[0])}
            className="block w-full text-sm file:mr-3 file:bg-white/10 file:border-0 file:rounded-lg file:px-3 file:py-2 text-muted"
          />
          <p className="text-xs text-muted mt-2">
            Uploads are validated (extension, MIME, magic bytes, size) before any model sees them. Images are stored
            only for this demo session. The model accepts chest X-rays only; other images will produce meaningless
            output — do not interpret them.
          </p>
        </div>
      </section>

      {run && (
        <section className="grid lg:grid-cols-2 gap-6">
          <div className="card">
            <div className="text-xs text-muted uppercase tracking-wide mb-2">Original image</div>
            {originalSrc && <img src={originalSrc} alt="original" className="w-full max-h-72 object-contain rounded-lg bg-black/40" />}
          </div>
          <div className="card">
            <div className="text-xs text-muted uppercase tracking-wide mb-2">Highest-scoring pathology</div>
            <div className="text-2xl font-semibold text-accent">{run.highest_label}</div>
            <ul className="mt-3 space-y-1 text-sm">
              {Object.entries(run.probabilities).sort((a, b) => b[1] - a[1]).slice(0, 6).map(([k, v]) => (
                <li key={k} className="flex justify-between">
                  <span>{k}</span>
                  <span className="text-muted">{(v * 100).toFixed(1)}%</span>
                </li>
              ))}
            </ul>
            <p className="text-xs text-muted mt-3">{run.probability_interpretation}</p>
            <p className="text-xs text-muted mt-1">inference: {run.inference_ms} ms (CPU)</p>
          </div>
          {run.gradcam && (
            <div className="card lg:col-span-2">
              <div className="text-xs text-muted uppercase tracking-wide mb-2">
                Grad-CAM overlay for “{run.gradcam.target_label}”
              </div>
              <img
                src={`data:image/png;base64,${run.gradcam.overlay_png_b64}`}
                alt="gradcam overlay"
                className="w-full max-h-96 object-contain rounded-lg bg-black/40"
              />
              <p className="text-xs text-warn mt-2">{run.gradcam.cam_explanation}</p>
            </div>
          )}
        </section>
      )}
    </div>
  );
}