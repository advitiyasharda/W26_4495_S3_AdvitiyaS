"use client";

import { useMemo } from "react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import type { AccessLog } from "@/lib/api";
import { chart as C } from "@/lib/theme";

interface Props {
  logs: AccessLog[];
}

export default function LogsDoorSummary({ logs }: Props) {
  const flow = useMemo(() => {
    let inC = 0;
    let outC = 0;
    for (const l of logs) {
      if (l.type === "entry") inC++;
      else outC++;
    }
    return [
      { name: "Entries", value: inC, fill: C.mint },
      { name: "Exits", value: outC, fill: C.sky },
    ].filter((d) => d.value > 0);
  }, [logs]);

  const access = useMemo(() => {
    let ok = 0;
    let bad = 0;
    for (const l of logs) {
      if (l.status === "success") ok++;
      else bad++;
    }
    return [
      { name: "Granted", value: ok, fill: C.sage },
      { name: "Denied / failed", value: bad, fill: C.blushSoft },
    ].filter((d) => d.value > 0);
  }, [logs]);

  if (logs.length === 0) return null;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div className="rounded-2xl border border-teal-100/80 bg-white/80 backdrop-blur-sm p-4 shadow-sm ring-1 ring-teal-50/60">
        <h2 className="text-sm font-semibold text-slate-800">Door flow (this list)</h2>
        <p className="text-xs text-slate-500 mt-0.5 mb-2">People crossing the threshold — in vs out</p>
        {flow.length === 0 ? (
          <p className="text-sm text-slate-400 py-6 text-center">No movements</p>
        ) : (
          <div className="flex flex-col sm:flex-row items-center gap-4">
            <div className="h-40 w-40 shrink-0">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={flow} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={48} outerRadius={62} paddingAngle={2}>
                    {flow.map((e) => (
                      <Cell key={e.name} fill={e.fill} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <ul className="text-xs space-y-2 flex-1 w-full">
              {flow.map((f) => (
                <li key={f.name} className="flex justify-between items-center gap-2 border-b border-slate-50 pb-2 last:border-0">
                  <span className="flex items-center gap-2 text-slate-600">
                    <span className="h-2.5 w-2.5 rounded-full shrink-0" style={{ background: f.fill }} />
                    {f.name}
                  </span>
                  <span className="font-semibold tabular-nums text-slate-800">{f.value}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
      <div className="rounded-2xl border border-slate-100/90 bg-white/80 backdrop-blur-sm p-4 shadow-sm">
        <h2 className="text-sm font-semibold text-slate-800">Face decision outcomes</h2>
        <p className="text-xs text-slate-500 mt-0.5 mb-2">Successful recognition vs failed attempts at the panel</p>
        {access.length === 0 ? (
          <p className="text-sm text-slate-400 py-6 text-center">No data</p>
        ) : (
          <div className="flex flex-col sm:flex-row items-center gap-4">
            <div className="h-40 w-40 shrink-0">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={access} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={48} outerRadius={62} paddingAngle={2}>
                    {access.map((e) => (
                      <Cell key={e.name} fill={e.fill} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <ul className="text-xs space-y-2 flex-1 w-full">
              {access.map((f) => (
                <li key={f.name} className="flex justify-between items-center gap-2 border-b border-slate-50 pb-2 last:border-0">
                  <span className="flex items-center gap-2 text-slate-600">
                    <span className="h-2.5 w-2.5 rounded-full shrink-0" style={{ background: f.fill }} />
                    {f.name}
                  </span>
                  <span className="font-semibold tabular-nums text-slate-800">{f.value}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
