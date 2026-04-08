"use client";

import { useEffect } from "react";
import Link from "next/link";
import InsightModalViz from "@/components/dashboard/InsightModalViz";
import type { AccessLog, FallEvent, ObjectDetectionEvent, Threat } from "@/lib/api";
import type { DashboardScrollSection, InsightId } from "@/components/dashboard/dashboardCardTypes";

const TITLES: Record<InsightId, string> = {
  traffic: "Door traffic",
  alerts: "Security alerts",
  falls: "Fall detection",
  objects: "Object detection",
};

const JUMP: Record<InsightId, DashboardScrollSection> = {
  traffic: "access",
  alerts: "security",
  falls: "safety",
  objects: "vision",
};

const PAGE_LINKS: Record<InsightId, { href: string; label: string }[]> = {
  traffic: [{ href: "/logs", label: "Access log" }],
  alerts: [{ href: "/alerts", label: "Alerts" }],
  falls: [{ href: "/falls", label: "Fall events" }],
  objects: [{ href: "/objects", label: "Object detection" }],
};

export default function KpiInsightModal({
  insight,
  open,
  onClose,
  logs,
  threats,
  falls,
  objects,
  onJumpToSection,
}: {
  insight: InsightId | null;
  open: boolean;
  onClose: () => void;
  logs: AccessLog[];
  threats: Threat[];
  falls: FallEvent[];
  objects: ObjectDetectionEvent[];
  onJumpToSection: (s: DashboardScrollSection) => void;
}) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open || !insight) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <button
        type="button"
        className="absolute inset-0 bg-slate-900/40 backdrop-blur-[2px]"
        onClick={onClose}
        aria-label="Close"
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="kpi-insight-title"
        className="relative z-[1] w-full max-w-2xl max-h-[min(90vh,880px)] overflow-y-auto rounded-2xl bg-white shadow-xl border border-slate-200/90 p-6"
      >
        <div className="flex items-start justify-between gap-4 mb-4">
          <h2 id="kpi-insight-title" className="text-lg font-semibold text-slate-900">
            {TITLES[insight]}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 text-xl leading-none"
            aria-label="Close dialog"
          >
            ×
          </button>
        </div>

        <InsightModalViz insight={insight} logs={logs} threats={threats} falls={falls} objects={objects} />

        <div className="mt-5 pt-4 border-t border-slate-100 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
          <button
            type="button"
            onClick={() => {
              onJumpToSection(JUMP[insight]);
              onClose();
            }}
            className="text-sm font-semibold text-teal-700 hover:text-teal-800 text-left w-fit"
          >
            Jump to charts below →
          </button>
          <div className="flex flex-col gap-2 sm:items-end">
            <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-400">Open full page</p>
            <div className="flex flex-wrap gap-x-4 gap-y-2">
              {PAGE_LINKS[insight].map((l) => (
                <Link
                  key={l.href}
                  href={l.href}
                  onClick={onClose}
                  className="text-sm font-semibold text-slate-700 hover:text-teal-800 underline-offset-2 hover:underline decoration-teal-200/80"
                >
                  {l.label} →
                </Link>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
