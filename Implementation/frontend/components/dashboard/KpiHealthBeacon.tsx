"use client";

import type { KpiHealth } from "@/lib/dashboardKpiHealth";

/** Color + pulsing “beep” only — no severity words on screen (labels are for assistive tech). */
const ARIA: Record<KpiHealth, string> = {
  normal: "Status OK",
  watch: "Status: elevated attention",
  critical: "Status: highest alert",
};

export default function KpiHealthBeacon({ health }: { health: KpiHealth }) {
  const showPing = health === "critical" || health === "watch";

  return (
    <div
      className="relative flex h-[18px] w-[18px] shrink-0 items-center justify-center"
      role="status"
      aria-label={ARIA[health]}
    >
      {showPing && (
        <span
          className={`absolute h-[13px] w-[13px] rounded-full motion-safe:opacity-95 ${
            health === "critical"
              ? "bg-red-600 motion-safe:animate-kpi-beacon-ping-critical"
              : "bg-amber-500 motion-safe:animate-kpi-beacon-ping-watch"
          }`}
          aria-hidden
        />
      )}
      <span
        className={`relative z-[1] block size-[12px] rounded-full shadow-sm ring-2 ring-white ${
          health === "normal"
            ? "bg-emerald-500 motion-safe:animate-kpi-beacon-soft"
            : health === "watch"
              ? "bg-amber-500"
              : "bg-red-700 ring-red-200"
        }`}
        aria-hidden
      />
    </div>
  );
}
