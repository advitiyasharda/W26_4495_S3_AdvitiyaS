"use client";

import Link from "next/link";
import KpiAnimatedVisual from "@/components/dashboard/KpiAnimatedVisual";
import KpiHealthPill from "@/components/dashboard/KpiHealthPill";
import SparkMicroChart from "@/components/SparkMicroChart";
import type { KpiHealth } from "@/lib/dashboardKpiHealth";

export type StatCardAccent = "teal" | "sky" | "amber" | "rose" | "violet" | "cyan" | "indigo";

const accentTier: Record<StatCardAccent, string> = {
  teal: "bg-gradient-to-b from-teal-400/95 via-teal-500/85 to-cyan-400/75",
  sky: "bg-gradient-to-b from-sky-400/95 via-sky-500/80 to-sky-400/70",
  amber: "bg-gradient-to-b from-amber-400/95 via-orange-400/80 to-amber-400/75",
  rose: "bg-gradient-to-b from-rose-400/95 via-rose-500/85 to-pink-400/70",
  violet: "bg-gradient-to-b from-violet-400/95 via-purple-500/80 to-violet-400/75",
  cyan: "bg-gradient-to-b from-cyan-400/95 via-teal-400/80 to-cyan-400/75",
  indigo: "bg-gradient-to-b from-indigo-400/95 via-indigo-500/80 to-violet-400/75",
};

const iconShell: Record<StatCardAccent, string> = {
  teal: "bg-teal-500/[0.06] text-teal-600/85 ring-1 ring-teal-200/60",
  sky: "bg-sky-500/[0.06] text-sky-600/85 ring-1 ring-sky-200/60",
  amber: "bg-amber-500/[0.07] text-amber-600/85 ring-1 ring-amber-200/60",
  rose: "bg-rose-500/[0.06] text-rose-600/85 ring-1 ring-rose-200/60",
  violet: "bg-violet-500/[0.06] text-violet-600/85 ring-1 ring-violet-200/60",
  cyan: "bg-cyan-500/[0.06] text-cyan-600/85 ring-1 ring-cyan-200/60",
  indigo: "bg-indigo-500/[0.06] text-indigo-600/85 ring-1 ring-indigo-200/60",
};

const liveBarColors: Record<StatCardAccent, [string, string, string]> = {
  teal: ["bg-teal-200/50", "bg-teal-300/45", "bg-teal-200/40"],
  sky: ["bg-sky-200/50", "bg-sky-300/45", "bg-sky-200/40"],
  amber: ["bg-amber-200/50", "bg-amber-300/45", "bg-amber-200/40"],
  rose: ["bg-rose-200/50", "bg-rose-300/45", "bg-rose-200/40"],
  violet: ["bg-violet-200/50", "bg-violet-300/45", "bg-violet-200/40"],
  cyan: ["bg-cyan-200/50", "bg-cyan-300/45", "bg-cyan-200/40"],
  indigo: ["bg-indigo-200/50", "bg-indigo-300/45", "bg-indigo-200/40"],
};

interface Props {
  title: string;
  value: React.ReactNode;
  sub?: React.ReactNode;
  icon?: React.ReactNode;
  trend?: { value: number; label?: string };
  href?: string;
  onClick?: () => void;
  selected?: boolean;
  className?: string;
  accent?: StatCardAccent;
  /** Animated icon strip (replaces sparkline when set) */
  visualKind?: "alerts" | "falls" | "objects";
  spark?: number[];
  sparkColor?: string;
  cardViz?: React.ReactNode;
  liveBars?: boolean;
  health?: KpiHealth;
}

function LiveBarsStrip({ accent }: { accent: StatCardAccent }) {
  const [a, b, c] = liveBarColors[accent];
  return (
    <div className="flex h-4 w-full items-end gap-0.5 animate-live-bars opacity-80" aria-hidden>
      <span className={`flex-1 rounded-sm h-2.5 ${a}`} />
      <span className={`flex-1 rounded-sm h-4 ${b}`} />
      <span className={`flex-1 rounded-sm h-2 ${c}`} />
    </div>
  );
}

