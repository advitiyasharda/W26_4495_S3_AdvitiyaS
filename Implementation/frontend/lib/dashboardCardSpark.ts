import type { AccessLog, FallEvent, ObjectDetectionEvent, Threat } from "./api";
import { hourlySingleType } from "./insightChartData";

function padTail(values: number[], len: number): number[] {
  if (values.length >= len) return values.slice(-len);
  const pad = Array(len - values.length).fill(0);
  return [...pad, ...values];
}

/** Last N hourly entry counts for KPI sparkline */
export function sparkEntries(logs: AccessLog[], n = 14): number[] {
  const rows = hourlySingleType(logs, "entry");
  const v = rows.map((r) => r.count);
  return padTail(v, n);
}

export function sparkExits(logs: AccessLog[], n = 14): number[] {
  const rows = hourlySingleType(logs, "exit");
  const v = rows.map((r) => r.count);
  return padTail(v, n);
}

function hourlyAny(events: { timestamp: string }[]): number[] {
  const buckets: Record<string, number> = {};
  for (const e of events) {
    const d = new Date(e.timestamp);
    const label = `${d.getHours().toString().padStart(2, "0")}:00`;
    buckets[label] = (buckets[label] ?? 0) + 1;
  }
  return Object.entries(buckets)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([, c]) => c);
}

export function sparkThreats(threats: Threat[], n = 14): number[] {
  return padTail(hourlyAny(threats), n);
}

export function sparkObjects(objects: ObjectDetectionEvent[], n = 14): number[] {
  return padTail(hourlyAny(objects), n);
}

/** Fall confidence % along timeline (lightweight trend on card) */
export function sparkFalls(falls: FallEvent[], n = 14): number[] {
  const sorted = [...falls].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );
  const v = sorted.map((f) => Math.round(f.anomaly_score * 100));
  return padTail(v, n);
}
