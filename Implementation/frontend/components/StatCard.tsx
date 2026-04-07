"use client";

import Link from "next/link";
import SparkMicroChart from "@/components/SparkMicroChart";
import type { KpiHealth } from "@/lib/dashboardKpiHealth";
import { KPI_HEALTH_LABEL } from "@/lib/dashboardKpiHealth";

export type StatCardAccent = "teal" | "sky" | "amber" | "rose" | "violet" | "cyan" | "indigo";

const healthDot: Record<KpiHealth, string> = {
  normal: "bg-teal-400/70 shadow-[0_0_0_3px_rgba(45,212,191,0.12)]",
  watch: "bg-amber-400/75 shadow-[0_0_0_3px_rgba(251,191,36,0.12)]",
  critical: "bg-red-600 ring-1 ring-red-200 shadow-[0_0_0_4px_rgba(239,68,68,0.26)]",
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
  spark,
  sparkColor,
  cardViz,
  liveBars,
  health,
}: Props) {
  const up = trend && trend.value >= 0;

  const surface =
    `kpi-card-surface stat-card-motion group ring-1 ring-white/60 p-5 flex flex-col gap-3 ` +
    (selected ? "ring-teal-200/40 bg-white" : "");

  const base = `${surface} ${className}`;

  const footer =
    liveBars && accent ? (
      <LiveBarsStrip accent={accent} />
    ) : cardViz ? (
      cardViz
    ) : spark && spark.length > 0 && sparkColor ? (
      <SparkMicroChart values={spark} color={sparkColor} />
    ) : null;

  const inner = (
    <>
      <div className="flex items-start justify-between gap-2">
        <p className="text-[11px] font-medium text-slate-400 tracking-wide">{title}</p>
        <div className="flex items-center gap-2 shrink-0">
          {health && (
            <>
              <span className={`size-2.5 rounded-full shrink-0 ${healthDot[health]}`} aria-hidden />
              <span className="text-[10px] font-medium text-slate-400">{KPI_HEALTH_LABEL[health]}</span>
            </>
          )}
          {icon && (
            <div
              className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 transition-transform duration-300 group-hover:scale-105 ${iconShell[accent]}`}
            >
              {icon}
            </div>
          )}
        </div>
      </div>

      <div className="flex items-end gap-2">
        <span className="text-2xl font-semibold tracking-tight text-slate-800 tabular-nums leading-none">{value}</span>
        {trend && (
          <span
            className={`flex items-center gap-0.5 text-[11px] font-medium mb-0.5 ${
              up ? "text-teal-600/80" : "text-rose-400/85"
            }`}
          >
            {up ? (
              <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}>
                <polyline points="18 15 12 9 6 15" />
              </svg>
            ) : (
              <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}>
                <polyline points="6 9 12 15 18 9" />
              </svg>
            )}
            {Math.abs(trend.value)}%
          </span>
        )}
      </div>

      {footer && <div className="min-h-[16px] flex items-center opacity-90">{footer}</div>}

      {sub && <div className="text-[11px] text-slate-400 leading-snug border-t border-slate-100/80 pt-2.5">{sub}</div>}
    </>
  );

  if (href) {
    return (
      <Link href={href} className={`${base} w-full text-left text-inherit no-underline block`}>
        {inner}
      </Link>
    );
  }

  if (onClick) {
    return (
      <button type="button" onClick={onClick} className={`${base} w-full text-left`}>
        {inner}
      </button>
    );
  }

  return <div className={base}>{inner}</div>;
}
