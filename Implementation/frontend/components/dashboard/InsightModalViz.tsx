"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import type { AccessLog, FallEvent, ObjectDetectionEvent, Threat } from "@/lib/api";
import type { InsightId } from "@/components/dashboard/dashboardCardTypes";
import { chart as C } from "@/lib/theme";
import { objectEventsPerHour } from "@/lib/objectAnalytics";
import { fallIndexVsScore, hourlySingleType, threatCumulative } from "@/lib/insightChartData";

const tip = { borderRadius: 12, fontSize: 11, border: "1px solid #e2e8f0" };

export default function InsightModalViz({
  insight,
  logs,
  threats,
  falls,
  objects,
}: {
  insight: InsightId;
  logs: AccessLog[];
  threats: Threat[];
  falls: FallEvent[];
  objects: ObjectDetectionEvent[];
}) {
  if (insight === "traffic") {
    if (logs.length === 0) {
      return <p className="text-xs text-slate-400 text-center py-6">No access events in window</p>;
    }
    return (
      <div className="rounded-xl bg-slate-50/50 border border-slate-100/80 p-3">
        <p className="text-[10px] font-medium text-slate-500 uppercase tracking-wide mb-2">Entries vs exits by hour</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <MiniHourly title="Entries" data={hourlySingleType(logs, "entry")} stroke={C.mint} />
          <MiniHourly title="Exits" data={hourlySingleType(logs, "exit")} stroke={C.sky} />
        </div>
      </div>
    );
  }

  if (insight === "alerts") {
    const data = threatCumulative(threats);
    if (data.length === 0) {
      return <p className="text-xs text-slate-400 text-center py-6">No threats in window</p>;
    }
    return (
      <div className="rounded-xl bg-slate-50/50 border border-slate-100/80 p-3">
        <p className="text-[10px] font-medium text-slate-500 uppercase tracking-wide mb-2">Cumulative threats (order)</p>
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart data={data} margin={{ top: 4, right: 8, left: 0, bottom: 20 }}>
            <defs>
              <linearGradient id="cumThreat" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={C.butter} stopOpacity={0.35} />
                <stop offset="100%" stopColor={C.butter} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="n" tick={{ fontSize: 9, fill: "#94a3b8" }} axisLine={false} tickLine={false} label={{ value: "nth threat", position: "insideBottom", offset: -14, fontSize: 9, fill: "#94a3b8" }} />
            <YAxis width={28} allowDecimals={false} tick={{ fontSize: 9, fill: "#94a3b8" }} />
            <Tooltip contentStyle={tip} />
            <Area type="stepAfter" dataKey="cumulative" stroke={C.peach} strokeWidth={2} fill="url(#cumThreat)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (insight === "falls") {
    const data = fallIndexVsScore(falls);
    if (data.length === 0) {
      return <p className="text-xs text-slate-400 text-center py-6">No falls in window</p>;
    }
    return (
      <div className="rounded-xl bg-slate-50/50 border border-slate-100/80 p-3">
        <p className="text-[10px] font-medium text-slate-500 uppercase tracking-wide mb-2">Chronological score (scatter)</p>
        <ResponsiveContainer width="100%" height={200}>
          <ScatterChart margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis type="number" dataKey="i" name="Order" tick={{ fontSize: 9, fill: "#94a3b8" }} />
            <YAxis type="number" dataKey="pct" name="%" unit="%" domain={[0, 100]} tick={{ fontSize: 9, fill: "#94a3b8" }} />
            <ZAxis range={[40, 40]} />
            <Tooltip cursor={{ strokeDasharray: "3 3" }} contentStyle={tip} />
            <Scatter data={data} fill={C.blushSoft} stroke={C.blush} strokeWidth={1} />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (insight === "objects") {
    if (objects.length === 0) {
      return <p className="text-xs text-slate-400 text-center py-6">No object events in window</p>;
    }

    const hourly = objectEventsPerHour(objects);
    const hMax = Math.max(...hourly.map((h) => h.count), 1);

    return (
      <div className="rounded-xl bg-slate-50/50 border border-slate-100/80 p-3">
        <p className="text-[10px] font-medium text-slate-500 uppercase tracking-wide mb-2">Detections by hour (local)</p>
        <p className="text-[11px] text-slate-500 mb-3 leading-relaxed">
          How many object events occurred in each clock hour for the dashboard time range. Category and class detail stay on
          the object detection page.
        </p>
        <ResponsiveContainer width="100%" height={240}>
          <AreaChart data={hourly} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="objKpiModalHour" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={C.lilac} stopOpacity={0.35} />
                <stop offset="100%" stopColor={C.lilac} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="hour" tick={{ fontSize: 9, fill: "#94a3b8" }} interval={2} axisLine={false} tickLine={false} />
            <YAxis width={28} domain={[0, Math.ceil(hMax * 1.1)]} allowDecimals={false} tick={{ fontSize: 9, fill: "#94a3b8" }} />
            <Tooltip contentStyle={tip} />
            <Area type="monotone" dataKey="count" stroke={C.lilac} strokeWidth={2} fill="url(#objKpiModalHour)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    );
  }

  return null;
}

function MiniHourly({ title, data, stroke }: { title: string; data: { hour: string; count: number }[]; stroke: string }) {
  if (data.length === 0) {
    return <p className="text-xs text-slate-400 py-4 text-center">{title}: no data</p>;
  }
  return (
    <div>
      <p className="text-[10px] font-medium text-slate-500 mb-1">{title}</p>
      <ResponsiveContainer width="100%" height={140}>
        <LineChart data={data} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis dataKey="hour" tick={{ fontSize: 8, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
          <YAxis width={20} allowDecimals={false} tick={{ fontSize: 8, fill: "#94a3b8" }} />
          <Tooltip contentStyle={tip} />
          <Line type="monotone" dataKey="count" stroke={stroke} strokeWidth={2} dot={false} activeDot={{ r: 3 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
