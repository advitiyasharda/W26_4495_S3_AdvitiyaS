"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import {
  getObjectEvents,
  getObjectStatus,
  ObjectCategory,
  ObjectDetectionEvent,
  ObjectSeverity,
  ObjectStatusResponse,
} from "@/lib/api";
import {
  OBJECT_CATEGORIES,
  OBJECT_CATEGORY_GUIDE,
  OBJECT_SEVERITIES,
  avgConfidence,
  countByCategory,
  countBySeverity,
  eventNeedsReview,
  normalizeObjectCategory,
  objectEventsPerHour,
  sortEventsByAttention,
} from "@/lib/objectAnalytics";
import { chart as chartPalette, objectCategoryFill, severityFill } from "@/lib/theme";
import ObjectCategoryBar from "@/components/ObjectCategoryBar";
import { ObjectCategoryIcon } from "@/components/icons/ObjectCategoryIcons";
import PageHero from "@/components/PageHero";
import { IconDownload, IconObjectFrame } from "@/components/icons/DoorIcons";
import { downloadCsv, objectsToCsvRows } from "@/lib/reportExport";
import { DEMO_OBJECT_EVENTS, DEMO_OBJECT_STATUS } from "@/lib/demoData";
import { demoFallbackEnabled, emptyOrDemo, nullOrDemo } from "@/lib/demoMode";

