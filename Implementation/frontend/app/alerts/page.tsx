"use client";

import { useEffect, useMemo, useState } from "react";
import { getThreats, Threat } from "@/lib/api";
import { DEMO_THREATS, demoFallbackEnabled, emptyOrDemo } from "@/lib/demoData";
import AlertList from "@/components/AlertList";
import PageHero from "@/components/PageHero";
import AlertSeveritySummary from "@/components/alerts/AlertSeveritySummary";
import { IconShieldAlert } from "@/components/icons/DoorIcons";

type Filter = "ALL" | "HIGH" | "CRITICAL";

const filters: { label: string; value: Filter; style: string; active: string }[] = [
  {
    label: "All",
    value: "ALL",
    style: "bg-white/90 border border-slate-200/80 text-slate-600 hover:bg-slate-50",
    active: "bg-slate-800 border-slate-800 text-white shadow-sm",
  },
  {
    label: "High",
    value: "HIGH",
    style: "bg-amber-50/80 border border-amber-200/80 text-amber-900 hover:bg-amber-100/80",
    active: "bg-amber-500 border-amber-500 text-amber-950 shadow-sm",
  },
  {
    label: "Critical",
    value: "CRITICAL",
    style: "bg-rose-50/80 border border-rose-200/80 text-rose-900 hover:bg-rose-100/80",
    active: "bg-rose-500 border-rose-500 text-white shadow-sm",
  },
];

export default function AlertsPage() {
  const [threats, setThreats] = useState<Threat[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<Filter>("ALL");
  const [usingDemo, setUsingDemo] = useState(false);

  const load = async (sev: Filter) => {
    setLoading(true);
    const data = await getThreats(sev === "ALL" ? undefined : sev);
    const merged = emptyOrDemo(data?.threats, DEMO_THREATS);
    setUsingDemo((data?.threats?.length ?? 0) === 0 && demoFallbackEnabled());
    const filtered = sev === "ALL" ? merged : merged.filter((t) => t.severity === sev);
    setThreats(filtered);
    setLoading(false);
  };

  useEffect(() => {
    load(filter);
    const id = setInterval(() => load(filter), 30_000);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter]);

  const badge = useMemo(() => {
    const n = threats.length;
    if (n === 0) return "Clear";
    if (n === 1) return "1 alert";
    return `${n} alerts`;
  }, [threats.length]);

  return (
    <div className="space-y-6">
      <PageHero
        tone="amber"
        eyebrow="Smart door · Security layer"
        title="Alerts & anomalies"
        icon={<IconShieldAlert className="w-6 h-6" />}
        description={
          <>
            Signals from the same camera that powers face access — failed matches, policy breaches, and behavioural flags
            before someone fully crosses the threshold.
          </>
        }
        aside={
          <div className="flex flex-wrap gap-2 justify-end">
            {usingDemo && (
              <span className="text-xs font-semibold px-2.5 py-1 rounded-full border border-amber-200 bg-amber-50/95 text-amber-900">
                Sample data
              </span>
            )}
            <span
              className={`text-sm font-semibold px-3 py-1.5 rounded-full border ${
                threats.length === 0
                  ? "bg-emerald-50/90 text-emerald-900 border-emerald-200/80"
                  : "bg-rose-50/90 text-rose-900 border-rose-200/80"
              }`}
            >
              {badge}
            </span>
          </div>
        }
      />

      <div className="flex flex-col lg:flex-row gap-4 lg:items-start">
        <div className="flex-1 min-w-0 space-y-4">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Severity filter</p>
            <div className="flex gap-2 flex-wrap">
              {filters.map((f) => (
                <button
                  key={f.value}
                  type="button"
                  onClick={() => setFilter(f.value)}
                  className={`px-4 py-2 rounded-xl text-sm font-medium border transition-all ${
                    filter === f.value ? f.active : f.style
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>
          <AlertList threats={threats} loading={loading} />
        </div>
        <div className="w-full lg:w-[300px] shrink-0">
          <AlertSeveritySummary threats={threats} />
        </div>
      </div>
    </div>
  );
}
