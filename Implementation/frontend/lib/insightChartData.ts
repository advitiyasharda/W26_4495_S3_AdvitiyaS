import type { AccessLog, FallEvent, ObjectDetectionEvent, Threat } from "./api";
import { OBJECT_CATEGORIES, countByCategory } from "./objectAnalytics";

/** 0–100 from access log outcomes in the current window (5th vertex on the vision spider chart). */
function accessVertexScore(logs: AccessLog[]): number {
  if (logs.length === 0) return 70;
  const ok = logs.filter((l) => l.status === "success").length;
  return Math.round((ok / logs.length) * 100);
}

const SEV_KEYS = ["CRITICAL", "HIGH", "MEDIUM", "LOW"] as const;
export type ThreatSevKey = (typeof SEV_KEYS)[number];

function dayKey(ts: string): string {
  const d = new Date(ts);
  if (Number.isNaN(d.getTime())) return "";
  return d.toISOString().slice(0, 10);
}

/**
 * Daily volume for one access type — KPI **modal** only.
 * Card sparklines use hourly buckets; this avoids repeating the same shape as the spark.
 */
export function dailySingleType(logs: AccessLog[], type: "entry" | "exit", maxDays = 14) {
  const map = new Map<string, number>();
  for (const l of logs) {
    if (l.type !== type) continue;
    const d = new Date(l.timestamp);
    if (Number.isNaN(d.getTime())) continue;
    const key = d.toISOString().slice(0, 10);
    map.set(key, (map.get(key) ?? 0) + 1);
  }
  const sorted = [...map.entries()].sort((a, b) => a[0].localeCompare(b[0]));
  const slice = sorted.slice(-maxDays);
  return slice.map(([iso]) => {
    const d = new Date(iso + "T12:00:00");
    return {
      day: d.toLocaleDateString("en-US", { month: "short", day: "numeric" }),
      count: map.get(iso)!,
    };
  });
}

/** Hourly counts for one access type — used for KPI card sparklines & combined charts. */
export function hourlySingleType(logs: AccessLog[], type: "entry" | "exit") {
  const buckets: Record<string, number> = {};
  for (const l of logs) {
    if (l.type !== type) continue;
    const d = new Date(l.timestamp);
    const label = `${d.getHours().toString().padStart(2, "0")}:00`;
    buckets[label] = (buckets[label] ?? 0) + 1;
  }
  return Object.entries(buckets)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([hour, count]) => ({ hour, count }));
}

/** Cumulative threat count over chronological order — unique to modal (dashboard uses severity bar). */
export function threatCumulative(threats: Threat[]) {
  const sorted = [...threats].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );
  return sorted.map((_, i) => ({
    n: i + 1,
    cumulative: i + 1,
  }));
}

/** Fall events: index vs confidence % — modal-only (dashboard uses histogram / area). */
export function fallIndexVsScore(falls: FallEvent[]) {
  const sorted = [...falls].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );
  return sorted.map((f, i) => ({
    i: i + 1,
    pct: Math.round(f.anomaly_score * 100),
  }));
}

/**
 * Five metrics → **pentagon** spider / radar chart (one vertex each, 0–100).
 */
export function cameraStackRadarData(
  fallStatus: { detector_ready?: boolean } | null,
  objectStatus: { detector_ready?: boolean; weapon_model_ready?: boolean } | null,
  dataLinkOk: boolean,
  logs: AccessLog[]
) {
  const score = (ready: boolean) => (ready ? 100 : 0);
  return [
    { subject: "Fall", readiness: score(!!fallStatus?.detector_ready), fullMark: 100 },
    { subject: "Object", readiness: score(!!objectStatus?.detector_ready), fullMark: 100 },
    { subject: "Weapon", readiness: score(!!objectStatus?.weapon_model_ready), fullMark: 100 },
    { subject: "Ingest", readiness: dataLinkOk ? 100 : 22, fullMark: 100 },
    { subject: "Access", readiness: accessVertexScore(logs), fullMark: 100 },
  ];
}

/** Radar rows for Recharts — modal-only (dashboard uses horizontal category bar + pie on /objects). */
export function objectRadarData(objects: ObjectDetectionEvent[]) {
  const c = countByCategory(objects);
  const max = Math.max(...OBJECT_CATEGORIES.map((k) => c[k]), 1);
  return OBJECT_CATEGORIES.map((cat) => ({
    subject: cat.replace(/_/g, " "),
    A: c[cat],
    fullMark: max,
  }));
}

/** Daily success vs failed — KPI modal (card uses hourly pulse strip, not this). */
export function dailyOutcomeStack(logs: AccessLog[], type: "entry" | "exit", maxDays = 14) {
  const map = new Map<string, { success: number; failed: number }>();
  for (const l of logs) {
    if (l.type !== type) continue;
    const key = dayKey(l.timestamp);
    if (!key) continue;
    const cur = map.get(key) ?? { success: 0, failed: 0 };
    if (l.status === "success") cur.success++;
    else cur.failed++;
    map.set(key, cur);
  }
  const sorted = [...map.entries()].sort((a, b) => a[0].localeCompare(b[0]));
  return sorted.slice(-maxDays).map(([iso, v]) => {
    const d = new Date(iso + "T12:00:00");
    return {
      day: d.toLocaleDateString("en-US", { month: "short", day: "numeric" }),
      success: v.success,
      failed: v.failed,
    };
  });
}

/** Stacked severity counts per calendar day — KPI modal (overview uses flat severity bar). */
export function threatsStackedByDay(threats: Threat[], maxDays = 14) {
  const map = new Map<string, Record<ThreatSevKey, number>>();
  for (const t of threats) {
    const key = dayKey(t.timestamp);
    if (!key) continue;
    const row = map.get(key) ?? { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0 };
    const sev = t.severity as ThreatSevKey;
    if (sev in row) row[sev]++;
    else row.LOW++;
    map.set(key, row);
  }
  const sorted = [...map.entries()].sort((a, b) => a[0].localeCompare(b[0]));
  return sorted.slice(-maxDays).map(([iso, v]) => {
    const d = new Date(iso + "T12:00:00");
    return {
      day: d.toLocaleDateString("en-US", { month: "short", day: "numeric" }),
      ...v,
    };
  });
}

/** Top YOLO labels for a horizontal bar — KPI modal (card uses class pills; overview uses category bar). */
export function topObjectClasses(objects: ObjectDetectionEvent[], limit = 8) {
  const m = new Map<string, number>();
  for (const o of objects) {
    const k = o.object_class || "unknown";
    m.set(k, (m.get(k) ?? 0) + 1);
  }
  return [...m.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit)
    .map(([name, count]) => ({
      name: name.replace(/_/g, " "),
      count,
    }));
}

/** Hour-of-day (0–23) counts for falls — KPI card pulse strip (different from score sparkline). */
export function fallHourBuckets(falls: FallEvent[]) {
  const h = Array.from({ length: 24 }, (_, i) => ({ hour: i, count: 0 }));
  for (const f of falls) {
    const d = new Date(f.timestamp);
    if (Number.isNaN(d.getTime())) continue;
    h[d.getHours()].count++;
  }
  return h;
}
