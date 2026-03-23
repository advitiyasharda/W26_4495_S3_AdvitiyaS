"use client";

import { useCallback, useEffect, useState } from "react";
import {
  getObjectEvents,
  getObjectStatus,
  ObjectCategory,
  ObjectDetectionEvent,
  ObjectSeverity,
  ObjectStatusResponse,
} from "@/lib/api";

// ── Helpers ───────────────────────────────────────────────────────────────────

function fmtTime(iso: string) {
  return new Date(iso).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

const SEVERITY_STYLES: Record<ObjectSeverity, string> = {
  CRITICAL: "bg-red-100 text-red-700",
  HIGH:     "bg-orange-100 text-orange-700",
  MEDIUM:   "bg-amber-100 text-amber-700",
  INFO:     "bg-blue-100 text-blue-700",
  LOW:      "bg-slate-100 text-slate-600",
};

const CATEGORY_LABELS: Record<ObjectCategory, string> = {
  WEAPON:          "Weapon",
  SECURITY_THREAT: "Security Threat",
  PARCEL:          "Parcel / Delivery",
  MOBILITY_AID:    "Mobility Aid",
  OPERATIONAL:     "Operational Hazard",
};

const CATEGORY_ICON: Record<ObjectCategory, string> = {
  WEAPON:          "🔪",
  SECURITY_THREAT: "⚠️",
  PARCEL:          "📦",
  MOBILITY_AID:    "♿",
  OPERATIONAL:     "🧹",
};

const ALL_CATEGORIES: ObjectCategory[] = [
  "WEAPON",
  "SECURITY_THREAT",
  "PARCEL",
  "MOBILITY_AID",
  "OPERATIONAL",
];

// ── Sub-components ────────────────────────────────────────────────────────────

function SeverityBadge({ severity }: { severity: ObjectSeverity }) {
  return (
    <span
      className={`text-xs font-semibold px-2 py-0.5 rounded-full ${SEVERITY_STYLES[severity]}`}
    >
      {severity}
    </span>
  );
}

function CategoryCard({
  category,
  count,
}: {
  category: ObjectCategory;
  count: number;
}) {
  return (
    <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-4 flex items-center gap-3">
      <span className="text-2xl">{CATEGORY_ICON[category]}</span>
      <div className="min-w-0">
        <p className="text-xs text-slate-500 font-medium truncate">
          {CATEGORY_LABELS[category]}
        </p>
        <p className="text-xl font-bold text-slate-800">{count}</p>
      </div>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function ObjectsPage() {
  const [events, setEvents] = useState<ObjectDetectionEvent[]>([]);
  const [status, setStatus] = useState<ObjectStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [categoryFilter, setCategoryFilter] = useState<ObjectCategory | "">("");
  const [severityFilter, setSeverityFilter] = useState<ObjectSeverity | "">("");

  const refresh = useCallback(async () => {
    setLoading(true);
    const [eventsData, statusData] = await Promise.all([
      getObjectEvents(100, categoryFilter || undefined, severityFilter || undefined),
      getObjectStatus(),
    ]);
    setEvents(eventsData?.events ?? []);
    setStatus(statusData ?? null);
    setLoading(false);
  }, [categoryFilter, severityFilter]);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 15_000);
    return () => clearInterval(id);
  }, [refresh]);

  const categoryCounts = status?.category_counts ?? {};

  const criticalCount = events.filter((e) => e.severity === "CRITICAL").length;
  const highCount = events.filter((e) => e.severity === "HIGH").length;
  const todayStr = new Date().toDateString();
  const todayCount = events.filter(
    (e) => new Date(e.timestamp).toDateString() === todayStr
  ).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Object Detection</h1>
          <p className="text-sm text-slate-400 mt-0.5">
            YOLOv8-powered detection of weapons, parcels, and hazards at the door
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`text-sm font-semibold px-3 py-1 rounded-full ${
              status?.detector_ready
                ? "bg-emerald-50 text-emerald-600"
                : "bg-red-50 text-red-600"
            }`}
          >
            {status?.detector_ready ? "Active" : "Offline"}
          </span>
          {status?.weapon_model_ready && (
            <span className="text-sm font-semibold px-3 py-1 rounded-full bg-purple-50 text-purple-600">
              Custom Weapon Model
            </span>
          )}
        </div>
      </div>

      {/* Offline warning */}
      {status && !status.detector_ready && (
        <div className="bg-amber-50 border border-amber-200 text-amber-800 px-4 py-3 rounded-lg text-sm">
          Object detector is offline.{" "}
          {status.message
            ? status.message
            : "Install ultralytics and restart the server: pip install ultralytics"}
        </div>
      )}

      {/* Summary cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-4 flex items-center justify-between">
          <span className="text-xs text-slate-500 font-medium">Today</span>
          <span className="text-xl font-bold text-slate-800">{todayCount}</span>
        </div>
        <div className="bg-white rounded-xl border border-red-100 shadow-sm p-4 flex items-center justify-between">
          <span className="text-xs text-red-500 font-medium">Critical</span>
          <span className="text-xl font-bold text-red-700">{criticalCount}</span>
        </div>
        <div className="bg-white rounded-xl border border-orange-100 shadow-sm p-4 flex items-center justify-between">
          <span className="text-xs text-orange-500 font-medium">High</span>
          <span className="text-xl font-bold text-orange-700">{highCount}</span>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-4 flex items-center justify-between">
          <span className="text-xs text-slate-500 font-medium">Total Logged</span>
          <span className="text-xl font-bold text-slate-800">
            {status?.events_logged ?? 0}
          </span>
        </div>
      </div>

      {/* Category counts */}
      <div>
        <h2 className="text-sm font-semibold text-slate-600 mb-2 uppercase tracking-wide">
          By Category
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          {ALL_CATEGORIES.map((cat) => (
            <CategoryCard
              key={cat}
              category={cat}
              count={categoryCounts[cat] ?? 0}
            />
          ))}
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2 items-center">
        <span className="text-sm text-slate-500 font-medium">Filter:</span>
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value as ObjectCategory | "")}
          className="text-sm border border-slate-200 rounded-lg px-3 py-1.5 text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-emerald-400"
        >
          <option value="">All Categories</option>
          {ALL_CATEGORIES.map((cat) => (
            <option key={cat} value={cat}>
              {CATEGORY_LABELS[cat]}
            </option>
          ))}
        </select>
        <select
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value as ObjectSeverity | "")}
          className="text-sm border border-slate-200 rounded-lg px-3 py-1.5 text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-emerald-400"
        >
          <option value="">All Severities</option>
          {(["CRITICAL", "HIGH", "MEDIUM", "INFO", "LOW"] as ObjectSeverity[]).map(
            (s) => (
              <option key={s} value={s}>
                {s}
              </option>
            )
          )}
        </select>
        <button
          type="button"
          onClick={refresh}
          className="ml-auto text-sm border border-slate-200 rounded-lg px-3 py-1.5 text-slate-600 bg-white hover:bg-slate-50 transition-colors"
        >
          Refresh
        </button>
      </div>

      {/* Events table */}
      <div className="bg-white rounded-xl border border-slate-100 shadow-sm">
        <div className="px-5 py-4 border-b border-slate-50">
          <h2 className="font-semibold text-slate-800">Detection Events</h2>
        </div>

        {loading ? (
          <p className="text-center text-slate-400 py-10">Loading detection events…</p>
        ) : events.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-slate-400 gap-2">
            <svg
              className="w-12 h-12 text-emerald-500"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={1.5}
            >
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
              <polyline points="22 4 12 14.01 9 11.01" />
            </svg>
            <p className="text-sm font-medium text-slate-600">
              No objects detected — all clear
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-100">
                  {[
                    "Time",
                    "Object",
                    "Category",
                    "Confidence",
                    "Unattended",
                    "Severity",
                  ].map((h) => (
                    <th
                      key={h}
                      className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wide px-5 py-3"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {events.map((e, idx) => (
                  <tr
                    key={idx}
                    className="border-b border-slate-50 last:border-0 hover:bg-slate-50/50"
                  >
                    <td className="px-5 py-3 text-sm text-slate-700 whitespace-nowrap">
                      {fmtTime(e.timestamp)}
                    </td>
                    <td className="px-5 py-3 text-sm font-medium text-slate-800 capitalize">
                      {CATEGORY_ICON[e.category]}{" "}
                      {e.object_class.replace(/_/g, " ")}
                    </td>
                    <td className="px-5 py-3 text-sm text-slate-600">
                      {CATEGORY_LABELS[e.category]}
                    </td>
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-2 bg-slate-100 rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full bg-emerald-500"
                            style={{
                              width: `${Math.min(100, e.confidence * 100)}%`,
                            }}
                          />
                        </div>
                        <span className="text-xs font-medium text-slate-600">
                          {Math.round(e.confidence * 100)}%
                        </span>
                      </div>
                    </td>
                    <td className="px-5 py-3 text-sm text-slate-600">
                      {e.unattended_seconds > 0
                        ? `${Math.floor(e.unattended_seconds / 60)}m ${Math.round(e.unattended_seconds % 60)}s`
                        : "—"}
                    </td>
                    <td className="px-5 py-3">
                      <SeverityBadge severity={e.severity} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Detector config panel */}
      {status?.detector_ready && (
        <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
          <h2 className="font-semibold text-slate-800 mb-3">Detector Configuration</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div>
              <p className="text-xs text-slate-400 font-medium">Confidence Threshold</p>
              <p className="text-sm font-semibold text-slate-700">
                {Math.round((status.confidence ?? 0) * 100)}%
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-400 font-medium">Frame Threshold</p>
              <p className="text-sm font-semibold text-slate-700">
                {status.frame_threshold} frames
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-400 font-medium">Unattended Alert</p>
              <p className="text-sm font-semibold text-slate-700">
                {status.unattended_minutes} min
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-400 font-medium">Custom Weapon Model</p>
              <p
                className={`text-sm font-semibold ${
                  status.weapon_model_ready ? "text-emerald-600" : "text-slate-400"
                }`}
              >
                {status.weapon_model_ready ? "Loaded" : "Not loaded"}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
