import type { ObjectCategory, ObjectDetectionEvent, ObjectSeverity } from "./api";

export const OBJECT_CATEGORIES: ObjectCategory[] = [
  "WEAPON",
  "SECURITY_THREAT",
  "PARCEL",
  "MOBILITY_AID",
  "OPERATIONAL",
];

export const OBJECT_SEVERITIES: ObjectSeverity[] = ["CRITICAL", "HIGH", "MEDIUM", "INFO", "LOW"];

/** Operator-facing copy: how each bucket ties to smart-door / facility safety workflows */
export const OBJECT_CATEGORY_GUIDE: Record<
  ObjectCategory,
  { label: string; shortLabel: string; why: string; examples: string }
> = {
  WEAPON: {
    label: "Weapons & improvised harm",
    shortLabel: "Weapons",
    why: "Highest-priority door events — correlate with access logs and alerts for the same window.",
    examples: "Knives, firearms, crowbars, bats, sharp tools",
  },
  SECURITY_THREAT: {
    label: "Ambiguous or policy flags",
    shortLabel: "Policy / ambiguous",
    why: "Items that need human judgment: odd shapes, sports gear blocking egress, or model uncertainty.",
    examples: "Unknown elongated object, skateboard in corridor, unusual props",
  },
  PARCEL: {
    label: "Luggage & deliveries",
    shortLabel: "Parcels & bags",
    why: "Track unattended packages and visitor luggage against your unattended threshold.",
    examples: "Backpacks, mail, Amazon boxes, totes left in the frame",
  },
  MOBILITY_AID: {
    label: "Accessibility & clinical equipment",
    shortLabel: "Mobility / clinical",
    why: "Expected in care settings — still logged for congestion, tipping risk, or corridor clearance.",
    examples: "Wheelchairs, walkers, oxygen, gurneys, IV poles",
  },
  OPERATIONAL: {
    label: "Routine doorway activity",
    shortLabel: "Routine / facility",
    why: "Normal objects and staff gear; useful for false-positive review and slip/trip context.",
    examples: "Person in frame, carts, signs, drinks, keys, laptops",
  },
};

/** Normalize API/demo strings so filters and charts never drop rows on unknown categories. */
export function normalizeObjectCategory(raw: string | undefined): ObjectCategory {
  if (!raw) return "OPERATIONAL";
  const u = String(raw).toUpperCase().replace(/\s+/g, "_") as ObjectCategory;
  return OBJECT_CATEGORIES.includes(u) ? u : "OPERATIONAL";
}

/** Counts derived from the current event list (aligned with table + filters). */
export function countByCategory(events: ObjectDetectionEvent[]): Record<ObjectCategory, number> {
  const out = {} as Record<ObjectCategory, number>;
  for (const c of OBJECT_CATEGORIES) out[c] = 0;
  for (const e of events) {
    out[normalizeObjectCategory(e.category)]++;
  }
  return out;
}

export function countBySeverity(events: ObjectDetectionEvent[]): Record<ObjectSeverity, number> {
  const out = {} as Record<ObjectSeverity, number>;
  for (const s of OBJECT_SEVERITIES) out[s] = 0;
  for (const e of events) {
    if (out[e.severity] !== undefined) out[e.severity]++;
  }
  return out;
}

export function topObjectClasses(events: ObjectDetectionEvent[], limit = 8) {
  const map = new Map<string, number>();
  for (const e of events) {
    const k = e.object_class || "unknown";
    map.set(k, (map.get(k) ?? 0) + 1);
  }
  return [...map.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit)
    .map(([name, count]) => ({ name: name.replace(/_/g, " "), count }));
}

export function objectEventsPerHour(events: ObjectDetectionEvent[]) {
  const buckets: Record<string, number> = {};
  for (const e of events) {
    const d = new Date(e.timestamp);
    const label = `${d.getHours().toString().padStart(2, "0")}:00`;
    buckets[label] = (buckets[label] ?? 0) + 1;
  }
  return Object.entries(buckets)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([hour, count]) => ({ hour, count }));
}

