"use client";

import { AccessLog } from "@/lib/api";
import StatusBadge from "./StatusBadge";
import { IconCalmCheck, IconEntry, IconExit } from "@/components/icons/DoorIcons";

function fmt(iso: string) {
  return new Date(iso).toLocaleString("en-US", {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function confTone(pct: number): string {
  if (pct >= 85) return "bg-teal-400";
  if (pct >= 60) return "bg-amber-300";
  return "bg-slate-300";
}

interface Props {
  logs: AccessLog[];
  loading?: boolean;
}

export default function AccessLogsTable({ logs, loading }: Props) {
  return (
    <div className="overflow-hidden rounded-2xl border border-slate-100/90 bg-white/95 shadow-sm ring-1 ring-slate-50/80">
      <div className="px-5 py-3 border-b border-slate-100 bg-gradient-to-r from-teal-50/40 via-white to-sky-50/30">
        <h2 className="text-sm font-semibold text-slate-800">Threshold crossings</h2>
        <p className="text-xs text-slate-500 mt-0.5">
          Each row is a face-verified (or attempted) entry or exit at the smart door.
        </p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm min-w-[720px]">
          <thead>
            <tr className="border-b border-slate-100 bg-slate-50/90">
              {["Person ID", "Name", "Movement", "Status", "Match strength", "Time"].map((h) => (
                <th key={h} className="px-4 sm:px-5 py-3 text-left text-[11px] font-semibold text-slate-500 uppercase tracking-wide">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {loading ? (
              <tr>
                <td colSpan={6} className="text-center py-14 text-slate-400 text-sm">
                  Loading access events…
                </td>
              </tr>
            ) : logs.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-14 px-6">
                  <div className="flex flex-col items-center text-center max-w-md mx-auto">
                    <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-100 text-slate-400 mb-3">
                      <IconCalmCheck className="w-8 h-8" />
                    </div>
                    <p className="text-sm font-semibold text-slate-700">No crossings in this list</p>
                    <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                      Increase the row limit or connect the door panel — successful and failed attempts will show with
                      direction (in / out).
                    </p>
                  </div>
                </td>
              </tr>
            ) : (
              logs.map((log, i) => {
                const pct = Math.min(100, Math.max(0, log.confidence * 100));
                return (
                  <tr key={i} className="hover:bg-teal-50/25 transition-colors">
                    <td className="px-4 sm:px-5 py-3 font-mono text-xs text-slate-500 align-middle">{log.person_id ?? "—"}</td>
                    <td className="px-4 sm:px-5 py-3 font-medium text-slate-800 align-middle">{log.name ?? "Unknown"}</td>
                    <td className="px-4 sm:px-5 py-3 align-middle">
                      {log.type === "entry" ? (
                        <span className="inline-flex items-center gap-1.5 bg-teal-50 text-teal-800 text-xs font-semibold px-2.5 py-1 rounded-full ring-1 ring-teal-200/50">
                          <IconEntry className="w-3.5 h-3.5 shrink-0" />
                          Entry
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 bg-sky-50 text-sky-800 text-xs font-semibold px-2.5 py-1 rounded-full ring-1 ring-sky-200/50">
                          <IconExit className="w-3.5 h-3.5 shrink-0" />
                          Exit
                        </span>
                      )}
                    </td>
                    <td className="px-4 sm:px-5 py-3 align-middle">
                      <StatusBadge variant={log.status === "success" ? "healthy" : "critical"} label={log.status} />
                    </td>
                    <td className="px-4 sm:px-5 py-3 align-middle w-[140px]">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden min-w-[56px]">
                          <div className={`h-full rounded-full ${confTone(pct)}`} style={{ width: `${pct}%` }} />
                        </div>
                        <span className="text-xs tabular-nums text-slate-600 w-11 shrink-0">{pct.toFixed(0)}%</span>
                      </div>
                    </td>
                    <td className="px-4 sm:px-5 py-3 text-slate-500 text-xs whitespace-nowrap align-middle">{fmt(log.timestamp)}</td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
