"use client";

import SparkMicroChart from "@/components/SparkMicroChart";
import type { KpiHealth } from "@/lib/dashboardKpiHealth";
import KpiHealthBeacon from "@/components/dashboard/KpiHealthBeacon";
import { IconCameraDoor } from "@/components/icons/DoorIcons";

function PipelineChip({ label, active }: { label: string; active: boolean }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-lg border px-2 py-0.5 text-[10px] font-semibold tracking-wide transition-colors ${
        active
          ? "border-teal-200/90 bg-teal-50/80 text-teal-900"
          : "border-slate-200/90 bg-slate-50/60 text-slate-400"
      }`}
    >
      <span
        className={`size-1.5 rounded-full ${active ? "bg-teal-500 shadow-[0_0_0_2px_rgba(20,184,166,0.2)]" : "bg-slate-300"}`}
        aria-hidden
      />
      {label}
    </span>
  );
}

function SignalStrip({ accent }: { accent: "cyan" }) {
  const bars =
    accent === "cyan"
      ? ["bg-cyan-200/70", "bg-cyan-300/80", "bg-cyan-400/75"]
      : ["bg-cyan-200/70", "bg-cyan-300/80", "bg-cyan-400/75"];
  return (
    <div className="flex h-3.5 w-full items-end gap-0.5 animate-live-bars opacity-95" aria-hidden>
      <span className={`flex-1 rounded-sm h-2 ${bars[0]}`} />
      <span className={`flex-1 rounded-sm h-3 ${bars[1]}`} />
      <span className={`flex-1 rounded-sm h-2.5 ${bars[2]}`} />
    </div>
  );
}

const IDLE_SPARK = Array.from({ length: 14 }, () => 0);

export default function CameraPipelineCard({
  health,
  fallReady,
  objectReady,
  weaponReady,
  dataLinkOk,
  onClick,
  className = "",
}: {
  health: KpiHealth;
  fallReady: boolean;
  objectReady: boolean;
  weaponReady: boolean;
  dataLinkOk: boolean;
  onClick: () => void;
  className?: string;
}) {
  const pipelinesUp = [fallReady, objectReady, weaponReady].filter(Boolean).length;
  const allCore = fallReady && objectReady && weaponReady && dataLinkOk;

  let headline = "Attention required";
  let headlineClass = "text-rose-700/95";
  if (allCore) {
    headline = "Operational";
    headlineClass = "text-slate-900";
  } else if (pipelinesUp >= 2 || (pipelinesUp >= 1 && dataLinkOk)) {
    headline = "Partial availability";
    headlineClass = "text-amber-900/90";
  } else if (pipelinesUp === 1) {
    headline = "Limited coverage";
    headlineClass = "text-amber-900/85";
  }

  return (
    <button
      type="button"
      onClick={onClick}
      className={`group kpi-card-surface stat-card-motion w-full text-left p-5 flex flex-col gap-3 ring-1 ring-white/60 ${className}`}
    >
      <div className="relative z-[1] flex flex-col gap-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex gap-3 min-w-0">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-50 to-sky-50 text-cyan-700 ring-1 ring-cyan-100/80 shadow-sm transition-transform duration-500 ease-[cubic-bezier(0.22,1,0.36,1)] group-hover:scale-105 motion-reduce:transition-none motion-reduce:group-hover:scale-100">
              <IconCameraDoor className="w-5 h-5" />
            </div>
            <div className="min-w-0 pt-0.5">
              <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-400">Unified camera</p>
              <p className="text-[11px] text-slate-500 mt-0.5 leading-snug">Entrance stream · ML pipelines</p>
            </div>
          </div>
          <KpiHealthBeacon health={health} />
        </div>

        <div className="transition-transform duration-300 ease-out group-hover:-translate-y-0.5 motion-reduce:transition-none motion-reduce:group-hover:translate-y-0">
          <p className={`text-xl font-semibold tracking-tight tabular-nums leading-tight ${headlineClass}`}>{headline}</p>
          <p className="text-[11px] text-slate-500 mt-1.5 leading-relaxed">
            Fall, object, and weapon heads on one feed. Open for a readiness radar.
          </p>
        </div>

        <div className="flex flex-wrap gap-1.5">
          <PipelineChip label="Fall" active={fallReady} />
          <PipelineChip label="Object" active={objectReady} />
          <PipelineChip label="Weapon" active={weaponReady} />
        </div>

        <div className="pt-1 border-t border-slate-100/85">
          {allCore ? (
            <SignalStrip accent="cyan" />
          ) : (
            <SparkMicroChart values={IDLE_SPARK} color="#94a3b8" />
          )}
        </div>
      </div>
    </button>
  );
}
