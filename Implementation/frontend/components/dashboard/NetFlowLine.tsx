"use client";

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";
import type { AccessLog } from "@/lib/api";
import { chart as C } from "@/lib/theme";

function buildNetByHour(logs: AccessLog[]) {
  const buckets: Record<string, { hour: string; net: number }> = {};
  for (const log of logs) {
    const d = new Date(log.timestamp);
    const label = `${d.getHours().toString().padStart(2, "0")}:00`;
    if (!buckets[label]) buckets[label] = { hour: label, net: 0 };
    if (log.type === "entry") buckets[label].net++;
    else buckets[label].net--;
  }
  return Object.values(buckets).sort((a, b) => a.hour.localeCompare(b.hour));
}

export default function NetFlowLine({ logs }: { logs: AccessLog[] }) {
  const data = buildNetByHour(logs);
  if (data.length === 0) {
    return <div className="flex items-center justify-center h-44 text-slate-400 text-sm">No access data in range</div>;
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
        <XAxis dataKey="hour" tick={{ fontSize: 10, fill: "#64748b" }} axisLine={false} tickLine={false} />
        <YAxis width={32} tick={{ fontSize: 10, fill: "#64748b" }} axisLine={false} tickLine={false} />
        <Tooltip contentStyle={{ borderRadius: 12, fontSize: 12 }} />
        <ReferenceLine y={0} stroke="#cbd5e1" strokeDasharray="3 3" />
        <Line type="monotone" dataKey="net" name="Net (entries − exits)" stroke={C.lilac} strokeWidth={2} dot={{ r: 3, fill: C.lilacSoft }} />
      </LineChart>
    </ResponsiveContainer>
  );
}
