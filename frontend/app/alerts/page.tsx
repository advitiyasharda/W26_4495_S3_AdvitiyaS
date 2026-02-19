"use client";

import { useEffect, useState } from "react";
import { getThreats, Threat } from "@/lib/api";
import { DEMO_THREATS } from "@/lib/demoData";
import AlertList from "@/components/AlertList";

type Filter = "ALL" | "HIGH" | "CRITICAL";

const filters: { label: string; value: Filter; style: string; active: string }[] = [
  { label: "All",       value: "ALL",      style: "bg-white border border-slate-200 text-slate-600 hover:bg-slate-50",           active: "bg-slate-800 border-slate-800 text-white" },
  { label: "High",      value: "HIGH",     style: "bg-white border border-orange-200 text-orange-600 hover:bg-orange-50",        active: "bg-orange-500 border-orange-500 text-white" },
  { label: "Critical",  value: "CRITICAL", style: "bg-white border border-red-200 text-red-600 hover:bg-red-50",                 active: "bg-red-500 border-red-500 text-white" },
];

export default function AlertsPage() {
  const [threats, setThreats] = useState<Threat[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<Filter>("ALL");
  const [usingDemo, setUsingDemo] = useState(false);

  const load = async (sev: Filter) => {
    setLoading(true);
    const data = await getThreats(sev === "ALL" ? undefined : sev);
    if (data && data.threats.length > 0) {
      setThreats(data.threats);
      setUsingDemo(false);
    } else {
      // Fall back to demo data filtered by severity
      const demo = sev === "ALL"
        ? DEMO_THREATS
        : DEMO_THREATS.filter((t) => t.severity === sev);
      setThreats(demo);
      setUsingDemo(true);
    }
    setLoading(false);
  };

  useEffect(() => {
    load(filter);
    const id = setInterval(() => load(filter), 30_000);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter]);

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Alerts</h1>
          <p className="text-sm text-slate-400 mt-0.5">Real-time security threats and behavioural anomalies</p>
        </div>
        <div className="flex items-center gap-2">
          {usingDemo && (
            <span className="bg-amber-50 text-amber-600 text-xs font-medium px-2.5 py-1 rounded-full border border-amber-200">
              Demo data
            </span>
          )}
          <span className="bg-red-50 text-red-600 font-semibold text-sm px-3 py-1 rounded-full">
            {threats.length} active
          </span>
        </div>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-2">
        {filters.map((f) => (
          <button
            key={f.value}
            onClick={() => setFilter(f.value)}
            className={`px-4 py-2 rounded-lg text-sm font-medium border transition-colors ${
              filter === f.value ? f.active : f.style
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      <AlertList threats={threats} loading={loading} />
    </div>
  );
}
