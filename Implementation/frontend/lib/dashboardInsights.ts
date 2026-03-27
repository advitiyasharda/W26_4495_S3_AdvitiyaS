import type { AccessLog, FallEvent, ObjectDetectionEvent, Threat } from "./api";
import { countByCategory, topObjectClasses } from "./objectAnalytics";

export function peakHourLabel(logs: AccessLog[], type: "entry" | "exit"): string | null {
  const buckets: Record<string, number> = {};
  for (const l of logs) {
    if (l.type !== type) continue;
    const d = new Date(l.timestamp);
    const h = d.getHours();
    const label = `${h.toString().padStart(2, "0")}:00`;
    buckets[label] = (buckets[label] ?? 0) + 1;
  }
  const entries = Object.entries(buckets);
  if (entries.length === 0) return null;
  entries.sort((a, b) => b[1] - a[1]);
  return entries[0][0];
}

export function accessSuccessStats(logs: AccessLog[]) {
  const ok = logs.filter((l) => l.status === "success").length;
  const fail = logs.filter((l) => l.status !== "success").length;
  const n = logs.length || 1;
  const avgConf =
    logs.length === 0 ? null : logs.reduce((s, l) => s + l.confidence, 0) / logs.length;
  return {
    success: ok,
    failed: fail,
    successRatePct: Math.round((ok / n) * 1000) / 10,
    avgConfidence: avgConf === null ? null : Math.round(avgConf * 1000) / 1000,
  };
}

export function fallInsightSummary(falls: FallEvent[]) {
  const scores = falls.map((f) => f.anomaly_score);
  const avg = scores.length ? scores.reduce((a, b) => a + b, 0) / scores.length : null;
  const latest = falls[0];
  return {
    count: falls.length,
    avgScore: avg === null ? null : Math.round(avg * 1000) / 1000,
    latest: latest
      ? { time: latest.timestamp, pct: Math.round(latest.anomaly_score * 100), text: latest.description }
      : null,
  };
}

export function objectInsightSummary(objects: ObjectDetectionEvent[]) {
  const byCat = countByCategory(objects);
  const top = topObjectClasses(objects, 5);
  const critical = objects.filter((o) => o.severity === "CRITICAL").length;
  return { byCat, topClasses: top, critical };
}

export function threatSeverityBreakdown(threats: Threat[]) {
  const m: Record<string, number> = {};
  for (const t of threats) {
    m[t.severity] = (m[t.severity] ?? 0) + 1;
  }
  return m;
}
