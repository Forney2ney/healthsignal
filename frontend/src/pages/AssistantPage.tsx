import { FormEvent, useState } from "react";
import { Sparkles } from "lucide-react";
import { api } from "../lib/api";

type Answer = {
  answer: string;
  evidence: { source: string; facts?: Record<string, unknown>; probability?: number; interpretation?: string }[];
  uncertainty: string;
  sources: string[];
};

const SUGGESTIONS = [
  "What does my heart model output mean?",
  "Explain the chest X-ray result.",
  "What datasets were used?",
  "I have chest pain — what should I do?",
];

export default function AssistantPage() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function ask(q: string) {
    setBusy(true);
    setError("");
    setAnswer(null);
    try {
      setAnswer(await api.post<Answer>("/assistant/ask", { question: q }));
    } catch (err) {
      setError(String(err instanceof Error ? err.message : err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6 max-w-3xl">
      <header className="animate-in">
        <div className="flex items-center gap-2 text-xs text-accent uppercase tracking-[0.18em] mb-2">
          <Sparkles className="w-3.5 h-3.5" /> Retrieval, not generation
        </div>
        <h1 className="text-3xl font-semibold tracking-tight">Evidence-grounded health assistant</h1>
        <p className="text-sm text-muted">
          No generative model is used. Answers are assembled only from your stored inputs, stored model outputs,
          and a small set of cited public-health references. It states when it has insufficient information, and it
          cannot diagnose or detect emergencies.
        </p>
      </header>

      <form className="card flex gap-2" onSubmit={(e: FormEvent) => { e.preventDefault(); ask(question); }}>
        <input
          className="flex-1 bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-sm"
          placeholder="Ask about your results, datasets or model behaviour…"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <button disabled={busy || !question.trim()} className="bg-accent/90 text-ink font-semibold text-sm px-4 rounded-lg">
          {busy ? "Thinking…" : "Ask"}
        </button>
      </form>

      <div className="flex flex-wrap gap-2">
        {SUGGESTIONS.map((s) => (
          <button key={s} className="stat-chip hover:bg-white/10" onClick={() => { setQuestion(s); ask(s); }}>
            {s}
          </button>
        ))}
      </div>

      {error && <div className="card text-danger text-sm">{error}</div>}

      {answer && (
        <div className="card space-y-4">
          <p className="text-sm whitespace-pre-wrap">{answer.answer}</p>
          {answer.evidence.length > 0 && (
            <div>
              <div className="text-xs uppercase tracking-wide text-muted mb-1">Evidence used</div>
              <div className="space-y-2">
                {answer.evidence.map((ev, i) => (
                  <div key={i} className="bg-black/20 rounded-lg p-2 text-xs">
                    <div className="font-medium">{ev.source}</div>
                    {ev.facts && <pre className="text-muted whitespace-pre-wrap">{JSON.stringify(ev.facts, null, 1)}</pre>}
                    {ev.probability !== undefined && <div className="text-muted">stored score: {(ev.probability * 100).toFixed(1)}%</div>}
                  </div>
                ))}
              </div>
            </div>
          )}
          <p className="text-xs text-warn">{answer.uncertainty}</p>
          {answer.sources.length > 0 && (
            <ul className="text-xs text-muted list-disc pl-5 space-y-0.5">
              {answer.sources.map((s) => <li key={s}>{s}</li>)}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}