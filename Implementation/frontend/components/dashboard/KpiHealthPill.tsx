"use client";

import type { KpiHealth } from "@/lib/dashboardKpiHealth";
import { KPI_HEALTH_LABEL } from "@/lib/dashboardKpiHealth";

const pill: Record<KpiHealth, string> = {
  normal: "bg-emerald-50 text-emerald-900/90 ring-emerald-200/70",
  watch: "bg-amber-50 text-amber-950/90 ring-amber-200/65",
  critical: "bg-rose-50 text-rose-950 ring-rose-200/75",
};

/** Readable status chip; pair with `kpi-card-critical-ring` on the card when critical. */
export default function KpiHealthPill({ health }: { health: KpiHealth }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em] ring-1 ${pill[health]}`}
    >
      {KPI_HEALTH_LABEL[health]}
    </span>
  );
}
