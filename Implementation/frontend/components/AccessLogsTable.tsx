"use client";

import { AccessLog } from "@/lib/api";
import StatusBadge from "./StatusBadge";

function fmt(iso: string) {
  return new Date(iso).toLocaleString("en-US", {
    month: "short", day: "2-digit",
    hour: "2-digit", minute: "2-digit", second: "2-digit",
  });
}

interface Props { logs: AccessLog[]; loading?: boolean }

export default function AccessLogsTable({ logs, loading }: Props) {
  return (
    <div className="overflow-hidden rounded-xl border border-slate-100 bg-white shadow-sm">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-100">
            {["Person ID", "Name", "Type", "Status", "Confidence", "Timestamp"].map((h) => (
              <th key={h} className="px-5 py-3.5 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-50">
          {loading ? (
            <tr><td colSpan={6} className="text-center py-10 text-slate-400">Loading…</td></tr>
          ) : logs.length === 0 ? (
            <tr><td colSpan={6} className="text-center py-10 text-slate-400">No records found</td></tr>
          ) : logs.map((log, i) => (
            <tr key={i} className="hover:bg-slate-50 transition-colors">
              <td className="px-5 py-3.5 font-mono text-xs text-slate-500">{log.person_id ?? "—"}</td>
              <td className="px-5 py-3.5 font-medium text-slate-700">{log.name ?? "Unknown"}</td>
              <td className="px-5 py-3.5">
                {log.type === "entry" ? (
                  <span className="inline-flex items-center gap-1.5 bg-emerald-50 text-emerald-700 text-xs font-semibold px-2.5 py-1 rounded-full">
                    <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><polyline points="10 17 15 12 10 7"/><line x1="15" y1="12" x2="3" y2="12"/></svg>
                    Entry
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 bg-slate-100 text-slate-500 text-xs font-semibold px-2.5 py-1 rounded-full">
                    <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
                    Exit
                  </span>
                )}
              </td>
              <td className="px-5 py-3.5">
                <StatusBadge variant={log.status === "success" ? "healthy" : "critical"} label={log.status} />
              </td>
              <td className="px-5 py-3.5 text-slate-600">{(log.confidence * 100).toFixed(1)}%</td>
              <td className="px-5 py-3.5 text-slate-400 text-xs">{fmt(log.timestamp)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
