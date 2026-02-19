"use client";

import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend,
} from "recharts";
import { AccessLog } from "@/lib/api";

interface Props { logs: AccessLog[] }

function buildChartData(logs: AccessLog[]) {
  const buckets: Record<string, { hour: string; entries: number; exits: number }> = {};

  logs.forEach((log) => {
    const d = new Date(log.timestamp);
    const label = `${d.getHours().toString().padStart(2, "0")}:00`;
    if (!buckets[label]) buckets[label] = { hour: label, entries: 0, exits: 0 };
    if (log.type === "entry") buckets[label].entries++;
    else buckets[label].exits++;
  });

  return Object.values(buckets).sort((a, b) => a.hour.localeCompare(b.hour));
}

const CustomTooltip = ({ active, payload, label }: { active?: boolean; payload?: { color: string; name: string; value: number }[]; label?: string }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-slate-100 rounded-xl shadow-lg p-3 text-xs">
      <p className="font-semibold text-slate-700 mb-1">{label}</p>
      {payload.map((p) => (
        <p key={p.name} style={{ color: p.color }} className="flex items-center gap-1">
          <span className="inline-block w-2 h-2 rounded-full" style={{ background: p.color }} />
          {p.name}: <span className="font-semibold">{p.value}</span>
        </p>
      ))}
    </div>
  );
};

export default function AccessChart({ logs }: Props) {
  const data = buildChartData(logs);

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-slate-400 text-sm">
        No access data yet
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} barCategoryGap="35%" barGap={4}>
        <CartesianGrid vertical={false} stroke="#f1f5f9" />
        <XAxis
          dataKey="hour"
          tick={{ fontSize: 11, fill: "#94a3b8" }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tick={{ fontSize: 11, fill: "#94a3b8" }}
          axisLine={false}
          tickLine={false}
          width={28}
          allowDecimals={false}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: "#f8fafc" }} />
        <Legend
          iconType="circle"
          iconSize={8}
          wrapperStyle={{ fontSize: 12, paddingTop: 12 }}
        />
        <Bar dataKey="entries" name="Entries" fill="#10b981" radius={[4, 4, 0, 0]} />
        <Bar dataKey="exits"   name="Exits"   fill="#94a3b8" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
