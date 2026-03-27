"use client";

import { AuditEntry } from "@/lib/api";
import { AuditActionIcon } from "@/components/icons/AuditActionIcon";
import { IconInbox } from "@/components/icons/DoorIcons";

function fmt(iso: string) {
  return new Date(iso).toLocaleString("en-US", {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function formatResource(r: string | null): string {
  if (!r) return "—";
  return r.replace(/\//g, " · ").replace(/_/g, " ");
}

interface Props {
  entries: AuditEntry[];
  loading?: boolean;
}

export default function AuditTable({ entries, loading }: Props) {
  return (
    <div className="overflow-hidden rounded-2xl border border-slate-100/90 bg-white/95 shadow-sm ring-1 ring-violet-50/60">
      <div className="px-5 py-3 border-b border-slate-100 bg-gradient-to-r from-violet-50/35 via-white to-indigo-50/25">
        <h2 className="text-sm font-semibold text-slate-800">Immutable audit log</h2>
        <p className="text-xs text-slate-500 mt-0.5">
          Who did what at the door system — aligned with PIPEDA / GDPR retention expectations.
        </p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm min-w-[800px]">
          <thead>
            <tr className="border-b border-slate-100 bg-slate-50/90">
              <th className="px-4 py-3 text-left text-[11px] font-semibold text-slate-500 uppercase tracking-wide w-14">
                {" "}
              </th>
              <th className="px-2 py-3 text-left text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Action</th>
              <th className="px-4 py-3 text-left text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Actor</th>
              <th className="px-4 py-3 text-left text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Door / resource</th>
              <th className="px-4 py-3 text-left text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Result</th>
              <th className="px-4 py-3 text-left text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Time</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {loading ? (
              <tr>
                <td colSpan={6} className="text-center py-14 text-slate-400 text-sm">
                  Loading audit records…
                </td>
              </tr>
            ) : entries.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-14 px-6">
                  <div className="flex flex-col items-center text-center max-w-md mx-auto text-slate-400">
                    <IconInbox className="w-11 h-11 mb-2 opacity-60" />
                    <p className="text-sm font-semibold text-slate-600">No audit records</p>
                    <p className="text-xs mt-1 text-slate-500">Exports and access events will appear here.</p>
                  </div>
                </td>
              </tr>
            ) : (
              entries.map((e, i) => (
                <tr key={i} className="hover:bg-violet-50/20 transition-colors">
                  <td className="px-4 py-3 align-top">
                    <AuditActionIcon action={e.action} />
                  </td>
                  <td className="px-2 py-3 align-top">
                    <span className="font-semibold text-slate-800 text-sm leading-snug">{e.action.replace(/_/g, " ")}</span>
                  </td>
                  <td className="px-4 py-3 text-slate-600 align-top">
                    <span className="text-sm">{e.user ?? "—"}</span>
                  </td>
                  <td className="px-4 py-3 text-slate-600 align-top max-w-[280px]">
                    <span className="text-sm leading-snug line-clamp-2" title={e.resource ?? undefined}>
                      {formatResource(e.resource)}
                    </span>
                  </td>
                  <td className="px-4 py-3 align-top">
                    <span
                      className={`inline-flex text-xs font-semibold px-2.5 py-1 rounded-full ${
                        e.result === "success"
                          ? "bg-emerald-50 text-emerald-800 ring-1 ring-emerald-200/70"
                          : "bg-rose-50 text-rose-700 ring-1 ring-rose-200/70"
                      }`}
                    >
                      {e.result}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-500 text-xs whitespace-nowrap align-top">{fmt(e.timestamp)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
