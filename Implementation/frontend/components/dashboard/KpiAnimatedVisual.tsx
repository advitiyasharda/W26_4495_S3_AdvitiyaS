"use client";

import type { CSSProperties } from "react";
import type { KpiHealth } from "@/lib/dashboardKpiHealth";
import {
  IconBell,
  IconEntry,
  IconExit,
  IconFallMotion,
  IconObjectFrame,
} from "@/components/icons/DoorIcons";

function motionDuration(health: KpiHealth | undefined): string {
  if (health === "critical") return "0.88s";
  if (health === "watch") return "1.45s";
  return "2.75s";
}

/** Decorative animated icons for KPI cards — replaces sparklines. */
export default function KpiAnimatedVisual({
  kind,
  health,
}: {
  kind: "traffic-in" | "traffic-out" | "alerts" | "falls" | "objects";
  health?: KpiHealth;
}) {
  const h = health;
  const style = { "--kpi-dur": motionDuration(h) } as CSSProperties;

  const label =
    kind === "traffic-in"
      ? "Inbound flow"
      : kind === "traffic-out"
        ? "Outbound flow"
        : kind === "alerts"
          ? "Alert watch"
          : kind === "falls"
            ? "Safety signal"
            : "Detection pulse";

  const motionClass =
    kind === "traffic-in"
      ? "kpi-motion-flow-in"
      : kind === "traffic-out"
        ? "kpi-motion-flow-out"
        : kind === "alerts"
          ? "kpi-motion-bell"
          : kind === "falls"
            ? "kpi-motion-fall"
            : "kpi-motion-object";

  const colorClass =
    kind === "traffic-in"
      ? "text-teal-600"
      : kind === "traffic-out"
        ? "text-sky-600"
        : kind === "alerts"
          ? "text-amber-600"
          : kind === "falls"
            ? "text-rose-600"
            : "text-violet-600";

  const Icon =
    kind === "traffic-in"
      ? IconEntry
      : kind === "traffic-out"
        ? IconExit
        : kind === "alerts"
          ? IconBell
          : kind === "falls"
            ? IconFallMotion
            : IconObjectFrame;

  return (
    <div
      className="flex min-h-[3.5rem] flex-col items-center justify-center gap-2"
      style={style}
    >
      <Icon
        className={`h-9 w-9 ${motionClass} ${colorClass} drop-shadow-sm motion-reduce:animate-none motion-reduce:[transform:none]`}
        aria-hidden
      />
      <span className="max-w-[10rem] text-center text-[10px] font-medium leading-snug text-slate-600">
        {label}
      </span>
    </div>
  );
}
