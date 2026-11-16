import { useEffect, useState } from "react";
import { FlaskConical } from "lucide-react";
import { api } from "../lib/api";

type Manifest = Record<string, {
  name: string; rows: number; columns: number; missing_values_total: number;
  positive_rate: number; verified_utc: string;
}>;

export default function ResearchPage() {
  const [manifest, setManifest] = useState<Manifest | null>(null);
  const [cards, setCards] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get<{ manifest: Manifest }>("/research/datasets").then((r) => setManifest(r.manifest)).catch((e) => setError(String(e)));
    api.get<{ model_cards: Record<string, unknown> }>("/research/models").then((r) => setCards(r.model_cards)).catch(() => setCards(null));
  }, []);

  return (
    <div className="space-y-6 max-w-5xl">
      <header className="animate-in">
        <div className="flex items-center gap-2 text-xs text-accent uppercase tracking-[0.18em] mb-2">
          <FlaskConical className="w-3.5 h-3.5" /> Provenance & evaluation
        </div>
        <h1 className="text-3xl font-semibold tracking-tight">Research workspace</h1>
        <p className="text-sm text-muted">
          Dataset provenance and full model cards (researcher/admin role only). No patient-level data is exposed
          here — this endpoint returns aggregate dataset statistics and model documentation only.
        </p>
      </header>

      {error && <div className="card text-danger text-sm">{error}</div>}

      {manifest && (
        <section className="card">
          <h2 className="font-semibold mb-3">Verified dataset manifest</h2>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-muted text-left">
                <th className="py-1">key</th><th>dataset</th><th>rows</th><th>cols</th><th>missing</th><th>positive rate</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(manifest).map(([k, d]) => (
                <tr key={k} className="border-t border-white/5">
                  <td className="py-1.5">{k}</td>
                  <td>{d.name}</td>
                  <td>{d.rows}</td>
                  <td>{d.columns}</td>
                  <td>{d.missing_values_total}</td>
                  <td>{(d.positive_rate * 100).toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {cards && (
        <section className="card">
          <h2 className="font-semibold mb-3">Model cards ({Object.keys(cards).length})</h2>
          <div className="space-y-3 max-h-[600px] overflow-auto text-xs text-muted">
            {Object.entries(cards).map(([k, c]) => (
              <pre key={k} className="bg-black/30 rounded-lg p-3 overflow-auto">{JSON.stringify(c, null, 2)}</pre>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}