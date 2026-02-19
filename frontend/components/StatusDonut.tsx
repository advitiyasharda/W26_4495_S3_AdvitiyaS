"use client";

import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import { AccessLog } from "@/lib/api";

interface Props { logs: AccessLog[] }

const COLORS = ["#10b981", "#f87171", "#fbbf24", "#94a3b8"];

export default function StatusDonut({ logs }: Props) {
  const success = logs.filter((l) => l.status === "success").length;
  const failed  = logs.filter((l) => l.status !== "success").length;
  const entries = logs.filter((l) => l.type === "entry").length;
  const exits   = logs.filter((l) => l.type === "exit").length;

  const data = [
    { name: "Success",  value: success },
    { name: "Failed",   value: failed },
    { name: "Entries",  value: entries },
    { name: "Exits",    value: exits },
  ].filter((d) => d.value > 0);

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-slate-400 text-sm">
        No data yet
      </div>
    );
  }

  const total = data.reduce((s, d) => s + d.value, 0);

  return (
    <div className="flex items-center gap-6">
      <div className="w-36 h-36 flex-shrink-0">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={38}
              outerRadius={58}
              paddingAngle={3}
              dataKey="value"
              strokeWidth={0}
            >
              {data.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip
              formatter={(v: number) => [`${v} (${((v / total) * 100).toFixed(0)}%)`, ""]}
              contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #e2e8f0" }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <ul className="space-y-2 text-sm flex-1">
        {data.map((d, i) => (
          <li key={d.name} className="flex items-center justify-between">
            <span className="flex items-center gap-2 text-slate-600">
              <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: COLORS[i] }} />
              {d.name}
            </span>
            <span className="font-semibold text-slate-700">{((d.value / total) * 100).toFixed(0)}%</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
