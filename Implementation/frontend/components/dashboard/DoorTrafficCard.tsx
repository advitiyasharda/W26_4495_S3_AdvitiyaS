"use client";

import KpiAnimatedVisual from "@/components/dashboard/KpiAnimatedVisual";
import KpiHealthPill from "@/components/dashboard/KpiHealthPill";
import type { KpiHealth } from "@/lib/dashboardKpiHealth";
import { IconDoorPanel } from "@/components/icons/DoorIcons";

const doorTier = "bg-gradient-to-b from-teal-400/95 via-cyan-500/80 to-sky-400/75";

function statusRingClass(health: KpiHealth): string {
  if (health === "critical") return "kpi-card-critical-ring";
  if (health === "watch") return "kpi-card-watch-ring";
  return "";
}

export default function DoorTrafficCard({
  entries,
  exits,
  health,
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
      className={`group kpi-card-surface stat-card-motion relative z-0 flex h-full min-h-0 w-full flex-row items-stretch overflow-hidden text-left ring-1 ring-white/60 ${statusRingClass(
        health
      )} ${className}`}
    >
      <div className={`w-1.5 shrink-0 self-stretch rounded-l-[1rem] ${doorTier}`} aria-hidden />

      <div className="flex min-h-[12rem] min-w-0 flex-1 flex-col justify-between gap-4 p-5">
        <div className="space-y-4">
          <div className="flex items-start justify-between gap-3">
            <div className="flex min-w-0 items-start gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-teal-100/90 to-sky-50/70 text-teal-700 shadow-sm ring-1 ring-teal-200/80 transition-transform duration-300 group-hover:scale-105">
                <IconDoorPanel className="h-5 w-5" />
              </div>
              <div className="min-w-0">
                <p className="text-[11px] font-medium uppercase tracking-[0.14em] text-slate-500">Door traffic</p>
                <p className="mt-0.5 text-xs text-slate-500">{rangeLabel}</p>
              </div>
            </div>
            <KpiHealthPill health={health} />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-[10px] font-medium uppercase tracking-wider text-slate-500">In</p>
              <p className="mt-1 text-3xl font-semibold leading-none tracking-tight text-slate-800 tabular-nums">
                {entries}
              </p>
            </div>
            <div className="border-l border-slate-100/90 pl-4">
              <p className="text-[10px] font-medium uppercase tracking-wider text-slate-500">Out</p>
              <p className="mt-1 text-3xl font-semibold leading-none tracking-tight text-slate-800 tabular-nums">
                {exits}
              </p>
            </div>
          </div>
        </div>

        <div className="space-y-0">
          <div className="rounded-xl border border-slate-100/90 bg-gradient-to-br from-slate-50/90 to-white/70 px-3 py-3 shadow-[0_1px_0_rgb(255_255_255_/_0.9)_inset]">
            <p className="mb-3 text-[9px] font-semibold uppercase tracking-[0.16em] text-slate-400">Live signal</p>
            <div className="grid grid-cols-2 gap-3">
              <KpiAnimatedVisual kind="traffic-in" health={health} />
              <div className="border-l border-slate-200/70 pl-3">
                <KpiAnimatedVisual kind="traffic-out" health={health} />
              </div>
            </div>
          </div>

          <p className="mt-2 border-t border-slate-100/85 pt-2.5 text-[11px] leading-relaxed text-slate-600">
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
            <span className="text-slate-400"> · Tap for detail</span>
          </p>
        </div>
      </div>
    </button>
  );
}
