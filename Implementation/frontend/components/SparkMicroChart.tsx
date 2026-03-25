"use client";

import { useId, useMemo } from "react";

/** Tiny area + line spark — animates in; meant for dashboard KPI cards */
export default function SparkMicroChart({
  values,
  color,
  className = "",
}: {
  values: number[];
  color: string;
  className?: string;
}) {
  const gid = useId().replace(/:/g, "");
  const gradId = `spark-fill-${gid}`;

  const { pathLine, pathArea, w, h } = useMemo(() => {
    const W = 72;
    const H = 20;
    const pad = 1;
    const vals = values.length ? values : [0, 0];
    const max = Math.max(...vals, 1);
    const n = vals.length;
    const step = n > 1 ? (W - pad * 2) / (n - 1) : 0;
    const pts: [number, number][] = vals.map((v, i) => {
      const x = pad + i * step;
      const y = pad + (1 - v / max) * (H - pad * 2);
      return [x, y];
    });
    const lineD = pts.map(([x, y], i) => `${i === 0 ? "M" : "L"} ${x.toFixed(1)} ${y.toFixed(1)}`).join(" ");
    const areaD = `${lineD} L ${pts[pts.length - 1][0].toFixed(1)} ${H - pad} L ${pts[0][0].toFixed(1)} ${H - pad} Z`;
    return { pathLine: lineD, pathArea: areaD, w: W, h: H };
  }, [values]);

  const flat = values.length > 0 && values.every((v) => v === 0);

  return (
    <div className={`relative h-5 w-full ${className}`} aria-hidden>
      <svg viewBox={`0 0 ${w} ${h}`} className="h-full w-full overflow-visible" preserveAspectRatio="xMidYMid meet">
        <defs>
          <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.35" />
            <stop offset="100%" stopColor={color} stopOpacity="0.02" />
          </linearGradient>
        </defs>
        {!flat && (
          <path
            d={pathArea}
            fill={`url(#${gradId})`}
            className="motion-safe:animate-spark-fill"
          />
        )}
        <path
          d={pathLine}
          fill="none"
          stroke={color}
          strokeWidth="1.35"
          strokeLinecap="round"
          strokeLinejoin="round"
          vectorEffect="non-scaling-stroke"
          className="motion-safe:animate-spark-draw opacity-90"
          pathLength={100}
        />
      </svg>
      {!flat && values.length > 0 && (
        <span
          className="absolute right-0 top-1/2 h-1.5 w-1.5 -translate-y-1/2 rounded-full motion-safe:animate-spark-dot opacity-80"
          style={{ backgroundColor: color }}
        />
      )}
    </div>
  );
}
