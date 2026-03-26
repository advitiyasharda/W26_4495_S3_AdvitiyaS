"use client";

import type { KpiHealth } from "@/lib/dashboardKpiHealth";
import KpiHealthPill from "@/components/dashboard/KpiHealthPill";
import { IconFallMotion, IconSearchObject } from "@/components/icons/DoorIcons";

const tier = "bg-gradient-to-b from-slate-400/90 via-slate-500/75 to-slate-400/60";

function statusRingClass(health: KpiHealth): string {
  if (health === "critical") return "kpi-card-critical-ring";
  if (health === "watch") return "kpi-card-watch-ring";
  return "";
}

function StatusPill({ ok, label }: { ok: boolean; label: string }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-xl border border-slate-100/90 bg-white/70 px-3 py-2">
      <span className="text-[11px] font-semibold text-slate-700">{label}</span>
      <span
        className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${
          ok ? "bg-emerald-50 text-emerald-700 border border-emerald-200/70" : "bg-rose-50 text-rose-700 border border-rose-200/70"
        }`}
      >
        {ok ? "Ready" : "Off"}
      </span>
    </div>
  );
}

export default function CameraPipelineCard({
  fallReady,
  objectReady,
  linkOk,
  health,
  rangeLabel,
  onClick,
  className = "",
}: {
  fallReady: boolean;
  objectReady: boolean;
  linkOk: boolean;
  health: KpiHealth;
  rangeLabel: string;
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
      <div className={`w-1.5 shrink-0 self-stretch rounded-l-[1rem] ${tier}`} aria-hidden />

      <div className="flex min-h-[12rem] min-w-0 flex-1 flex-col justify-between gap-4 p-5">
        <div className="space-y-4">
          <div className="flex items-start justify-between gap-3">
            <div className="flex min-w-0 items-start gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-slate-100/90 to-white/70 text-slate-700 shadow-sm ring-1 ring-slate-200/80 transition-transform duration-300 group-hover:scale-105">
                <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8}>
                  <path d="M23 7l-7 5 7 5V7z" />
                  <rect x="1" y="5" width="15" height="14" rx="2" ry="2" />
                </svg>
              </div>
              <div className="min-w-0">
                <p className="text-[11px] font-medium uppercase tracking-[0.14em] text-slate-500">Pipelines</p>
                <p className="mt-0.5 text-xs text-slate-500">{rangeLabel}</p>
              </div>
            </div>
            <KpiHealthPill health={health} />
          </div>

          <div className="grid grid-cols-1 gap-2">
            <div className="flex items-center justify-between gap-3 rounded-xl border border-slate-100/90 bg-gradient-to-br from-slate-50/90 to-white/70 px-3 py-2 shadow-[0_1px_0_rgb(255_255_255_/_0.9)_inset]">
              <div className="flex items-center gap-2 min-w-0">
                <span className="text-slate-500">{IconFallMotion ? <IconFallMotion className="h-4 w-4" /> : null}</span>
                <span className="text-[11px] font-semibold text-slate-700 truncate">Fall detector</span>
              </div>
              <span
                className={`shrink-0 text-[11px] font-semibold px-2 py-0.5 rounded-full border ${
                  fallReady ? "bg-emerald-50 text-emerald-700 border-emerald-200/70" : "bg-rose-50 text-rose-700 border-rose-200/70"
                }`}
              >
                {fallReady ? "Ready" : "Off"}
              </span>
            </div>

            <div className="flex items-center justify-between gap-3 rounded-xl border border-slate-100/90 bg-gradient-to-br from-slate-50/90 to-white/70 px-3 py-2 shadow-[0_1px_0_rgb(255_255_255_/_0.9)_inset]">
              <div className="flex items-center gap-2 min-w-0">
                <span className="text-slate-500">{IconSearchObject ? <IconSearchObject className="h-4 w-4" /> : null}</span>
                <span className="text-[11px] font-semibold text-slate-700 truncate">Object detector</span>
              </div>
              <span
                className={`shrink-0 text-[11px] font-semibold px-2 py-0.5 rounded-full border ${
                  objectReady ? "bg-emerald-50 text-emerald-700 border-emerald-200/70" : "bg-rose-50 text-rose-700 border-rose-200/70"
                }`}
              >
                {objectReady ? "Ready" : "Off"}
              </span>
            </div>

            <div className="flex items-center justify-between gap-3 rounded-xl border border-slate-100/90 bg-white/70 px-3 py-2">
              <span className="text-[11px] font-semibold text-slate-700">Data link</span>
              <span
                className={`text-[11px] font-semibold px-2 py-0.5 rounded-full border ${
                  linkOk ? "bg-sky-50 text-sky-800 border-sky-200/70" : "bg-amber-50 text-amber-800 border-amber-200/70"
                }`}
              >
                {linkOk ? "Active" : "Limited"}
              </span>
            </div>
          </div>
        </div>

        <p className="border-t border-slate-100/85 pt-2.5 text-[11px] leading-relaxed text-slate-600">
          Detector readiness summary for this window. <span className="text-slate-400">· Tap for detail</span>
        </p>
      </div>
    </button>
  );
}
