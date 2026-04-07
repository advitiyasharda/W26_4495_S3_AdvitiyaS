"use client";

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import type { ObjectDetectionEvent } from "@/lib/api";
import { objectCategoryFill } from "@/lib/theme";

function aggregate(events: ObjectDetectionEvent[]) {
  const map: Record<string, number> = {};
  for (const e of events) {
    map[e.category] = (map[e.category] ?? 0) + 1;
  }
  return Object.entries(map).map(([name, count]) => ({
    name: name.replace(/_/g, " "),
    count,
    key: name,
  }));
}

export default function ObjectCategoryBar({ events }: { events: ObjectDetectionEvent[] }) {
  const data = aggregate(events);
  if (data.length === 0) {
    return <div className="flex items-center justify-center h-44 text-slate-400 text-sm">No object events in range</div>;
  }

  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data} layout="vertical" margin={{ top: 4, right: 16, left: 8, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
        <XAxis type="number" allowDecimals={false} tick={{ fontSize: 10, fill: "#64748b" }} />
        <YAxis type="category" dataKey="name" width={100} tick={{ fontSize: 10, fill: "#64748b" }} />
        <Tooltip contentStyle={{ borderRadius: 12, fontSize: 12 }} />
        <Bar dataKey="count" radius={[0, 4, 4, 0]}>
          {data.map((row) => (
            <Cell key={row.key} fill={objectCategoryFill[row.key] ?? "#94a3b8"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
