import type { FallEvent } from "./api";

const BUCKETS: { range: string; test: (s: number) => boolean }[] = [
  { range: "0–20%", test: (s) => s < 0.2 },
  { range: "20–40%", test: (s) => s >= 0.2 && s < 0.4 },
  { range: "40–60%", test: (s) => s >= 0.4 && s < 0.6 },
  { range: "60–80%", test: (s) => s >= 0.6 && s < 0.8 },
  { range: "80–100%", test: (s) => s >= 0.8 },
];

export function fallConfidenceHistogram(events: FallEvent[]) {
  const rows = BUCKETS.map((b) => ({ range: b.range, count: 0 }));
  for (const e of events) {
    const s = e.anomaly_score;
    const idx = BUCKETS.findIndex((b) => b.test(s));
    if (idx >= 0) rows[idx].count++;
  }
  return rows;
}

export function fallsPerDay(events: FallEvent[]) {
  const map = new Map<string, { label: string; count: number }>();
  for (const e of events) {
    const d = new Date(e.timestamp);
    const key = d.toISOString().slice(0, 10);
    const label = d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
    const cur = map.get(key);
    if (cur) cur.count++;
    else map.set(key, { label, count: 1 });
  }
  return [...map.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([, v]) => ({ day: v.label, count: v.count }));
}
