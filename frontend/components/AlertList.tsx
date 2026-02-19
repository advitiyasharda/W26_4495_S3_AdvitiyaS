"use client";

import { Threat } from "@/lib/api";

function fmt(iso: string) {
  return new Date(iso).toLocaleString("en-US", {
    month: "short", day: "2-digit", hour: "2-digit", minute: "2-digit",
  });
}

const severityStyles: Record<string, { dot: string; badge: string; border: string }> = {
  CRITICAL: { dot: "bg-red-500",    badge: "bg-red-50 text-red-600",     border: "border-red-200" },
  HIGH:     { dot: "bg-orange-400", badge: "bg-orange-50 text-orange-600", border: "border-orange-200" },
  MEDIUM:   { dot: "bg-amber-400",  badge: "bg-amber-50 text-amber-600",  border: "border-amber-200" },
  LOW:      { dot: "bg-slate-300",  badge: "bg-slate-50 text-slate-500",  border: "border-slate-200" },
};

interface Props { threats: Threat[]; loading?: boolean }

export default function AlertList({ threats, loading }: Props) {
  if (loading)
    return <p className="text-center text-slate-400 py-10">Loading alerts…</p>;

  if (threats.length === 0)
    return (
      <div className="flex flex-col items-center justify-center py-16 text-slate-400 gap-2">
        <svg className="w-10 h-10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}>
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
        </svg>
        <p className="text-sm font-medium">No active threats</p>
      </div>
    );

  return (
    <div className="space-y-3">
      {threats.map((t, i) => {
        const s = severityStyles[t.severity] ?? severityStyles.LOW;
        return (
          <div key={i} className={`bg-white rounded-xl border ${s.border} p-4 flex items-start justify-between gap-4 shadow-sm`}>
            <div className="flex items-start gap-3">
              <span className={`mt-1.5 w-2 h-2 rounded-full flex-shrink-0 ${s.dot}`} />
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <h4 className="font-semibold text-sm text-slate-800">{t.threat_type}</h4>
                  <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${s.badge}`}>{t.severity}</span>
                </div>
                <p className="text-xs text-slate-500">{t.message}</p>
              </div>
            </div>
            <span className="text-xs text-slate-400 whitespace-nowrap flex-shrink-0">{fmt(t.timestamp)}</span>
          </div>
        );
      })}
    </div>
  );
}
