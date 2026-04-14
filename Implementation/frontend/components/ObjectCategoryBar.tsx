"use client";

import { ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, Legend } from "recharts";
import type { ObjectDetectionEvent } from "@/lib/api";
import { objectCategoryFill, chart as chartPalette } from "@/lib/theme";
import { avgConfidenceByCategory } from "@/lib/objectAnalytics";

export default function ObjectCategoryBar({ events }: { events: ObjectDetectionEvent[] }) {
  const data = avgConfidenceByCategory(events);
  if (data.length === 0) {
    return <div className="flex items-center justify-center h-44 text-slate-400 text-sm">No object events in range</div>;
  }

  const chartData = data.map(d => ({
    ...d,
    avgPct: Math.round(d.avg * 100),
  }));

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white border border-slate-200 shadow-sm p-3 rounded-xl text-xs z-50 relative">
          <p className="font-semibold text-slate-800 mb-1">{label}</p>
          <p className="text-slate-600">Volume: <span className="font-semibold tabular-nums text-slate-900">{payload[0].value}</span></p>
          {payload[1] && <p className="text-slate-600 mt-1">Avg Confidence: <span className="font-semibold tabular-nums text-indigo-600">{payload[1].value}%</span></p>}
        </div>
      );
    }
    return null;
  };

  return (
    <ResponsiveContainer width="100%" height={280}>
      <ComposedChart data={chartData} margin={{ top: 8, right: 0, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
        <XAxis dataKey="label" tick={{ fontSize: 10, fill: "#64748b" }} axisLine={false} tickLine={false} />
        <YAxis yAxisId="left" tick={{ fontSize: 10, fill: "#64748b" }} axisLine={false} tickLine={false} allowDecimals={false} />
        <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 10, fill: "#94a3b8" }} axisLine={false} tickLine={false} domain={[0, 100]} hide={true} />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: "#f8fafc" }} />
        <Legend wrapperStyle={{ fontSize: 11, paddingTop: 10 }} iconType="circle" />
        <Bar yAxisId="left" name="Volume" dataKey="n" radius={[6, 6, 0, 0]} maxBarSize={56}>
          {chartData.map((row) => (
            <Cell key={row.category} fill={objectCategoryFill[row.category] ?? "#94a3b8"} />
          ))}
        </Bar>
        <Line yAxisId="right" name="Avg Confidence (%)" type="monotone" dataKey="avgPct" stroke={chartPalette.indigo} strokeWidth={2.5} dot={{ r: 4, strokeWidth: 2, fill: "white" }} activeDot={{ r: 6 }} />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
