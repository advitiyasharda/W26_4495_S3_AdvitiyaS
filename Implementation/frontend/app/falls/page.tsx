"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import { getFallEvents, getFallStatus, resetFallDetector, FallEvent, FallStatusResponse } from "@/lib/api";
import { DEMO_FALL_EVENTS, DEMO_FALL_STATUS, emptyOrDemo, nullOrDemo } from "@/lib/demoData";
import { useDemoMode } from "@/lib/useDemoMode";
import { downloadCsv, fallEventsToCsvRows } from "@/lib/reportExport";
import PageHero from "@/components/PageHero";
import { IconCalmCheck, IconCameraDoor, IconDownload, IconFallMotion } from "@/components/icons/DoorIcons";
import { fallConfidenceHistogram, fallsPerDay } from "@/lib/chartPrep";
import { chart as C } from "@/lib/theme";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

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
  if (conf > 0.8) return "bg-rose-400";
  if (conf >= 0.5) return "bg-amber-300";
  return "bg-emerald-400";
}

const HIST_FILLS = ["#fce7f3", "#fbcfe8", "#f9a8d4", "#f472b6", "#ec4899"];

export default function FallsPage() {
  const { demoEnabled } = useDemoMode();
  const [eventsRaw, setEventsRaw] = useState<FallEvent[]>([]);
  const [status, setStatus] = useState<FallStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [resetting, setResetting] = useState(false);
  const [showResetConfirm, setShowResetConfirm] = useState(false);
  const [usingDemo, setUsingDemo] = useState(false);

  const refresh = useCallback(async (demo: boolean) => {
    setLoading(true);
    const [eventsData, statusData] = await Promise.all([getFallEvents(100), getFallStatus()]);
    const apiEvents = eventsData?.events ?? [];
    setUsingDemo(apiEvents.length === 0 && demo);
    setEventsRaw(emptyOrDemo(apiEvents, DEMO_FALL_EVENTS, demo));
    setStatus(nullOrDemo(statusData, DEMO_FALL_STATUS, demo));
    setLoading(false);
  }, []);

  useEffect(() => {
    refresh(demoEnabled);
    const id = setInterval(() => refresh(demoEnabled), 15_000);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refresh, demoEnabled]);

  const events = eventsRaw;
  const todayStr = new Date().toDateString();
  const todayCount = events.filter((e) => new Date(e.timestamp).toDateString() === todayStr).length;
  const totalCount = events.length;
  const lastFall = events[0] ? fmtTime(events[0].timestamp) : "—";

  const hist = useMemo(() => fallConfidenceHistogram(events), [events]);
  const byDay = useMemo(() => fallsPerDay(events), [events]);

  const handleReset = async () => {
    setResetting(true);
    await resetFallDetector();
    setResetting(false);
    setShowResetConfirm(false);
    await refresh(demoEnabled);
  };

  const latestFall = events[0];
  const showVisibilityBanner = latestFall?.description?.includes("Body not fully visible") ?? false;

  return (
    <div className="space-y-6">
      {showVisibilityBanner && (
        <div className="bg-amber-100 border border-amber-300 text-amber-800 px-4 py-3 rounded-lg">
          Camera cannot see full body — ask person to step back.
        </div>
      )}

      <PageHero
        tone="pink"
        eyebrow="Same camera · Pose & LSTM"
        title="Fall detection"
        icon={<IconFallMotion className="w-6 h-6" />}
        description={
          <>
            Monitors the doorway zone for sudden posture changes. Use the charts to see model confidence and when events
            clustered — ideal for reviewing camera placement.
          </>
        }
        aside={
          <div className="flex flex-wrap items-center gap-2 justify-center sm:justify-end">
            <span
              className={`inline-flex items-center gap-1.5 text-sm font-semibold px-3 py-1.5 rounded-full border ${
                status?.detector_ready
                  ? "bg-emerald-100 text-emerald-900 border-emerald-200/80"
                  : "bg-rose-100 text-rose-900 border-rose-200/80"
              }`}
            >
              <IconCameraDoor className="w-4 h-4 opacity-80" />
              {status?.detector_ready ? "Stream OK" : "Offline"}
            </span>
            <button
              type="button"
              onClick={() => setShowResetConfirm(true)}
              className="bg-white text-rose-700 text-sm font-semibold px-4 py-2 rounded-xl border border-rose-200/80 hover:bg-rose-50/90 transition-colors shadow-sm"
            >
              Reset detector
            </button>
            <button
              type="button"
              onClick={() =>
                downloadCsv(
                  `fall_events_${Date.now()}.csv`,
                  fallEventsToCsvRows(events),
                  ["timestamp", "anomaly_id", "anomaly_type", "anomaly_score", "user_id", "description"]
                )
              }
              className="inline-flex items-center gap-2 bg-white text-rose-700 text-sm font-semibold px-4 py-2 rounded-xl border border-rose-200/80 hover:bg-rose-50/90 transition-colors shadow-sm"
            >
              <IconDownload className="w-4 h-4" />
              Export CSV
            </button>
          </div>
        }
      >
        {usingDemo && (
          <span className="inline-block mt-2 text-xs font-semibold bg-fuchsia-100/90 text-fuchsia-950 px-2.5 py-1 rounded-full border border-fuchsia-200/80">
            Demo fall events — API buffer was empty
          </span>
        )}
      </PageHero>

      {showResetConfirm && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
          onClick={() => setShowResetConfirm(false)}
        >
          <div
            className="bg-white rounded-xl shadow-xl max-w-md w-full p-5"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-lg font-semibold text-slate-800 mb-2">Reset detector?</h3>
            <p className="text-sm text-slate-500 mb-4">
              Clears velocity history and cooldown — use after moving the camera or changing the scene.
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
                className="px-4 py-2 text-sm font-medium text-white bg-rose-500 rounded-lg hover:bg-rose-600 disabled:opacity-50"
              >
                {resetting ? "Resetting…" : "Reset"}
              </button>
            </div>
          </div>
        </div>
      )}

      {events.length > 0 && latestFall && (
        <div className="bg-white rounded-xl border border-rose-100 shadow-sm p-4">
          <h2 className="text-sm font-semibold text-rose-800 mb-2">Latest event confidence</h2>
          <div className="flex items-center gap-3">
            <div className="flex-1 h-4 bg-slate-100 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${confidenceColor(latestFall.anomaly_score)}`}
                style={{ width: `${Math.min(100, latestFall.anomaly_score * 100)}%` }}
              />
            </div>
            <span className="text-sm font-medium text-slate-600 min-w-[3rem]">{Math.round(latestFall.anomaly_score * 100)}%</span>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 w-full max-w-4xl mx-auto">
        <div className="bg-gradient-to-br from-rose-50 to-orange-50 rounded-xl border border-rose-100 shadow-sm p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 text-center sm:text-left">
          <span className="text-xs text-rose-800 font-semibold">Falls today</span>
          <span className="text-xl font-bold text-rose-900 tabular-nums">{todayCount}</span>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 text-center sm:text-left">
          <span className="text-xs text-slate-500 font-medium">In buffer</span>
          <span className="text-xl font-bold text-slate-800 tabular-nums">{totalCount}</span>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 text-center sm:text-left min-w-0">
          <span className="text-xs text-slate-500 font-medium">Last fall</span>
          <span className="text-sm font-medium text-slate-700 break-words">{lastFall}</span>
        </div>
      </div>

      {!loading && events.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="rounded-2xl border border-fuchsia-100 bg-white p-5 shadow-sm">
            <h2 className="text-sm font-bold text-fuchsia-900 mb-1">Confidence buckets</h2>
            <p className="text-xs text-slate-500 mb-3">Model certainty for all loaded events</p>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={hist}>
                <CartesianGrid strokeDasharray="3 3" stroke="#fdf4ff" />
                <XAxis dataKey="range" tick={{ fontSize: 10, fill: "#86198f" }} axisLine={false} tickLine={false} />
                <YAxis width={28} allowDecimals={false} tick={{ fontSize: 10, fill: "#86198f" }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ borderRadius: 12 }} />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {hist.map((_, i) => (
                    <Cell key={i} fill={HIST_FILLS[i] ?? C.blush} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="rounded-2xl border border-orange-100 bg-gradient-to-b from-orange-50/50 to-white p-5 shadow-sm">
            <h2 className="text-sm font-bold text-orange-900 mb-1">Events by day</h2>
            <p className="text-xs text-slate-500 mb-3">Last several days with activity</p>
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={byDay} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="fallsPageArea" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={C.peach} stopOpacity={0.4} />
                    <stop offset="100%" stopColor={C.peach} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffedd5" />
                <XAxis dataKey="day" tick={{ fontSize: 9, fill: "#9a3412" }} axisLine={false} tickLine={false} />
                <YAxis width={28} allowDecimals={false} tick={{ fontSize: 10, fill: "#9a3412" }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ borderRadius: 12 }} />
                <Area type="monotone" dataKey="count" stroke={C.peach} strokeWidth={2} fill="url(#fallsPageArea)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl border border-slate-100 shadow-sm">
        <div className="px-5 py-4 border-b border-slate-50">
          <h2 className="font-semibold text-slate-800">Fall events</h2>
        </div>
        {loading ? (
          <p className="text-center text-slate-400 py-10">Loading fall events…</p>
        ) : events.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-100/70 text-emerald-600 mb-3">
              <IconCalmCheck className="w-9 h-9" />
            </div>
            <p className="text-sm font-semibold text-slate-800">No falls in the buffer</p>
            <p className="text-xs text-slate-500 mt-1 max-w-sm leading-relaxed">
              The entrance view is clear. If you expect activity, confirm the fall worker is running on the door camera
              stream.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-100">
                  <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wide px-5 py-3">Time</th>
                  <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wide px-5 py-3">Confidence</th>
                  <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wide px-5 py-3">Details</th>
                  <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wide px-5 py-3">Severity</th>
                </tr>
              </thead>
              <tbody>
                {events.map((e) => (
                  <tr key={e.anomaly_id} className="border-b border-slate-50 last:border-0 hover:bg-rose-50/30">
                    <td className="px-5 py-3 text-sm text-slate-700 whitespace-nowrap">{fmtTime(e.timestamp)}</td>
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-20 h-2 bg-slate-100 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${confidenceColor(e.anomaly_score)}`}
                            style={{ width: `${Math.min(100, e.anomaly_score * 100)}%` }}
                          />
                        </div>
                        <span className="text-xs font-medium text-slate-600">{Math.round(e.anomaly_score * 100)}%</span>
                      </div>
                    </td>
                    <td className="px-5 py-3 text-sm text-slate-600 max-w-md truncate" title={e.description}>
                      {e.description}
                    </td>
                    <td className="px-5 py-3">
                      <span className="bg-rose-100 text-rose-800 text-xs font-semibold px-2 py-0.5 rounded-full ring-1 ring-rose-200/80">
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
