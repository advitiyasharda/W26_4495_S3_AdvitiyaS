"use client";

import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import Link from "next/link";
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
import {
  getStats,
  getAccessLogs,
  getFallEvents,
  getFallStatus,
  getObjectEvents,
  getObjectStatus,
  getThreats,
  type StatsResponse,
  type AccessLog,
  type FallEvent,
  type ObjectDetectionEvent,
  type Threat,
  type FallStatusResponse,
  type ObjectStatusResponse,
} from "@/lib/api";
import {
  DEMO_LOGS,
  DEMO_THREATS,
  DEMO_FALL_EVENTS,
  DEMO_OBJECT_EVENTS,
  DEMO_OBJECT_STATUS,
  DEMO_FALL_STATUS,
  emptyOrDemo,
  nullOrDemo,
} from "@/lib/demoData";
import { fallConfidenceHistogram, fallsPerDay } from "@/lib/chartPrep";
import { chart as C } from "@/lib/theme";
import {
  filterByTimeRange,
  TIME_RANGE_OPTIONS,
  type TimeRangeId,
} from "@/lib/timeRange";
import { downloadCsv, logsToCsvRows } from "@/lib/reportExport";
import AccessChart from "@/components/AccessChart";
import StatusDonut from "@/components/StatusDonut";
import NetFlowLine from "@/components/dashboard/NetFlowLine";
import { objectEventsPerHour } from "@/lib/objectAnalytics";
import ObjectCategoryBar from "@/components/ObjectCategoryBar";
import PageHero from "@/components/PageHero";
import { IconDoorPanel } from "@/components/icons/DoorIcons";
import ThreatSeverityBar from "@/components/dashboard/ThreatSeverityBar";
import DoorTrafficCard from "@/components/dashboard/DoorTrafficCard";
import StatCard from "@/components/StatCard";
import KpiInsightModal from "@/components/dashboard/KpiInsightModal";
import {
  fallInsightSummary,
  objectInsightSummary,
  peakHourLabel,
  threatSeverityBreakdown,
} from "@/lib/dashboardInsights";
import {
  accessTrafficHealth,
  alertsHealth,
  fallsHealth,
  objectsHealth,
} from "@/lib/dashboardKpiHealth";
import type { DashboardScrollSection, InsightId } from "@/components/dashboard/dashboardCardTypes";

const HIST_FILLS = ["#fce7f3", "#fbcfe8", "#f9a8d4", "#f472b6", "#ec4899"];

const ACCENT_BAR = {
  teal: "bg-teal-500",
  amber: "bg-amber-500",
  violet: "bg-violet-500",
  rose: "bg-rose-500",
  slate: "bg-slate-400",
} as const;

type AccentKey = keyof typeof ACCENT_BAR;

function OpsSection({
  accent,
  kicker,
  title,
  description,
  action,
  children,
  sectionId,
}: {
  accent: AccentKey;
  kicker: string;
  title: string;
  description: string;
  action?: ReactNode;
  children: ReactNode;
  sectionId?: DashboardScrollSection;
}) {
  return (
    <section
      id={sectionId ? `section-${sectionId}` : undefined}
      className="rounded-2xl border border-slate-200/70 bg-white/80 shadow-sm overflow-hidden scroll-mt-6"
    >
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 px-5 py-4 border-b border-slate-100/90 bg-slate-50/50">
        <div className="flex gap-3 min-w-0">
          <div className={`w-1 shrink-0 rounded-full ${ACCENT_BAR[accent]}`} aria-hidden />
          <div className="min-w-0">
            <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-400">{kicker}</p>
            <h2 className="text-base font-semibold text-slate-900 tracking-tight mt-0.5">{title}</h2>
            <p className="text-xs text-slate-500 mt-1 leading-relaxed">{description}</p>
          </div>
        </div>
        {action ? <div className="shrink-0 flex flex-wrap items-center gap-2">{action}</div> : null}
      </div>
      <div className="p-5">{children}</div>
    </section>
  );
}

function VizCard({ label, hint, children }: { label: string; hint: string; children: ReactNode }) {
  return (
    <div className="rounded-xl border border-slate-100/90 bg-slate-50/20 p-4">
      <div className="mb-3">
        <h3 className="text-sm font-semibold text-slate-800">{label}</h3>
        <p className="text-[11px] text-slate-500 mt-0.5">{hint}</p>
      </div>
      {children}
    </div>
  );
}

const RefreshIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} className="w-4 h-4">
    <polyline points="23 4 23 10 17 10" />
    <polyline points="1 20 1 14 7 14" />
    <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
  </svg>
);

const AlertIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} className="w-6 h-6 transition-transform duration-300 group-hover:scale-110 group-hover:text-amber-600" aria-labelledby="alert-icon-title" role="img">
    <title id="alert-icon-title">FaceDoor Security Threats (Unrecognized faces, tailgating)</title>
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M12 8v4" strokeLinecap="round" strokeLinejoin="round" className="text-amber-500" />
    <circle cx="12" cy="16" r="1" fill="currentColor" stroke="none" className="text-amber-500" />
    <path d="M8 5v14M16 5v14" opacity={0.15} />
  </svg>
);

const FallIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} className="w-6 h-6 transition-transform duration-300 group-hover:scale-110 group-hover:text-rose-600" aria-labelledby="fall-icon-title" role="img">
    <title id="fall-icon-title">MediaPipe Pose Detection: Fall Events Tracker</title>
    <path d="M3 20h18" strokeLinecap="round" strokeDasharray="2 4" className="text-rose-300" />
    <circle cx="16" cy="13" r="2.5" />
    <path d="M16 15.5l-3.5 3.5M16 15.5l-1.5-4 4-2" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M8 8c2.5 0 4.5 1.5 5.5 3.5" strokeDasharray="2 2" strokeLinecap="round" opacity={0.4} />
  </svg>
);

const ObjectIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} className="w-6 h-6 transition-transform duration-300 group-hover:scale-110 group-hover:text-violet-600" aria-labelledby="object-icon-title" role="img">
    <title id="object-icon-title">Camera Frame Object Detection (Parcels, equipment)</title>
    <path d="M4 4h16v16H4z" strokeDasharray="4 4" strokeLinecap="round" opacity={0.4} />
    <rect x="8" y="10" width="8" height="6" rx="1.5" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M8 13h8" strokeLinecap="round" opacity={0.4}/>
    <path d="M2 13h20" className="text-violet-400 opacity-50" strokeLinecap="round" strokeDasharray="1 6"/>
  </svg>
);

function matchPct(logs: AccessLog[], type: "entry" | "exit"): number | null {
  const rows = logs.filter((l) => l.type === type);
  if (rows.length === 0) return null;
  return Math.round((rows.filter((l) => l.status === "success").length / rows.length) * 100);
}

