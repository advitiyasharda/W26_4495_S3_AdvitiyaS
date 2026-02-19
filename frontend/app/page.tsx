"use client";

import { useEffect, useState, useCallback } from "react";
import { getStats, getAccessLogs, StatsResponse, AccessLog } from "@/lib/api";
import { DEMO_LOGS } from "@/lib/demoData";
import StatCard from "@/components/StatCard";
import AccessLogsTable from "@/components/AccessLogsTable";
import AccessChart from "@/components/AccessChart";
import StatusDonut from "@/components/StatusDonut";

// ── Small inline icons ────────────────────────────────────────────────────────
const EntryIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} className="w-4 h-4">
    <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" />
    <polyline points="10 17 15 12 10 7" /><line x1="15" y1="12" x2="3" y2="12" />
  </svg>
);
const ExitIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} className="w-4 h-4">
    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
    <polyline points="16 17 21 12 16 7" /><line x1="21" y1="12" x2="9" y2="12" />
  </svg>
);
const AlertIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} className="w-4 h-4">
    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
    <path d="M13.73 21a2 2 0 0 1-3.46 0" />
  </svg>
);
const CheckIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} className="w-4 h-4">
    <polyline points="20 6 9 17 4 12" />
  </svg>
);
const RefreshIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} className="w-4 h-4">
    <polyline points="23 4 23 10 17 10" /><polyline points="1 20 1 14 7 14" />
    <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
  </svg>
);

export default function DashboardPage() {
  const [stats, setStats]     = useState<StatsResponse | null>(null);
  const [logs, setLogs]       = useState<AccessLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [usingDemo, setUsingDemo] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const refresh = useCallback(async () => {
    setLoading(true);
    const [s, l] = await Promise.all([getStats(), getAccessLogs(50)]);

    const hasRealPeople = l?.logs.some((log) => log.person_id != null && log.name != null);

    if (hasRealPeople) {
      setLogs(l!.logs);
      setUsingDemo(false);
    } else {
      setLogs(DEMO_LOGS);
      setUsingDemo(true);
    }

    if (s) {
      setStats(s);
    } else if (!s) {
      // synthetic stats derived from demo logs
      const entries = DEMO_LOGS.filter((x) => x.type === "entry").length;
      const exits   = DEMO_LOGS.filter((x) => x.type === "exit").length;
      setStats({ access_events: { total_entries: entries, total_exits: exits, today: DEMO_LOGS.length }, threats: { active_alerts: 3 } });
    }

    setLoading(false);
    setLastRefresh(new Date());
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 30_000);
    return () => clearInterval(id);
  }, [refresh]);

  const recent = logs.slice(0, 8);

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Dashboard</h1>
          <div className="flex items-center gap-2 mt-0.5">
            <p className="text-sm text-slate-400">Last updated {lastRefresh.toLocaleTimeString()}</p>
            {usingDemo && (
              <span className="bg-amber-50 text-amber-600 text-xs font-medium px-2.5 py-0.5 rounded-full border border-amber-200">
                Demo data
              </span>
            )}
          </div>
        </div>
        <button
          onClick={refresh}
          className="flex items-center gap-2 bg-white border border-slate-200 text-slate-600 text-sm font-medium px-4 py-2 rounded-lg hover:bg-slate-50 hover:border-slate-300 transition-colors shadow-sm"
        >
          <RefreshIcon /> Refresh
        </button>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Entries Today"
          value={stats?.access_events.total_entries ?? "—"}
          sub="Entry events"
          icon={<EntryIcon />}
          trend={{ value: 2.5 }}
        />
        <StatCard
          title="Total Exits Today"
          value={stats?.access_events.total_exits ?? "—"}
          sub="Exit events"
          icon={<ExitIcon />}
          trend={{ value: -0.8 }}
        />
        <StatCard
          title="Active Alerts"
          value={stats?.threats.active_alerts ?? "—"}
          sub="Critical / High severity"
          icon={<AlertIcon />}
          trend={{ value: stats?.threats.active_alerts && stats.threats.active_alerts > 0 ? 1 : 0 }}
        />
        <StatCard
          title="System Status"
          value={
            <span className="flex items-center gap-2 text-emerald-500 text-2xl font-bold">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
              Online
            </span>
          }
          sub="All systems operational"
          icon={<CheckIcon />}
        />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Bar chart */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-100 shadow-sm p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="font-semibold text-slate-800">Access Activity</h2>
              <p className="text-xs text-slate-400 mt-0.5">Entries &amp; exits by hour</p>
            </div>
            <div className="flex items-center gap-3 text-xs text-slate-500">
              <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm bg-emerald-500 inline-block"/>Entries</span>
              <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm bg-slate-300 inline-block"/>Exits</span>
            </div>
          </div>
          <AccessChart logs={logs} />
        </div>

        {/* Donut chart */}
        <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
          <div className="mb-4">
            <h2 className="font-semibold text-slate-800">Access Breakdown</h2>
            <p className="text-xs text-slate-400 mt-0.5">Status distribution</p>
          </div>
          <StatusDonut logs={logs} />
        </div>
      </div>

      {/* Recent activity table */}
      <div className="bg-white rounded-xl border border-slate-100 shadow-sm">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-50">
          <h2 className="font-semibold text-slate-800">Recent Access Activity</h2>
          <a href="/logs" className="text-xs text-emerald-600 font-medium hover:text-emerald-700">
            View all →
          </a>
        </div>
        <AccessLogsTable logs={recent} loading={loading} />
      </div>
    </div>
  );
}
