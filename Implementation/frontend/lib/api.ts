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
  falls?: {
    today: number;
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

export interface User {
  user_id: string;
  name: string;
  display_id: string;
  role: string;
}

export interface UsersResponse {
  users: User[];
}

// ─── API functions ────────────────────────────────────────────────────────────

export const getStats = () => fetchAPI<StatsResponse>("/stats");

export const getUsers = () => fetchAPI<UsersResponse>("/users");

export async function deleteUser(userId: string): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/users/${encodeURIComponent(userId)}`, {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
    });
    return res.ok;
  } catch (err) {
    console.error("Delete user failed:", err);
    return false;
  }
}

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

// ─── Fall Detection ──────────────────────────────────────────────────────────

export interface FallEvent {
  anomaly_id: number;
  user_id: string;
  anomaly_type: string;
  /** LSTM confidence 0–1 (maps to anomaly_score from backend) */
  anomaly_score: number;
  /** Contains reason; check for "Body not fully visible" for visibility warnings */
  description: string;
  timestamp: string;
}
export interface FallEventsResponse {
  events: FallEvent[];
  count: number;
}
export interface FallStatusResponse {
  detector_ready: boolean;
  active_mode?: "rules" | "lstm" | "unavailable";
  requested_mode?: "rules" | "lstm";
  fall_threshold: number;
  velocity_window: number;
  sequence_length?: number;
  cooldown_frames: number;
  history_length: number;
  artifacts?: {
    pose_model_exists?: boolean;
    lstm_model_exists?: boolean;
    lstm_scaler_exists?: boolean;
  };
  model_info?: Record<string, unknown>;
}
export const getFallEvents = (limit = 20) =>
  fetchAPI<FallEventsResponse>(`/fall/events?limit=${limit}`);
export const getFallStatus = () =>
  fetchAPI<FallStatusResponse>("/fall/status");
export const resetFallDetector = () =>
  fetchAPI<{ status: string }>("/fall/reset", { method: "POST" });

// ─── Object Detection ─────────────────────────────────────────────────────────

export type ObjectCategory =
  | "WEAPON"
  | "SECURITY_THREAT"
  | "PARCEL"
  | "MOBILITY_AID"
  | "OPERATIONAL";

export type ObjectSeverity = "CRITICAL" | "HIGH" | "MEDIUM" | "INFO" | "LOW";

export interface ObjectDetectionEvent {
  object_class: string;
  category: ObjectCategory;
  severity: ObjectSeverity;
  confidence: number;
  unattended_seconds: number;
  frame_count: number;
  timestamp: string;
}

export interface ObjectEventsResponse {
  events: ObjectDetectionEvent[];
  count: number;
}

export interface ObjectStatusResponse {
  detector_ready: boolean;
  weapon_model_ready: boolean;
  confidence: number;
  frame_threshold: number;
  unattended_minutes: number;
  events_logged: number;
  category_counts: Partial<Record<ObjectCategory, number>>;
  message?: string;
}

export const getObjectEvents = (limit = 50, category?: string, severity?: string) => {
  const params = new URLSearchParams({ limit: String(limit) });
  if (category) params.set("category", category);
  if (severity) params.set("severity", severity);
  return fetchAPI<ObjectEventsResponse>(`/objects/events?${params.toString()}`);
};

export const getObjectStatus = () =>
  fetchAPI<ObjectStatusResponse>("/objects/status");

// ─── Demo Interfaces ─────────────────────────────────────────────────────────

export interface DemoToolStatus {
  id: string;
  label: string;
  kind: string;
  command: string;
  running: boolean;
  pid: number | null;
}

export interface DemoToolsResponse {
  tools: DemoToolStatus[];
  timestamp: string;
}

export const getDemoTools = () =>
  fetchAPI<DemoToolsResponse>("/demo/tools");

export const startDemoTool = (toolId: string) =>
  fetchAPI<{ status: string; tool_id: string; pid?: number }>(`/demo/tools/${encodeURIComponent(toolId)}/start`, {
    method: "POST",
  });

export const startDemoToolWithPayload = (toolId: string, payload: Record<string, unknown>) =>
  fetchAPI<{ status: string; tool_id: string; pid?: number }>(`/demo/tools/${encodeURIComponent(toolId)}/start`, {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const stopDemoTool = (toolId: string) =>
  fetchAPI<{ status: string; tool_id: string }>(`/demo/tools/${encodeURIComponent(toolId)}/stop`, {
    method: "POST",
  });
