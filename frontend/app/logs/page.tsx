"use client";

import { useEffect, useState } from "react";
import { getAccessLogs, AccessLog } from "@/lib/api";
import { DEMO_LOGS } from "@/lib/demoData";
import AccessLogsTable from "@/components/AccessLogsTable";

export default function LogsPage() {
  const [logs, setLogs]           = useState<AccessLog[]>([]);
  const [loading, setLoading]     = useState(true);
  const [limit, setLimit]         = useState(20);
  const [usingDemo, setUsingDemo] = useState(false);
  const [showAll, setShowAll]     = useState(false);

  const load = async (l: number) => {
    setLoading(true);
    const data = await getAccessLogs(l);

    // Use real data only when at least one record has a known person
    // Use != null (loose) to catch both null and undefined (field name mismatches)
    const hasRealPeople = data?.logs.some((log) => log.person_id != null && log.name != null);

    if (hasRealPeople) {
      setLogs(data!.logs);
      setUsingDemo(false);
    } else {
      setLogs(showAll ? DEMO_LOGS : DEMO_LOGS.slice(0, l));
      setUsingDemo(true);
    }
    setLoading(false);
  };

  useEffect(() => { load(limit); }, [limit, showAll]); // eslint-disable-line

  const displayed = logs;
  const hasMore   = usingDemo
    ? displayed.length < DEMO_LOGS.length
    : displayed.length === limit;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Access Logs</h1>
          <div className="flex items-center gap-2 mt-0.5">
            <p className="text-sm text-slate-400">Full audit trail of all door access events</p>
            {usingDemo && (
              <span className="bg-amber-50 text-amber-600 text-xs font-medium px-2.5 py-0.5 rounded-full border border-amber-200">
                Demo data
              </span>
            )}
          </div>
        </div>
        <span className="bg-slate-100 text-slate-600 text-sm font-medium px-3 py-1 rounded-full">
          {displayed.length} records
        </span>
      </div>

      {/* Summary strip */}
      {!loading && displayed.length > 0 && (
        <div className="grid grid-cols-3 gap-3">
          {[
            {
              label: "Successful",
              value: displayed.filter((l) => l.status === "success").length,
              color: "text-emerald-600",
              bg: "bg-emerald-50",
            },
            {
              label: "Failed",
              value: displayed.filter((l) => l.status !== "success").length,
              color: "text-red-500",
              bg: "bg-red-50",
            },
            {
              label: "Unique People",
              value: new Set(displayed.map((l) => l.person_id).filter(Boolean)).size,
              color: "text-slate-700",
              bg: "bg-slate-50",
            },
          ].map((s) => (
            <div key={s.label} className={`${s.bg} rounded-xl px-4 py-3 flex items-center justify-between`}>
              <span className="text-xs text-slate-500 font-medium">{s.label}</span>
              <span className={`text-xl font-bold ${s.color}`}>{s.value}</span>
            </div>
          ))}
        </div>
      )}

      {/* Table */}
      <AccessLogsTable logs={displayed} loading={loading} />

      {/* Load more */}
      {hasMore && (
        <button
          onClick={() => {
            if (usingDemo) setShowAll(true);
            else setLimit((p) => p + 30);
          }}
          className="flex items-center gap-2 bg-white border border-slate-200 text-slate-600 text-sm font-medium px-4 py-2 rounded-lg hover:bg-slate-50 transition-colors shadow-sm"
        >
          Load more
          <span className="text-slate-400 text-xs">
            ({usingDemo ? DEMO_LOGS.length - displayed.length : "30"} remaining)
          </span>
        </button>
      )}
    </div>
  );
}
