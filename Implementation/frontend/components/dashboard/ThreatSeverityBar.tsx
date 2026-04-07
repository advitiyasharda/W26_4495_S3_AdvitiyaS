"use client";

import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { Threat } from "@/lib/api";
import { severityFill } from "@/lib/theme";

const ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"] as const;

export default function ThreatSeverityBar({
  threats,
  embedded,
}: {
  threats: Threat[];
  /** Compact chrome when nested inside another labeled card */
  embedded?: boolean;
}) {
  const map: Record<string, number> = {};
  for (const t of threats) {
    map[t.severity] = (map[t.severity] ?? 0) + 1;
  }
  const data = ORDER.map((name) => ({ name, count: map[name] ?? 0 }));

  const shell = embedded
    ? "rounded-xl border border-slate-100/80 bg-white/70 p-3"
    : "rounded-xl border border-slate-100/90 bg-gradient-to-br from-amber-50/30 via-white to-white p-5 shadow-sm border-l-4 border-l-amber-400";

  if (threats.length === 0) {
    return (
      <div className={embedded ? shell : `${shell} border-l-4 border-l-amber-300`}>
        {!embedded && (
          <>
            <h3 className="text-sm font-semibold text-slate-800">Threats by severity</h3>
            <p className="text-xs text-slate-500 mb-3">Same timeline as dashboard</p>
          </>
        )}
        <p className={`text-xs text-slate-400 text-center py-4 ${embedded ? "" : "mt-8"}`}>No threats in this window</p>
      </div>
    );
  }

  return (
    <div className={shell}>
      {!embedded && (
        <>
          <h3 className="text-sm font-semibold text-slate-800">Threats by severity</h3>
          <p className="text-xs text-slate-500 mb-3">Same timeline as dashboard</p>
        </>
      )}
      <ResponsiveContainer width="100%" height={embedded ? 160 : 200}>
        <BarChart data={data} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis dataKey="name" tick={{ fontSize: 10, fill: "#64748b" }} axisLine={false} tickLine={false} />
          <YAxis width={28} allowDecimals={false} tick={{ fontSize: 10, fill: "#64748b" }} />
          <Tooltip contentStyle={{ borderRadius: 12, fontSize: 12 }} />
          <Bar dataKey="count" radius={[6, 6, 0, 0]}>
            {data.map((row) => (
              <Cell key={row.name} fill={severityFill[row.name] ?? "#cbd5e1"} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