export default function UnifiedDashboard() {
  const [timeRange, setTimeRange] = useState<TimeRangeId>("7d");
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [logsRaw, setLogsRaw] = useState<AccessLog[]>([]);
  const [fallsRaw, setFallsRaw] = useState<FallEvent[]>([]);
  const [objectsRaw, setObjectsRaw] = useState<ObjectDetectionEvent[]>([]);
  const [threatsRaw, setThreatsRaw] = useState<Threat[]>([]);
  const [fallStatus, setFallStatus] = useState<FallStatusResponse | null>(null);
  const [objectStatus, setObjectStatus] = useState<ObjectStatusResponse | null>(null);
  const [usingDemo, setUsingDemo] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  const [mounted, setMounted] = useState(false);
  const [insight, setInsight] = useState<InsightId | null>(null);

  const refresh = useCallback(async () => {
    const [s, l, fallData, objData, thData, fs, os] = await Promise.all([
      getStats(),
      getAccessLogs(280),
      getFallEvents(150),
      getObjectEvents(150),
      getThreats(),
      getFallStatus(),
      getObjectStatus(),
    ]);

    const hasRealPeople = l?.logs.some((log) => log.person_id != null && log.name != null);
    if (hasRealPeople) {
      setLogsRaw(l!.logs);
      setUsingDemo(false);
    } else {
      setLogsRaw(DEMO_LOGS);
      setUsingDemo(true);
    }

    if (s) setStats(s);
    else {
      const entries = DEMO_LOGS.filter((x) => x.type === "entry").length;
      const exits = DEMO_LOGS.filter((x) => x.type === "exit").length;
      setStats({
        access_events: { total_entries: entries, total_exits: exits, today: DEMO_LOGS.length },
        threats: { active_alerts: DEMO_THREATS.length },
      });
    }

    const apiFalls = fallData?.events ?? [];
    setFallsRaw(emptyOrDemo(apiFalls, DEMO_FALL_EVENTS));

    const apiO = objData?.events ?? [];
    setObjectsRaw(emptyOrDemo(apiO, DEMO_OBJECT_EVENTS));

    const apiT = thData?.threats ?? [];
    setThreatsRaw(emptyOrDemo(apiT, DEMO_THREATS));

    setFallStatus(nullOrDemo(fs, DEMO_FALL_STATUS));
    setObjectStatus(nullOrDemo(os, DEMO_OBJECT_STATUS));
    setLastRefresh(new Date());
  }, []);

  useEffect(() => {
    setMounted(true);
  }, []);
  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 10_000);
    return () => clearInterval(id);
  }, [refresh]);

  useEffect(() => {
    const handleWindowFocus = () => {
      void refresh();
    };
    const handleVisibilityChange = () => {
      if (document.visibilityState === "visible") {
        void refresh();
      }
    };

    window.addEventListener("focus", handleWindowFocus);
    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      window.removeEventListener("focus", handleWindowFocus);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [refresh]);

  const logs = useMemo(() => filterByTimeRange(logsRaw, (x) => x.timestamp, timeRange), [logsRaw, timeRange]);
  const falls = useMemo(() => filterByTimeRange(fallsRaw, (x) => x.timestamp, timeRange), [fallsRaw, timeRange]);
  const objects = useMemo(() => filterByTimeRange(objectsRaw, (x) => x.timestamp, timeRange), [objectsRaw, timeRange]);
  const threats = useMemo(() => filterByTimeRange(threatsRaw, (x) => x.timestamp, timeRange), [threatsRaw, timeRange]);

  const fallHist = useMemo(() => fallConfidenceHistogram(falls), [falls]);
  const fallsByDay = useMemo(() => fallsPerDay(falls), [falls]);
  const objectsHourly = useMemo(() => objectEventsPerHour(objects), [objects]);

  const rangeLabel = useMemo(
    () => TIME_RANGE_OPTIONS.find((o) => o.id === timeRange)?.label ?? timeRange,
    [timeRange]
  );

  const entriesCount = useMemo(() => logs.filter((l) => l.type === "entry").length, [logs]);
  const exitsCount = useMemo(() => logs.filter((l) => l.type === "exit").length, [logs]);

  const trafficHealth = useMemo(() => accessTrafficHealth(logs), [logs]);
  const alertHealth = useMemo(() => alertsHealth(threats), [threats]);
  const fallHealth = useMemo(() => fallsHealth(falls), [falls]);
  const objectHealth = useMemo(() => objectsHealth(objects), [objects]);

  const peakIn = useMemo(() => peakHourLabel(logs, "entry"), [logs]);
  const peakOut = useMemo(() => peakHourLabel(logs, "exit"), [logs]);
  const matchInPct = useMemo(() => matchPct(logs, "entry"), [logs]);
  const matchOutPct = useMemo(() => matchPct(logs, "exit"), [logs]);

  const fallSub = useMemo(() => {
    const fi = fallInsightSummary(falls);
    if (falls.length === 0) return "No falls in range";
    return fi.avgScore != null ? `Avg score ${fi.avgScore} · Tap for detail` : "Tap for detail";
  }, [falls]);

  const objectSub = useMemo(() => {
    const oi = objectInsightSummary(objects);
    if (objects.length === 0) return "No detections in range";
    const top = oi.topClasses[0];
    return top ? `${top.name} (${top.count}) · Tap for detail` : "Tap for detail";
  }, [objects]);

  const threatSub = useMemo(() => {
    const b = threatSeverityBreakdown(threats);
    const crit = b.CRITICAL ?? 0;
    const high = b.HIGH ?? 0;
    if (threats.length === 0) return "No threats in range";
    return `${crit} critical · ${high} high · Tap for detail`;
  }, [threats]);

  const exportAccessCsv = () => {
    downloadCsv(`access_logs_${timeRange}.csv`, logsToCsvRows(logs), [
      "timestamp",
      "type",
      "status",
      "name",
      "person_id",
      "confidence",
    ]);
  };

  const cameraOk =
    (fallStatus?.detector_ready ?? false) || (objectStatus?.detector_ready ?? false) || stats != null;

  const scrollToSection = useCallback((s: DashboardScrollSection) => {
    const el = document.getElementById(`section-${s}`);
    el?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, []);

  const sectionLink = (href: string, label: string, color: string) => (
    <Link href={href} className={`text-xs font-semibold ${color} hover:underline whitespace-nowrap`}>
      {label}
    </Link>
  );

  return (
    <div className="space-y-8 pb-10">
      <PageHero
        tone="teal"
        eyebrow="Operations"
        title="Operations dashboard"
        icon={<IconDoorPanel className="w-6 h-6" />}
        description={
          <>
            One scrollable view of access, alerts, objects, and falls. Each block is labeled; the time range applies
            everywhere below.
          </>
        }
        aside={
          <div className="flex flex-col items-stretch sm:items-end gap-2 w-full sm:w-auto">
            <div className="flex flex-wrap items-center gap-2 justify-end">
              {usingDemo && (
                <span className="bg-amber-50/95 text-amber-900 text-[11px] font-semibold px-2.5 py-1 rounded-full border border-amber-200/80">
                  Demo data
                </span>
              )}
              <span className="text-[11px] text-slate-400 tabular-nums" suppressHydrationWarning>
                Updated {mounted ? lastRefresh.toLocaleTimeString() : "—"}
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-2 justify-end">
              <label className="flex items-center gap-2 text-xs font-semibold text-slate-600">
                <span className="whitespace-nowrap">Range</span>
                <select
                  value={timeRange}
                  onChange={(e) => setTimeRange(e.target.value as TimeRangeId)}
                  className="text-sm border border-slate-200/90 rounded-xl px-2.5 py-1.5 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-400/45 shadow-sm"
                >
                  {TIME_RANGE_OPTIONS.map((o) => (
                    <option key={o.id} value={o.id}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </label>
              <button
                type="button"
                onClick={exportAccessCsv}
                className="text-xs font-semibold px-3 py-1.5 rounded-xl border border-slate-200/90 bg-white text-slate-700 hover:bg-slate-50/90 shadow-sm"
              >
                Export CSV
              </button>
              <button
                type="button"
                onClick={refresh}
                className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-xl border border-teal-200/90 bg-teal-50/50 text-teal-900 hover:bg-teal-100/80 shadow-sm"
              >
                <RefreshIcon /> Sync
              </button>
            </div>
          </div>
        }
      />

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <DoorTrafficCard
          entries={entriesCount}
          exits={exitsCount}
          health={trafficHealth}
          rangeLabel={rangeLabel}
          peakIn={peakIn}
          peakOut={peakOut}
          matchInPct={matchInPct}
          matchOutPct={matchOutPct}
          onClick={() => setInsight("traffic")}
        />
        <StatCard
          title="Security alerts"
          value={threats.length}
          sub={threatSub}
          icon={<AlertIcon />}
          accent="amber"
          health={alertHealth}
          visualKind="alerts"
          onClick={() => setInsight("alerts")}
        />
        <StatCard
          title="Fall events"
          value={falls.length}
          sub={fallSub}
          icon={<FallIcon />}
          accent="rose"
          health={fallHealth}
          visualKind="falls"
          onClick={() => setInsight("falls")}
        />
        <StatCard
          title="Object events"
          value={objects.length}
          sub={objectSub}
          icon={<ObjectIcon />}
          accent="violet"
          health={objectHealth}
          visualKind="objects"
          onClick={() => setInsight("objects")}
        />
      </div>

      <OpsSection
        accent="slate"
        kicker="Pipelines"
        title="Detector & camera status"
        description="Quick read on whether vision stacks report ready. Does not replace detailed settings on each product page."
        sectionId="pipelines"
        action={
          <>
            {sectionLink("/objects", "Object settings", "text-violet-700")}
            {sectionLink("/falls", "Fall settings", "text-rose-700")}
          </>
        }
      >
        <div className="flex flex-wrap gap-6 text-sm text-slate-700">
          <div>
            <p className="text-[11px] font-medium uppercase tracking-wide text-slate-400">Fall detector</p>
            <p className="mt-1 font-semibold tabular-nums">
              {fallStatus?.detector_ready ? "Ready" : "Off / degraded"}
            </p>
          </div>
          <div>
            <p className="text-[11px] font-medium uppercase tracking-wide text-slate-400">Object detector</p>
            <p className="mt-1 font-semibold tabular-nums">
              {objectStatus?.detector_ready ? "Ready" : "Off / degraded"}
            </p>
          </div>
          <div>
            <p className="text-[11px] font-medium uppercase tracking-wide text-slate-400">Data link</p>
            <p className="mt-1 font-semibold tabular-nums">{cameraOk ? "Active" : "Limited"}</p>
          </div>
        </div>
      </OpsSection>

      <OpsSection
        accent="teal"
        kicker="Access"
        title="Door traffic & outcomes"
        description="Hourly entries and exits, net flow, and success vs failed for the selected range."
        sectionId="access"
        action={
          <>
            {sectionLink("/logs", "Full access log", "text-teal-700")}
            <button
              type="button"
              onClick={exportAccessCsv}
              className="text-xs font-semibold text-slate-500 hover:text-teal-800 hover:underline whitespace-nowrap"
            >
              CSV
            </button>
          </>
        }
      >
        <div className="space-y-4">
          <VizCard label="Hourly entries & exits" hint="Counts by local hour for the current range">
            <AccessChart logs={logs} />
          </VizCard>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <VizCard label="Net flow" hint="Entries minus exits over time">
              <NetFlowLine logs={logs} />
            </VizCard>
            <VizCard label="Outcome mix" hint="Granted vs failed attempts">
              <StatusDonut logs={logs} />
            </VizCard>
          </div>
        </div>
      </OpsSection>

      <OpsSection
        accent="amber"
        kicker="Security"
        title="Alerts"
        description="Threat counts by severity for the same time window."
        sectionId="security"
        action={sectionLink("/alerts", "Open alerts", "text-amber-800")}
      >
        <VizCard label="By severity" hint="Stacked severities in the filtered period">
          <ThreatSeverityBar threats={threats} embedded />
        </VizCard>
      </OpsSection>

      <OpsSection
        accent="violet"
        kicker="Vision"
        title="Object detection"
        description="Category mix and hourly detection volume from the object pipeline."
        sectionId="vision"
        action={sectionLink("/objects", "Object detection log", "text-violet-700")}
      >
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <VizCard label="By category" hint="Policy-style buckets in this range">
            <ObjectCategoryBar events={objects} />
          </VizCard>
          <VizCard label="By hour" hint="When detections occurred (local time)">
            {objectsHourly.length === 0 ? (
              <p className="text-sm text-slate-400 py-12 text-center">No events</p>
            ) : (
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={objectsHourly}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="hour" tick={{ fontSize: 9, fill: "#64748b" }} interval={2} />
                  <YAxis width={28} allowDecimals={false} tick={{ fontSize: 10, fill: "#64748b" }} />
                  <Tooltip contentStyle={{ borderRadius: 12 }} />
                  <Bar dataKey="count" fill="#a78bfa" fillOpacity={0.85} radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </VizCard>
        </div>
      </OpsSection>

      <OpsSection
        accent="rose"
        kicker="Safety"
        title="Fall detection"
        description="Model score distribution and daily event counts."
        sectionId="safety"
        action={sectionLink("/falls", "Fall event log", "text-rose-700")}
      >
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <VizCard label="Confidence buckets" hint="How scores group across events">
            {falls.length === 0 ? (
              <p className="text-sm text-slate-400 py-12 text-center">No falls in this window</p>
            ) : (
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={fallHist}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#fce7f3" />
                  <XAxis dataKey="range" tick={{ fontSize: 10, fill: "#64748b" }} />
                  <YAxis width={28} allowDecimals={false} tick={{ fontSize: 10, fill: "#64748b" }} />
                  <Tooltip />
                  <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                    {fallHist.map((_, i) => (
                      <Cell key={i} fill={HIST_FILLS[i] ?? C.blush} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </VizCard>
          <VizCard label="Events by day" hint="Count per calendar day">
            {fallsByDay.length === 0 ? (
              <p className="text-sm text-slate-400 py-12 text-center">No history</p>
            ) : (
              <ResponsiveContainer width="100%" height={240}>
                <AreaChart data={fallsByDay} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="dashFallArea" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={C.blush} stopOpacity={0.35} />
                      <stop offset="100%" stopColor={C.blush} stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffe4e6" />
                  <XAxis dataKey="day" tick={{ fontSize: 10, fill: "#64748b" }} />
                  <YAxis width={28} allowDecimals={false} tick={{ fontSize: 10, fill: "#64748b" }} />
                  <Tooltip />
                  <Area type="monotone" dataKey="count" stroke={C.blush} strokeWidth={2} fill="url(#dashFallArea)" />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </VizCard>
        </div>
      </OpsSection>

      <KpiInsightModal
        insight={insight}
        open={insight != null}
        onClose={() => setInsight(null)}
        logs={logs}
        threats={threats}
        falls={falls}
        objects={objects}
        onJumpToSection={scrollToSection}
      />
    </div>
  );
}
