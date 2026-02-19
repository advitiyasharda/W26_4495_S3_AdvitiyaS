// API client — all calls go through Next.js /api proxy → Flask :5000

export const API_BASE = "/api";

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T | null> {
  try {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      headers: { "Content-Type": "application/json", ...options?.headers },
      ...options,
    });
    if (!res.ok) throw new Error(`API error: ${res.statusText}`);
    return (await res.json()) as T;
  } catch (err) {
    console.error("API fetch failed:", err);
    return null;
  }
}

// ─── Types ────────────────────────────────────────────────────────────────────

export interface StatsResponse {
  access_events: {
    total_entries: number;
    total_exits: number;
    today: number;
  };
  threats: {
    active_alerts: number;
  };
}

export interface AccessLog {
  person_id: string | null;
  name: string | null;
  type: "entry" | "exit";
  status: "success" | "failed";
  confidence: number;
  timestamp: string;
}

export interface LogsResponse {
  logs: AccessLog[];
}

export interface Threat {
  threat_type: string;
  message: string;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  timestamp: string;
}

export interface ThreatsResponse {
  threats: Threat[];
}

export interface AuditEntry {
  action: string;
  user: string | null;
  resource: string | null;
  result: string;
  timestamp: string;
}

export interface AuditResponse {
  audit_log: AuditEntry[];
}

// ─── API functions ────────────────────────────────────────────────────────────

export const getStats = () => fetchAPI<StatsResponse>("/stats");

export const getAccessLogs = (limit = 20, personId?: string) => {
  const qs = personId ? `?limit=${limit}&person_id=${personId}` : `?limit=${limit}`;
  return fetchAPI<LogsResponse>(`/logs${qs}`);
};

export const getThreats = (severity?: string) => {
  const qs = severity ? `?severity=${severity}` : "";
  return fetchAPI<ThreatsResponse>(`/threats${qs}`);
};

export const getAuditLog = (limit = 50) =>
  fetchAPI<AuditResponse>(`/compliance/audit?limit=${limit}`);
