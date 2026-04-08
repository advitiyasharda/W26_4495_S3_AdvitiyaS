"use client";

import { useMemo } from "react";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { AuditEntry } from "@/lib/api";
import { auditActionFill } from "@/lib/theme";

function shortAction(a: string): string {
  return a.replace(/_/g, " ").toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function ComplianceActionChart({ entries }: { entries: AuditEntry[] }) {
  const data = useMemo(() => {
    const m = new Map<string, number>();
    for (const e of entries) {
      m.set(e.action, (m.get(e.action) ?? 0) + 1);
    }
    return [...m.entries()]
      .map(([action, count]) => ({
        action,
        label: shortAction(action),
        count,
        fill: auditActionFill[action] ?? "#cbd5e1",
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);
  }, [entries]);

  if (entries.length === 0) {
    return (
      <div className="rounded-2xl border border-slate-100 bg-white/80 p-6 text-center text-sm text-slate-500">
        Load audit entries to see an action breakdown chart.
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-violet-100/80 bg-white/85 backdrop-blur-sm p-4 shadow-sm ring-1 ring-violet-50/50">
      <h2 className="text-sm font-semibold text-slate-800">Activity at the smart door</h2>
      <p className="text-xs text-slate-500 mt-0.5 mb-3">Top audit actions in the loaded window (access, enrollments, exports, config)</p>
      <ResponsiveContainer width="100%" height={Math.min(320, 40 + data.length * 28)}>
        <BarChart layout="vertical" data={data} margin={{ top: 4, right: 16, left: 4, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
          <XAxis type="number" allowDecimals={false} tick={{ fontSize: 10, fill: "#64748b" }} axisLine={false} tickLine={false} />
          <YAxis
            type="category"
            dataKey="label"
            width={118}
            tick={{ fontSize: 9, fill: "#475569" }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            formatter={(v) => [v ?? 0, "Events"]}
            labelFormatter={(_, p) => (p?.[0]?.payload?.action as string) ?? ""}
            contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0" }}
          />
          <Bar dataKey="count" radius={[0, 6, 6, 0]}>
            {data.map((d) => (
              <Cell key={d.action} fill={d.fill} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
