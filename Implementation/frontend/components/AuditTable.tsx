"use client";

import { AuditEntry } from "@/lib/api";

function fmt(iso: string) {
  return new Date(iso).toLocaleString("en-US", {
    month: "short", day: "2-digit",
    hour: "2-digit", minute: "2-digit", second: "2-digit",
  });
}

interface Props { entries: AuditEntry[]; loading?: boolean }

export default function AuditTable({ entries, loading }: Props) {
  return (
    <div className="overflow-hidden rounded-xl border border-slate-100 bg-white shadow-sm">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-100">
            {["Action", "User / System", "Resource", "Result", "Timestamp"].map((h) => (
              <th key={h} className="px-5 py-3.5 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-50">
          {loading ? (
            <tr><td colSpan={5} className="text-center py-10 text-slate-400">Loading…</td></tr>
          ) : entries.length === 0 ? (
            <tr><td colSpan={5} className="text-center py-10 text-slate-400">No audit records found</td></tr>
          ) : entries.map((e, i) => (
            <tr key={i} className="hover:bg-slate-50 transition-colors">
              <td className="px-5 py-3.5 font-medium text-slate-700">{e.action}</td>
              <td className="px-5 py-3.5 text-slate-500">{e.user ?? "—"}</td>
              <td className="px-5 py-3.5 text-slate-500">{e.resource ?? "—"}</td>
              <td className="px-5 py-3.5">
                <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full ${
                  e.result === "success"
                    ? "bg-emerald-50 text-emerald-700"
                    : "bg-red-50 text-red-600"
                }`}>{e.result}</span>
              </td>
              <td className="px-5 py-3.5 text-slate-400 text-xs">{fmt(e.timestamp)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