export function avgConfidence(events: ObjectDetectionEvent[]): number | null {
  if (events.length === 0) return null;
  return events.reduce((s, e) => s + e.confidence, 0) / events.length;
}

const SEVERITY_RANK: Record<ObjectSeverity, number> = {
  CRITICAL: 0,
  HIGH: 1,
  MEDIUM: 2,
  LOW: 3,
  INFO: 4,
};

/** Table default: what staff should look at first (severity, then dwell time, then recency). */
export function sortEventsByAttention(events: ObjectDetectionEvent[]): ObjectDetectionEvent[] {
  return [...events].sort((a, b) => {
    const sr = SEVERITY_RANK[a.severity] - SEVERITY_RANK[b.severity];
    if (sr !== 0) return sr;
    if (b.unattended_seconds !== a.unattended_seconds) return b.unattended_seconds - a.unattended_seconds;
    return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
  });
}

/** Heuristic “needs review” for KPI strip — tune without changing API. */
export function eventNeedsReview(e: ObjectDetectionEvent): boolean {
  if (e.severity === "CRITICAL" || e.severity === "HIGH") return true;
  if (normalizeObjectCategory(e.category) === "WEAPON") return true;
  if (e.unattended_seconds >= 180) return true;
  if (
    e.severity === "MEDIUM" &&
    (normalizeObjectCategory(e.category) === "SECURITY_THREAT" || normalizeObjectCategory(e.category) === "PARCEL")
  ) {
    return true;
  }
  return false;
}

export function categoryStackByDay(events: ObjectDetectionEvent[], maxDays = 14) {
  const map = new Map<string, Record<ObjectCategory, number>>();
  for (const e of events) {
    const d = new Date(e.timestamp);
    if (Number.isNaN(d.getTime())) continue;
    const key = d.toISOString().slice(0, 10);
    const cat = normalizeObjectCategory(e.category);
    if (!map.has(key)) {
      const z = {} as Record<ObjectCategory, number>;
      for (const c of OBJECT_CATEGORIES) z[c] = 0;
      map.set(key, z);
    }
    map.get(key)![cat]++;
  }
  const sorted = [...map.entries()].sort((a, b) => a[0].localeCompare(b[0])).slice(-maxDays);
  return sorted.map(([iso, counts]) => ({
    day: new Date(iso + "T12:00:00").toLocaleDateString("en-US", { month: "short", day: "numeric" }),
    ...counts,
  }));
}

export function hourlyCategoryStack(events: ObjectDetectionEvent[]) {
  const rows: Array<{ hour: string } & Record<ObjectCategory, number>> = [];
  for (let h = 0; h < 24; h++) {
    const label = `${h.toString().padStart(2, "0")}:00`;
    const base = { hour: label } as { hour: string } & Record<ObjectCategory, number>;
    for (const c of OBJECT_CATEGORIES) base[c] = 0;
    rows.push(base);
  }
  for (const e of events) {
    const d = new Date(e.timestamp);
    if (Number.isNaN(d.getTime())) continue;
    const h = d.getHours();
    const cat = normalizeObjectCategory(e.category);
    rows[h][cat]++;
  }
  return rows;
}

export function avgConfidenceByCategory(events: ObjectDetectionEvent[]): Array<{
  category: ObjectCategory;
  label: string;
  avg: number;
  n: number;
}> {
  const sums = {} as Record<ObjectCategory, { s: number; n: number }>;
  for (const c of OBJECT_CATEGORIES) sums[c] = { s: 0, n: 0 };
  for (const e of events) {
    const c = normalizeObjectCategory(e.category);
    sums[c].s += e.confidence;
    sums[c].n++;
  }
  return OBJECT_CATEGORIES.filter((c) => sums[c].n > 0).map((category) => ({
    category,
    label: OBJECT_CATEGORY_GUIDE[category].shortLabel,
    avg: sums[category].s / sums[category].n,
    n: sums[category].n,
  }));
}
