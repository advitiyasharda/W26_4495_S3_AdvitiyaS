/**
 * Shared light pastel palette — colourful but soft (not neon, not flat grey).
 */
export const chart = {
  grid: "#e2e8f0",
  axis: "#64748b",
  mint: "#2dd4bf",
  mintSoft: "#5eead4",
  sky: "#38bdf8",
  skySoft: "#7dd3fc",
  lilac: "#a78bfa",
  lilacSoft: "#c4b5fd",
  peach: "#fb923c",
  peachSoft: "#fdba74",
  blush: "#fb7185",
  blushSoft: "#fda4af",
  butter: "#fbbf24",
  sage: "#86efac",
  indigo: "#818cf8",
} as const;

export const severityFill: Record<string, string> = {
  CRITICAL: "#fca5a5",
  HIGH: "#fcd34d",
  MEDIUM: "#fde68a",
  LOW: "#bfdbfe",
  INFO: "#a5f3fc",
};

export const objectCategoryFill: Record<string, string> = {
  WEAPON: "#fca5a5",
  SECURITY_THREAT: "#fdba74",
  PARCEL: "#93c5fd",
  MOBILITY_AID: "#c4b5fd",
  OPERATIONAL: "#94a3b8",
};

export const auditActionFill: Record<string, string> = {
  ACCESS_GRANTED: "#6ee7b7",
  ACCESS_DENIED: "#fca5a5",
  FACE_REGISTRATION: "#c4b5fd",
  THREAT_CREATED: "#fdba74",
  THREAT_RESOLVED: "#5eead4",
  ANOMALY_DETECTED: "#f0abfc",
  DATA_EXPORT: "#7dd3fc",
  SYSTEM_CONFIG_CHANGE: "#94a3b8",
  BACKUP_COMPLETED: "#86efac",
  LOGIN_SUCCESS: "#a5b4fc",
  REPORT_GENERATED: "#fcd34d",
  CONFIG_VIEW: "#cbd5e1",
  POLICY_UPDATE: "#fde68a",
  SESSION_TIMEOUT: "#fbcfe8",
};

export const statSpark = {
  entry: { stroke: "#14b8a8", fill: "rgba(20, 184, 166, 0.2)" },
  exit: { stroke: "#38bdf8", fill: "rgba(56, 189, 248, 0.18)" },
  alert: { stroke: "#f59e0b", fill: "rgba(245, 158, 11, 0.18)" },
  fall: { stroke: "#fb7185", fill: "rgba(251, 113, 133, 0.18)" },
  status: { stroke: "#8b5cf6", fill: "rgba(139, 92, 246, 0.16)" },
} as const;
