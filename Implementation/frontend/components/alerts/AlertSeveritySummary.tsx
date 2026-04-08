"use client";

import { useMemo } from "react";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { Threat } from "@/lib/api";
import { severityFill } from "@/lib/theme";

const ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW"] as const;

export default function AlertSeveritySummary({ threats }: { threats: Threat[] }) {
  const data = useMemo(() => {
    const counts: Record<string, number> = { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0 };
    for (const t of threats) {
      if (counts[t.severity] !== undefined) counts[t.severity]++;
    }
    return ORDER.map((name) => ({ name, count: counts[name] }));
  }, [threats]);

  const total = threats.length;
  if (total === 0) {
    return (
      <div className="rounded-2xl border border-slate-100 bg-white/80 p-5 text-center shadow-sm">
        <p className="text-sm font-medium text-slate-600">Severity breakdown</p>
        <p className="text-xs text-slate-400 mt-2 leading-relaxed">No threats in this view — chart appears when alerts exist.</p>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-amber-100/80 bg-white/85 backdrop-blur-sm p-4 shadow-sm ring-1 ring-amber-50/50">
      <h2 className="text-sm font-semibold text-slate-800">Threats at the entrance</h2>
      <p className="text-xs text-slate-500 mt-0.5 mb-3">Count by severity for the current filter — same camera stream as the door panel</p>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
          <XAxis dataKey="name" tick={{ fontSize: 10, fill: "#64748b" }} axisLine={false} tickLine={false} />
          <YAxis width={32} allowDecimals={false} tick={{ fontSize: 10, fill: "#64748b" }} axisLine={false} tickLine={false} />
          <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0" }} />
          <Bar dataKey="count" radius={[6, 6, 0, 0]}>
            {data.map((d) => (
              <Cell key={d.name} fill={severityFill[d.name] ?? "#cbd5e1"} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
