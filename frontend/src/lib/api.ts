const TOKEN_KEY = "hs_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = { ...(options.headers as Record<string, string>) };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (options.body && !(options.body instanceof FormData)) headers["Content-Type"] = "application/json";
  const res = await fetch(`/api${path}`, { ...options, headers });
  const text = await res.text();
  const data = text ? JSON.parse(text) : null;
  if (!res.ok) {
    throw new Error(typeof data?.detail === "string" ? data.detail : `request failed (${res.status})`);
  }
  return data as T;
}

export const api = {
  get: <T,>(path: string) => request<T>(path),
  post: <T,>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) }),
  del: <T,>(path: string) => request<T>(path, { method: "DELETE" }),
  upload: <T,>(path: string, file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return request<T>(path, { method: "POST", body: fd });
  },
};

export type ModelCard = {
  model_key: string;
  model_name: string;
  model_type: string;
  prediction_task: string;
  system: string;
  human_task: string;
  dataset: { name: string; source_url: string; documented_records: string; licence: string; known_limitations: string[] };
  performance: {
    roc_auc: number; pr_auc: number; recall_sensitivity: number; specificity: number;
    f1: number; brier: number; n_train: number; n_test: number;
  };
  feature_schema: {
    feature: string; label: string; unit: string; options: Record<string, string> | null;
    min: number | null; max: number | null; step: number | null; hint: string;
  }[];
  intended_use: string;
  limitations: string[];
};

export type PredictionOut = {
  model_key: string;
  model_name: string;
  probability: number;
  probability_interpretation: string;
  provided_features: Record<string, unknown>;
  imputed_features: string[];
  explanation: {
    method: string;
    top_features: { feature: string; contribution: number; direction: string; value: number | null }[];
    note: string;
  } | null;
  limitations: string[];
  safe_harbour: string;
};

export type ProfileOut = { id: number; label: string; is_synthetic: boolean; created_at: string; owner_id: number };