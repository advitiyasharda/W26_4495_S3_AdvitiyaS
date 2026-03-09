"use client";

import { useEffect, useState, useCallback } from "react";
import { getFallEvents, getFallStatus, resetFallDetector, FallEvent, FallStatusResponse } from "@/lib/api";

function fmtTime(iso: string) {
  return new Date(iso).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function confidenceColor(conf: number): string {
  if (conf > 0.7) return "bg-red-500";
  if (conf >= 0.5) return "bg-orange-500";
  return "bg-yellow-500";
}

export default function FallsPage() {
  const [events, setEvents] = useState<FallEvent[]>([]);
  const [status, setStatus] = useState<FallStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [resetting, setResetting] = useState(false);
  const [showResetConfirm, setShowResetConfirm] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    const [eventsData, statusData] = await Promise.all([getFallEvents(100), getFallStatus()]);
    setEvents(eventsData?.events ?? []);
    setStatus(statusData ?? null);
    setLoading(false);
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 15_000);
    return () => clearInterval(id);
  }, [refresh]);

  const todayStr = new Date().toDateString();
  const todayCount = events.filter((e) => new Date(e.timestamp).toDateString() === todayStr).length;
  const totalCount = events.length;
  const lastFall = events[0] ? fmtTime(events[0].timestamp) : "—";

  const handleReset = async () => {
    setResetting(true);
    await resetFallDetector();
    setResetting(false);
    setShowResetConfirm(false);
    await refresh();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Fall Detection</h1>
          <p className="text-sm text-slate-400 mt-0.5">
            Real-time monitoring for falls and sudden collapses
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`text-sm font-semibold px-3 py-1 rounded-full ${status?.detector_ready ? "bg-emerald-50 text-emerald-600" : "bg-red-50 text-red-600"
              }`}
          >
            {status?.detector_ready ? "Active" : "Offline"}
          </span>
          <button
            type="button"
            onClick={() => setShowResetConfirm(true)}
            className="bg-white border border-slate-200 text-slate-600 text-sm font-medium px-4 py-2 rounded-lg hover:bg-slate-50 hover:border-slate-300 transition-colors shadow-sm"
          >
            Reset Detector
          </button>
        </div>
      </div>

      {/* Reset confirmation modal */}
      {showResetConfirm && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
          onClick={() => setShowResetConfirm(false)}
        >
          <div
            className="bg-white rounded-xl shadow-xl max-w-md w-full p-5"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-lg font-semibold text-slate-800 mb-2">Reset Detector?</h3>
            <p className="text-sm text-slate-500 mb-4">
              This will clear the detector&apos;s velocity history and cooldown. Use when changing
              scenes or re-positioning the camera.
            </p>
            <div className="flex gap-2 justify-end">
              <button
                type="button"
                onClick={() => setShowResetConfirm(false)}
                className="px-4 py-2 text-sm font-medium text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleReset}
                disabled={resetting}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 disabled:opacity-50"
              >
                {resetting ? "Resetting…" : "Reset"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Summary bar */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-4 flex items-center justify-between">
          <span className="text-xs text-slate-500 font-medium">Falls Today</span>
          <span className="text-xl font-bold text-slate-800">{todayCount}</span>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-4 flex items-center justify-between">
          <span className="text-xs text-slate-500 font-medium">Total All Time</span>
          <span className="text-xl font-bold text-slate-800">{totalCount}</span>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-4 flex items-center justify-between">
          <span className="text-xs text-slate-500 font-medium">Last Fall</span>
          <span className="text-sm font-medium text-slate-700">{lastFall}</span>
        </div>
      </div>

      {/* Events table */}
      <div className="bg-white rounded-xl border border-slate-100 shadow-sm">
        <div className="px-5 py-4 border-b border-slate-50">
          <h2 className="font-semibold text-slate-800">Fall Events</h2>
        </div>
        {loading ? (
          <p className="text-center text-slate-400 py-10">Loading fall events…</p>
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
            <p className="text-sm font-medium text-slate-600">No falls detected — all clear</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-100">
                  <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wide px-5 py-3">
                    Time
                  </th>
                  <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wide px-5 py-3">
                    Confidence
                  </th>
                  <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wide px-5 py-3">
                    Details
                  </th>
                  <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wide px-5 py-3">
                    Severity
                  </th>
                </tr>
              </thead>
              <tbody>
                {events.map((e) => (
                  <tr key={e.anomaly_id} className="border-b border-slate-50 last:border-0 hover:bg-slate-50/50">
                    <td className="px-5 py-3 text-sm text-slate-700 whitespace-nowrap">
                      {fmtTime(e.timestamp)}
                    </td>
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-20 h-2 bg-slate-100 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${confidenceColor(e.anomaly_score)}`}
                            style={{ width: `${Math.min(100, e.anomaly_score * 100)}%` }}
                          />
                        </div>
                        <span className="text-xs font-medium text-slate-600">
                          {Math.round(e.anomaly_score * 100)}%
                        </span>
                      </div>
                    </td>
                    <td className="px-5 py-3 text-sm text-slate-600 max-w-md truncate" title={e.description}>
                      {e.description}
                    </td>
                    <td className="px-5 py-3">
                      <span className="bg-red-100 text-red-700 text-xs font-semibold px-2 py-0.5 rounded-full">
                        CRITICAL
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
