import type { AccessLog, FallEvent, ObjectDetectionEvent, Threat } from "./api";
import type { TimeRangeId } from "./timeRange";
import { rangeLabelForExport } from "./timeRange";

export interface AiReportPayload {
  report_version: "1.0";
  schema: "facedoor_unified_dashboard";
  generated_at: string;
  time_range: TimeRangeId;
  time_range_label: string;
  unified_entrance_camera: {
    description: string;
    pipelines: string[];
  };
  period: { iso_start: string | null; iso_end: string };
  summary: {
    access: { entries: number; exits: number; failed_attempts: number; success_rate_percent: number };
    threats: { count: number; by_severity: Record<string, number> };
    falls: { count: number; avg_confidence: number | null };
    objects: { total_events: number; by_category: Record<string, number> };
  };
  samples: {
    access_events: Array<Record<string, unknown>>;
    threats: Array<Record<string, unknown>>;
    fall_events: Array<Record<string, unknown>>;
    object_events: Array<Record<string, unknown>>;
  };
  instructions_for_ai: string[];
}

function avg(nums: number[]): number | null {
  if (nums.length === 0) return null;
  return nums.reduce((a, b) => a + b, 0) / nums.length;
}

export function buildAiReport(opts: {
  range: TimeRangeId;
  periodStart: string | null;
  logs: AccessLog[];
  threats: Threat[];
  falls: FallEvent[];
  objects: ObjectDetectionEvent[];
}): AiReportPayload {
  const { range, periodStart, logs, threats, falls, objects } = opts;
  const entries = logs.filter((l) => l.type === "entry").length;
  const exits = logs.filter((l) => l.type === "exit").length;
  const failed = logs.filter((l) => l.status !== "success").length;
  const ok = logs.filter((l) => l.status === "success").length;
  const denom = logs.length || 1;
  const bySev: Record<string, number> = {};
  for (const t of threats) {
    bySev[t.severity] = (bySev[t.severity] ?? 0) + 1;
  }
  const byCat: Record<string, number> = {};
  for (const o of objects) {
    byCat[o.category] = (byCat[o.category] ?? 0) + 1;
  }

  return {
    report_version: "1.0",
    schema: "facedoor_unified_dashboard",
    generated_at: new Date().toISOString(),
    time_range: range,
    time_range_label: rangeLabelForExport(range),
    unified_entrance_camera: {
      description:
        "Single camera feed at the main entrance powers face-based access, YOLO object safety, and pose-based fall detection in one integrated stack.",
      pipelines: ["access_recognition", "object_detection", "fall_detection"],
    },
    period: {
      iso_start: periodStart,
      iso_end: new Date().toISOString(),
    },
    summary: {
      access: {
        entries,
        exits,
        failed_attempts: failed,
        success_rate_percent: Math.round((ok / denom) * 1000) / 10,
      },
      threats: { count: threats.length, by_severity: bySev },
      falls: {
        count: falls.length,
        avg_confidence:
          falls.length === 0
            ? null
            : Math.round((avg(falls.map((f) => f.anomaly_score)) ?? 0) * 1000) / 1000,
      },
      objects: { total_events: objects.length, by_category: byCat },
    },
    samples: {
      access_events: logs.slice(0, 40).map((l) => ({
        timestamp: l.timestamp,
        type: l.type,
        status: l.status,
        name: l.name,
        confidence: l.confidence,
      })),
      threats: threats.slice(0, 20).map((t) => ({
        threat_type: t.threat_type,
        severity: t.severity,
        message: t.message,
        timestamp: t.timestamp,
      })),
      fall_events: falls.slice(0, 20).map((f) => ({
        anomaly_id: f.anomaly_id,
        anomaly_score: f.anomaly_score,
        description: f.description,
        timestamp: f.timestamp,
      })),
      object_events: objects.slice(0, 30).map((o) => ({
        object_class: o.object_class,
        category: o.category,
        severity: o.severity,
        confidence: o.confidence,
        timestamp: o.timestamp,
      })),
    },
    instructions_for_ai: [
      "Evaluate risk trends from threats and failed access attempts.",
      "Correlate fall confidence with object hazards if timestamps are close.",
      "Flag privacy-sensitive fields before external sharing.",
      "Compare entry/exit balance for occupancy reasoning.",
    ],
  };
}

export function downloadJson(filename: string, data: unknown) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function downloadCsv(filename: string, rows: Record<string, string | number | null>[]) {
  if (rows.length === 0) return;
  const headers = Object.keys(rows[0]);
  const esc = (v: string | number | null) => {
    const s = v === null || v === undefined ? "" : String(v);
    if (/[",\n]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
    return s;
  };
  const lines = [headers.join(","), ...rows.map((r) => headers.map((h) => esc(r[h] as string | number | null)).join(","))];
  const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function logsToCsvRows(logs: AccessLog[]) {
  return logs.map((l) => ({
    timestamp: l.timestamp,
    type: l.type,
    status: l.status,
    name: l.name ?? "",
    person_id: l.person_id ?? "",
    confidence: l.confidence,
  }));
}
