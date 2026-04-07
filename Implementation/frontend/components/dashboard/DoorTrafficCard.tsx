"use client";

import SparkMicroChart from "@/components/SparkMicroChart";
import type { KpiHealth } from "@/lib/dashboardKpiHealth";
import { KPI_HEALTH_LABEL } from "@/lib/dashboardKpiHealth";
import { statSpark } from "@/lib/theme";
import { IconDoorPanel } from "@/components/icons/DoorIcons";

const healthDot: Record<KpiHealth, string> = {
  normal: "bg-teal-400/70 shadow-[0_0_0_3px_rgba(45,212,191,0.12)]",
  watch: "bg-amber-400/75 shadow-[0_0_0_3px_rgba(251,191,36,0.12)]",
  critical: "bg-red-600 ring-1 ring-red-200 shadow-[0_0_0_4px_rgba(239,68,68,0.26)]",
};

export default function DoorTrafficCard({
  entries,
  exits,
  health,
  sparkIn,
  sparkOut,
  rangeLabel,
  peakIn,
  peakOut,
  matchInPct,
  matchOutPct,
  onClick,
  className = "",
}: {
  entries: number;
  exits: number;
  health: KpiHealth;
  sparkIn: number[];
  sparkOut: number[];
  rangeLabel: string;
  peakIn: string | null;
  peakOut: string | null;
  matchInPct: number | null;
  matchOutPct: number | null;
  onClick: () => void;
  className?: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`group kpi-card-surface stat-card-motion w-full text-left p-5 flex flex-col gap-4 ring-1 ring-white/60 ${className}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0 bg-gradient-to-br from-teal-100/90 to-sky-50/70 text-teal-700 ring-1 ring-teal-200/80 shadow-sm transition-transform duration-300 group-hover:scale-105">
            <IconDoorPanel className="w-5 h-5" />
          </div>
          <div>
            <p className="text-[11px] font-medium text-slate-400 tracking-wide">Door traffic</p>
            <p className="text-xs text-slate-400/90 mt-0.5">{rangeLabel}</p>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className={`size-2.5 rounded-full shrink-0 ${healthDot[health]}`} aria-hidden />
          <span className="text-[10px] font-medium text-slate-400 tabular-nums">{KPI_HEALTH_LABEL[health]}</span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <p className="text-[10px] font-medium uppercase tracking-wider text-slate-400">In</p>
          <p className="text-3xl font-semibold text-slate-800 tabular-nums leading-none tracking-tight">{entries}</p>
          <SparkMicroChart values={sparkIn} color={statSpark.entry.stroke} />
        </div>
        <div className="space-y-2 border-l border-slate-100/90 pl-4">
          <p className="text-[10px] font-medium uppercase tracking-wider text-slate-400">Out</p>
          <p className="text-3xl font-semibold text-slate-800 tabular-nums leading-none tracking-tight">{exits}</p>
          <SparkMicroChart values={sparkOut} color={statSpark.exit.stroke} />
        </div>
      </div>

      <p className="text-[11px] text-slate-400 leading-relaxed pt-1 border-t border-slate-100/80">
        {peakIn || peakOut ? (
          <>
            {peakIn && <span>Peak in {peakIn}</span>}
            {peakIn && peakOut ? " · " : null}
            {peakOut && <span>Peak out {peakOut}</span>}
            {(matchInPct != null || matchOutPct != null) && " · "}
          </>
        ) : null}
        {matchInPct != null && <span>Match in {matchInPct}%</span>}
        {matchInPct != null && matchOutPct != null ? " · " : null}
        {matchOutPct != null && <span>out {matchOutPct}%</span>}
        <span className="text-slate-300"> · Tap for detail</span>
      </p>
    </button>
  );
}
