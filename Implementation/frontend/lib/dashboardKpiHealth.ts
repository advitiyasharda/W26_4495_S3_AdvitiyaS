import type { AccessLog, FallEvent, ObjectDetectionEvent, Threat } from "./api";

/** Surface condition for KPI cards — drives border + pill, not the modal charts. */
export type KpiHealth = "normal" | "watch" | "critical";

/** Worst of entry vs exit access health — for the combined door traffic card. */
export function accessTrafficHealth(logs: AccessLog[]): KpiHealth {
  const e = accessTypeHealth(logs, "entry");
  const x = accessTypeHealth(logs, "exit");
  if (e === "critical" || x === "critical") return "critical";
  if (e === "watch" || x === "watch") return "watch";
  return "normal";
}

export function accessTypeHealth(logs: AccessLog[], type: "entry" | "exit"): KpiHealth {
  const rows = logs.filter((l) => l.type === type);
  if (rows.length === 0) return "normal";
  const failed = rows.filter((l) => l.status === "failed").length;
  const rate = failed / rows.length;
  if (rate > 0.12 || failed >= 6) return "critical";
  if (failed > 0) return "watch";
  return "normal";
}

export function alertsHealth(threats: Threat[]): KpiHealth {
  if (threats.some((t) => t.severity === "CRITICAL")) return "critical";
  if (threats.some((t) => t.severity === "HIGH" || t.severity === "MEDIUM")) return "watch";
  return "normal";
}

export function fallsHealth(falls: FallEvent[]): KpiHealth {
  if (falls.length === 0) return "normal";
  if (falls.length >= 4) return "critical";
  return "watch";
}

export function objectsHealth(objects: ObjectDetectionEvent[]): KpiHealth {
  const critical = objects.filter((o) => o.severity === "CRITICAL").length;
  const high = objects.filter((o) => o.severity === "HIGH").length;
  if (critical > 0) return "critical";
  if (high > 0) return "watch";
  return "normal";
}

export const KPI_HEALTH_LABEL: Record<KpiHealth, string> = {
  normal: "Normal",
  watch: "Watch",
  critical: "Critical",
};