function statusRingClass(health: KpiHealth | undefined): string {
  if (health === "critical") return "kpi-card-critical-ring";
  if (health === "watch") return "kpi-card-watch-ring";
  return "";
}

export default function StatCard({
  title,
  value,
  sub,
  icon,
  trend,
  href,
  onClick,
  selected,
  className = "",
  accent = "teal",
  visualKind,
  spark,
  sparkColor,
  cardViz,
  liveBars,
  health,
}: Props) {
  const up = trend && trend.value >= 0;

  const healthSafe = health ?? "normal";

  const footer =
    visualKind ? (
      <KpiAnimatedVisual kind={visualKind} health={healthSafe} />
    ) : liveBars && accent ? (
      <LiveBarsStrip accent={accent} />
    ) : cardViz ? (
      cardViz
    ) : spark && spark.length > 0 && sparkColor ? (
      <SparkMicroChart values={spark} color={sparkColor} />
    ) : null;

  const surface =
    `kpi-card-surface stat-card-motion group relative z-0 ring-1 ring-white/60 flex flex-row overflow-hidden p-0 ` +
    statusRingClass(healthSafe) +
    (selected ? " ring-teal-200/40 bg-white" : "");

  const base = `${surface} ${className}`;
  const stretch = "flex h-full min-h-0 w-full flex-row items-stretch text-left";

  const body = (
    <>
      <div className={`w-1.5 shrink-0 self-stretch rounded-l-[1rem] ${accentTier[accent]}`} aria-hidden />
      <div className="flex min-h-[12rem] min-w-0 flex-1 flex-col justify-between gap-4 p-5">
        <div className="space-y-3">
          <div className="flex items-start justify-between gap-2">
            <p className="text-[11px] font-medium uppercase tracking-[0.14em] text-slate-500">{title}</p>
            <div className="flex flex-wrap items-center justify-end gap-2">
              {health != null ? <KpiHealthPill health={health} /> : null}
              {icon ? (
                <div
                  className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-xl transition-transform duration-300 group-hover:scale-105 ${iconShell[accent]}`}
                >
                  {icon}
                </div>
              ) : null}
            </div>
          </div>

          <div className="flex items-end gap-2">
            <span className="text-[1.65rem] font-semibold leading-none tracking-tight text-slate-800 tabular-nums">
              {value}
            </span>
            {trend && (
              <span
                className={`mb-0.5 flex items-center gap-0.5 text-[11px] font-medium ${
                  up ? "text-teal-600/80" : "text-rose-400/85"
                }`}
              >
                {up ? (
                  <svg className="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}>
                    <polyline points="18 15 12 9 6 15" />
                  </svg>
                ) : (
                  <svg className="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}>
                    <polyline points="6 9 12 15 18 9" />
                  </svg>
                )}
                {Math.abs(trend.value)}%
              </span>
            )}
          </div>
        </div>

        {(footer || sub) && (
          <div className="space-y-0">
            {footer ? (
              visualKind ? (
                <div className="rounded-xl border border-slate-100/90 bg-gradient-to-br from-slate-50/90 to-white/70 px-3 py-3 shadow-[0_1px_0_rgb(255_255_255_/_0.9)_inset]">
                  <p className="mb-2 text-[9px] font-semibold uppercase tracking-[0.16em] text-slate-400">Live signal</p>
                  {footer}
                </div>
              ) : (
                <div className="flex min-h-[1rem] items-center opacity-90">{footer}</div>
              )
            ) : null}
            {sub ? (
              <div
                className={`text-[11px] leading-snug text-slate-600 ${
                  footer ? "mt-2 border-t border-slate-100/85 pt-2.5" : "border-t border-slate-100/85 pt-2.5"
                }`}
              >
                {sub}
              </div>
            ) : null}
          </div>
        )}
      </div>
    </>
  );

  if (href) {
    return (
      <Link href={href} className={`${base} ${stretch} text-inherit no-underline`}>
        {body}
      </Link>
    );
  }

  if (onClick) {
    return (
      <button type="button" onClick={onClick} className={`${base} ${stretch}`}>
        {body}
      </button>
    );
  }

  return <div className={`${base} ${stretch}`}>{body}</div>;
}
