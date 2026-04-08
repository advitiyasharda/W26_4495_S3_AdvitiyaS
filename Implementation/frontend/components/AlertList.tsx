"use client";

import type { Threat } from "@/lib/api";
import { IconCalmCheck, IconFaceScan, IconShieldAlert } from "@/components/icons/DoorIcons";

function fmt(iso: string) {
  return new Date(iso).toLocaleString("en-US", {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

const severityStyles: Record<string, { dot: string; badge: string; border: string; iconBg: string }> = {
  CRITICAL: {
    dot: "bg-rose-400",
    badge: "bg-rose-50 text-rose-800 ring-1 ring-rose-200/70",
    border: "border-rose-200/60",
    iconBg: "bg-rose-50 text-rose-600",
  },
  HIGH: {
    dot: "bg-amber-400",
    badge: "bg-amber-50 text-amber-900 ring-1 ring-amber-200/70",
    border: "border-amber-200/60",
    iconBg: "bg-amber-50 text-amber-700",
  },
  MEDIUM: {
    dot: "bg-sky-400",
    badge: "bg-sky-50 text-sky-900 ring-1 ring-sky-200/70",
    border: "border-sky-200/55",
    iconBg: "bg-sky-50 text-sky-700",
  },
  LOW: {
    dot: "bg-slate-300",
    badge: "bg-slate-50 text-slate-600 ring-1 ring-slate-200/80",
    border: "border-slate-200/70",
    iconBg: "bg-slate-50 text-slate-600",
  },
};

function ThreatGlyph({ type }: { type: string }) {
  const t = type.toLowerCase();
  const wrap = "h-10 w-10 rounded-xl flex items-center justify-center shrink-0 ring-1 ring-black/[0.04]";
  if (t.includes("weapon") || t.includes("intrusion") || t.includes("forced")) {
    return (
      <div className={`${wrap} bg-rose-50 text-rose-600`}>
        <IconShieldAlert className="w-5 h-5" />
      </div>
    );
  }
  if (t.includes("face") || t.includes("spoof") || t.includes("unknown") || t.includes("identity")) {
    return (
      <div className={`${wrap} bg-violet-50 text-violet-600`}>
        <IconFaceScan className="w-5 h-5" />
      </div>
    );
  }
  return (
    <div className={`${wrap} bg-amber-50 text-amber-700`}>
      <IconShieldAlert className="w-5 h-5" />
    </div>
  );
}

interface Props {
  threats: Threat[];
  loading?: boolean;
}

export default function AlertList({ threats, loading }: Props) {
  if (loading) {
    return (
      <div className="rounded-2xl border border-slate-100 bg-white/80 py-16 text-center text-slate-400 text-sm">
        Syncing alerts from the door panel…
      </div>
    );
  }

  if (threats.length === 0) {
    return (
      <div className="rounded-2xl border border-emerald-100/80 bg-gradient-to-b from-emerald-50/40 to-white px-6 py-14 text-center">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-100/60 text-emerald-600 mb-3">
          <IconCalmCheck className="w-9 h-9" />
        </div>
        <p className="text-sm font-semibold text-slate-800">Entrance is calm</p>
        <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto leading-relaxed">
          No active threats from the unified camera. Alerts appear here when the door stack flags risk at the threshold.
        </p>
      </div>
    );
  }

  return (
    <ul className="space-y-3">
      {threats.map((t, i) => {
        const s = severityStyles[t.severity] ?? severityStyles.LOW;
        return (
          <li
            key={`${t.timestamp}-${i}`}
            className={`rounded-2xl border bg-white/90 backdrop-blur-sm p-4 shadow-sm flex flex-col sm:flex-row sm:items-start gap-4 ${s.border}`}
          >
            <ThreatGlyph type={t.threat_type} />
            <div className="flex-1 min-w-0">
              <div className="flex flex-wrap items-center gap-2 gap-y-1">
                <h3 className="font-semibold text-slate-900 text-sm">{t.threat_type}</h3>
                <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${s.badge}`}>{t.severity}</span>
                <span className={`w-1.5 h-1.5 rounded-full ${s.dot} sm:hidden`} aria-hidden />
              </div>
              <p className="text-sm text-slate-600 mt-2 leading-relaxed">{t.message}</p>
              <p className="text-[11px] text-slate-400 mt-2 font-medium">Panel time · {fmt(t.timestamp)}</p>
            </div>
            <div className="hidden sm:flex flex-col items-end gap-1 shrink-0">
              <span className={`w-2 h-2 rounded-full ${s.dot}`} aria-hidden />
              <time className="text-xs text-slate-400 whitespace-nowrap">{fmt(t.timestamp)}</time>
            </div>
          </li>
        );
      })}
    </ul>
  );
}