function fmtTime(iso: string) {
  return new Date(iso).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

const SEVERITY_STYLES: Record<ObjectSeverity, string> = {
  CRITICAL: "bg-rose-100 text-rose-900 ring-1 ring-rose-200/80",
  HIGH: "bg-orange-100 text-orange-900 ring-1 ring-orange-200/80",
  MEDIUM: "bg-amber-100 text-amber-900 ring-1 ring-amber-200/80",
  INFO: "bg-sky-100 text-sky-900 ring-1 ring-sky-200/80",
  LOW: "bg-slate-100 text-slate-700 ring-1 ring-slate-200/80",
};

function SeverityBadge({ severity }: { severity: ObjectSeverity }) {
  return (
    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${SEVERITY_STYLES[severity]}`}>{severity}</span>
  );
}

function confTone(c: number): string {
  if (c >= 0.75) return "bg-emerald-400";
  if (c >= 0.45) return "bg-amber-300";
  return "bg-slate-300";
}

export default function ObjectsPage() {
  const [allEvents, setAllEvents] = useState<ObjectDetectionEvent[]>([]);
  const [status, setStatus] = useState<ObjectStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [usingDemo, setUsingDemo] = useState(false);
  const [categoryFilter, setCategoryFilter] = useState<ObjectCategory | "">("");
  const [severityFilter, setSeverityFilter] = useState<ObjectSeverity | "">("");

  const load = useCallback(async () => {
    setLoading(true);
    const [eventsData, statusData] = await Promise.all([
      getObjectEvents(280, undefined, undefined),
      getObjectStatus(),
    ]);
    const apiEv = eventsData?.events ?? [];
    setUsingDemo(apiEv.length === 0 && demoFallbackEnabled());
    setAllEvents(emptyOrDemo(apiEv, DEMO_OBJECT_EVENTS));
    setStatus(nullOrDemo(statusData, DEMO_OBJECT_STATUS));
    setLoading(false);
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(load, 15_000);
    return () => clearInterval(id);
  }, [load]);

  const filtered = useMemo(() => {
    return allEvents.filter((e) => {
      if (categoryFilter && normalizeObjectCategory(e.category) !== categoryFilter) return false;
      if (severityFilter && e.severity !== severityFilter) return false;
      return true;
    });
  }, [allEvents, categoryFilter, severityFilter]);

  const byCat = useMemo(() => countByCategory(filtered), [filtered]);
  const bySev = useMemo(() => countBySeverity(filtered), [filtered]);
  const hourly = useMemo(() => objectEventsPerHour(filtered), [filtered]);
  const hourlyMax = useMemo(() => (hourly.length ? Math.max(...hourly.map((h) => h.count), 1) : 1), [hourly]);
  const avgConf = useMemo(() => avgConfidence(filtered), [filtered]);

  const todayStr = new Date().toDateString();
  const todayCount = filtered.filter((e) => new Date(e.timestamp).toDateString() === todayStr).length;
  const needsReviewCount = useMemo(() => filtered.filter(eventNeedsReview).length, [filtered]);

  const sortedRows = useMemo(() => sortEventsByAttention(filtered), [filtered]);

  const sevTotal = OBJECT_SEVERITIES.reduce((s, k) => s + bySev[k], 0);

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      <PageHero
        tone="violet"
        eyebrow="Smart door · Same camera as access"
        title="Object detection"
        icon={<IconObjectFrame className="w-6 h-6" />}
        description={
          <>
            YOLO tags what appears in the doorway: weapons, parcels, mobility aids, and routine items. Use the chips to
            filter; the list is ordered with the most important rows first.
          </>
        }
        aside={
          <div className="flex flex-wrap items-center gap-2">
            {usingDemo && (
              <span className="text-xs font-semibold px-2.5 py-1 rounded-full border border-violet-200/90 bg-violet-50 text-violet-900">
                Sample data
              </span>
            )}
            <span
              className={`text-sm font-semibold px-3 py-1.5 rounded-full border ${
                status?.detector_ready
                  ? "bg-emerald-50 text-emerald-800 border-emerald-200/90"
                  : "bg-rose-50 text-rose-900 border-rose-200/80"
              }`}
            >
              {status?.detector_ready ? "Live" : "Offline"}
            </span>
            {status?.weapon_model_ready && (
              <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-violet-100/90 text-violet-900 border border-violet-200/70">
                Weapon model
              </span>
            )}
            <button
              type="button"
              onClick={() => downloadCsv(`object-detections-${new Date().toISOString().slice(0, 10)}.csv`, objectsToCsvRows(filtered))}
              disabled={filtered.length === 0}
              className="inline-flex items-center gap-2 text-sm font-semibold px-3 py-1.5 rounded-xl border border-violet-200/80 bg-white text-violet-900 hover:bg-violet-50/80 shadow-sm transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <IconDownload className="w-4 h-4" />
              Export CSV
            </button>
            <button
              type="button"
              onClick={load}
              className="text-sm font-semibold px-3 py-1.5 rounded-xl border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 shadow-sm"
            >
              Refresh
            </button>
          </div>
        }
      />

      {status && !status.detector_ready && (
        <div className="rounded-2xl bg-amber-50 border border-amber-200/90 text-amber-950 px-4 py-3 text-sm">
          Detector offline. {status.message ?? "Check the backend and ultralytics install."}
        </div>
      )}

      {/* Summary strip */}
      <div className="rounded-2xl border border-slate-200/70 bg-gradient-to-br from-white via-violet-50/20 to-white p-6 shadow-sm">
        <div className="grid grid-cols-3 gap-6 text-center sm:text-left sm:flex sm:items-end sm:justify-between sm:gap-8">
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">Detections</p>
            <p className="text-3xl font-semibold text-slate-900 tabular-nums mt-1">{filtered.length}</p>
            <p className="text-xs text-slate-400 mt-1">{todayCount} today</p>
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">Flagged</p>
            <p className="text-3xl font-semibold text-amber-900 tabular-nums mt-1">{needsReviewCount}</p>
            <p className="text-xs text-amber-800/70 mt-1">worth a quick look</p>
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">Avg confidence</p>
            <p className="text-3xl font-semibold text-slate-900 tabular-nums mt-1">
              {avgConf == null ? "—" : `${Math.round(avgConf * 100)}%`}
            </p>
            <p className="text-xs text-slate-400 mt-1">in this view</p>
          </div>
        </div>

        {sevTotal > 0 && (
          <div className="mt-6 pt-5 border-t border-slate-100">
            <p className="text-[11px] font-medium text-slate-400 uppercase tracking-wide mb-2">Severity mix</p>
            <div className="flex h-3 rounded-full overflow-hidden ring-1 ring-slate-100">
              {OBJECT_SEVERITIES.map((s) => {
                const v = bySev[s];
                if (!v) return null;
                const pct = (v / sevTotal) * 100;
                return (
                  <div
                    key={s}
                    className="h-full min-w-[4px] transition-all duration-500"
                    style={{ width: `${pct}%`, backgroundColor: severityFill[s] ?? "#cbd5e1" }}
                    title={`${s}: ${v}`}
                  />
                );
              })}
            </div>
            <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-[11px] text-slate-500">
              {OBJECT_SEVERITIES.filter((s) => bySev[s] > 0).map((s) => (
                <span key={s} className="inline-flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full shrink-0" style={{ background: severityFill[s] }} />
                  {s} <span className="text-slate-400 tabular-nums">({bySev[s]})</span>
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="space-y-3">
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Filter</p>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => setCategoryFilter("")}
            className={`text-xs font-semibold px-3 py-2 rounded-xl border transition-all ${
              !categoryFilter
                ? "bg-slate-900 text-white border-slate-900 shadow-sm"
                : "bg-white text-slate-600 border-slate-200 hover:border-slate-300"
            }`}
          >
            All
          </button>
          {OBJECT_CATEGORIES.map((cat) => {
            const active = categoryFilter === cat;
            return (
              <button
                key={cat}
                type="button"
                onClick={() => setCategoryFilter((c) => (c === cat ? "" : cat))}
                className={`text-xs font-semibold px-3 py-2 rounded-xl border transition-all inline-flex items-center gap-2 ${
                  active ? "text-white shadow-sm border-transparent" : "bg-white text-slate-600 border-slate-200 hover:border-slate-300"
                }`}
                style={
                  active
                    ? { backgroundColor: objectCategoryFill[cat], borderColor: objectCategoryFill[cat] }
                    : undefined
                }
              >
                <ObjectCategoryIcon
                  category={cat}
                  className={`w-4 h-4 shrink-0 ${active ? "text-white/95" : "text-teal-600/85"}`}
                />
                {OBJECT_CATEGORY_GUIDE[cat].shortLabel}
              </button>
            );
          })}
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <label className="text-xs text-slate-500">Severity</label>
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value as ObjectSeverity | "")}
            className="text-sm rounded-xl border border-slate-200 bg-white px-3 py-2 text-slate-800 focus:outline-none focus:ring-2 focus:ring-violet-300/50"
          >
            <option value="">Any</option>
            {OBJECT_SEVERITIES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Category volume — single main viz */}
      <section className="rounded-2xl border border-slate-200/70 bg-white p-6 shadow-sm">
        <h2 className="text-sm font-semibold text-slate-800">By category</h2>
        <p className="text-xs text-slate-500 mt-0.5 mb-5">How detections split across policy buckets</p>
        <ObjectCategoryBar events={filtered} />
        <div className="mt-5 flex flex-wrap gap-3 text-xs text-slate-500">
          {OBJECT_CATEGORIES.map((c) => (
            <span key={c} className="tabular-nums">
              <span className="font-medium text-slate-700">{OBJECT_CATEGORY_GUIDE[c].shortLabel}</span> {byCat[c]}
            </span>
          ))}
        </div>
      </section>

      {/* Timeline — area chart matches KPI modal language; respects filters */}
      <section className="rounded-2xl border border-slate-200/70 bg-white p-6 shadow-sm">
        <h2 className="text-sm font-semibold text-slate-800">Activity by hour</h2>
        <p className="text-xs text-slate-500 mt-0.5 mb-4">Local time · same metric as the dashboard object card detail</p>
        {hourly.length === 0 ? (
          <p className="text-sm text-slate-400 py-16 text-center">No events in this view</p>
        ) : (
          <div className="h-[220px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={hourly} margin={{ top: 8, right: 8, left: -8, bottom: 0 }}>
                <defs>
                  <linearGradient id="objectsPageHourGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={chartPalette.lilac} stopOpacity={0.4} />
                    <stop offset="100%" stopColor={chartPalette.lilac} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis dataKey="hour" tick={{ fontSize: 10, fill: "#94a3b8" }} interval={3} axisLine={false} tickLine={false} />
                <YAxis
                  width={36}
                  domain={[0, Math.ceil(hourlyMax * 1.1)]}
                  allowDecimals={false}
                  tick={{ fontSize: 10, fill: "#94a3b8" }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  cursor={{ stroke: chartPalette.lilac, strokeWidth: 1, strokeDasharray: "4 4" }}
                  contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0", fontSize: 12 }}
                />
                <Area
                  type="monotone"
                  dataKey="count"
                  stroke={chartPalette.lilac}
                  strokeWidth={2}
                  fill="url(#objectsPageHourGrad)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </section>

      {/* Table */}
      <section className="rounded-2xl border border-slate-200/70 bg-white shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex flex-wrap items-end justify-between gap-2">
          <div>
            <h2 className="text-sm font-semibold text-slate-800">Recent detections</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Urgent first · {sortedRows.length} row{sortedRows.length !== 1 ? "s" : ""}
            </p>
          </div>
          <div className="flex gap-3 text-xs">
            <a href="/logs" className="font-medium text-teal-700 hover:underline">
              Access logs
            </a>
            <a href="/alerts" className="font-medium text-amber-800 hover:underline">
              Alerts
            </a>
          </div>
        </div>
        {loading ? (
          <p className="text-center text-slate-400 py-14">Loading…</p>
        ) : sortedRows.length === 0 ? (
          <div className="py-14 px-6 text-center text-slate-500 text-sm">Nothing matches these filters.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50/90">
                  <th className="w-8 px-3 py-3" />
                  <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wide px-3 py-3">When</th>
                  <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wide px-3 py-3">Object</th>
                  <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wide px-3 py-3">Category</th>
                  <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wide px-3 py-3 hidden sm:table-cell">
                    Confidence
                  </th>
                  <th className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wide px-3 py-3">Severity</th>
                </tr>
              </thead>
              <tbody>
                {sortedRows.map((e, idx) => {
                  const review = eventNeedsReview(e);
                  const cat = normalizeObjectCategory(e.category);
                  return (
                    <tr
                      key={`${e.timestamp}-${e.object_class}-${idx}`}
                      className={`border-b border-slate-50 last:border-0 ${review ? "bg-amber-50/40" : "hover:bg-slate-50/80"}`}
                    >
                      <td className="px-3 py-3 text-center">
                        {review ? <span className="inline-block size-2 rounded-full bg-amber-500" title="Flagged" /> : null}
                      </td>
                      <td className="px-3 py-3 whitespace-nowrap text-slate-600 text-xs">{fmtTime(e.timestamp)}</td>
                      <td className="px-3 py-3 font-medium text-slate-800 capitalize">{e.object_class.replace(/_/g, " ")}</td>
                      <td className="px-3 py-3">
                        <span className="inline-flex items-center gap-1.5 text-xs text-slate-700">
                          <ObjectCategoryIcon category={cat} className="w-4 h-4 text-teal-600/80 shrink-0" />
                          {OBJECT_CATEGORY_GUIDE[cat].shortLabel}
                        </span>
                      </td>
                      <td className="px-3 py-3 hidden sm:table-cell">
                        <div className="flex items-center gap-2 max-w-[140px]">
                          <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full ${confTone(e.confidence)}`}
                              style={{ width: `${Math.min(100, e.confidence * 100)}%` }}
                            />
                          </div>
                          <span className="text-xs tabular-nums text-slate-500 w-9">{Math.round(e.confidence * 100)}%</span>
                        </div>
                      </td>
                      <td className="px-3 py-3">
                        <SeverityBadge severity={e.severity} />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {status?.detector_ready && (
        <p className="text-center text-xs text-slate-400 px-4">
          Threshold {Math.round((status.confidence ?? 0) * 100)}% · {status.frame_threshold} frames · Unattended{" "}
          {status.unattended_minutes}m · {status.events_logged.toLocaleString()} events on server
        </p>
      )}
    </div>
  );
}
