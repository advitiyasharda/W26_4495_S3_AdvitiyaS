interface Props {
  title: string;
  value: React.ReactNode;
  sub?: React.ReactNode;
  icon?: React.ReactNode;
  trend?: { value: number; label?: string };
}

export default function StatCard({ title, value, sub, icon, trend }: Props) {
  const up = trend && trend.value >= 0;

  return (
    <div className="bg-white rounded-xl border border-slate-100 p-5 flex flex-col gap-3 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">{title}</p>
        {icon && (
          <div className="w-8 h-8 rounded-lg bg-slate-50 flex items-center justify-center text-slate-400">
            {icon}
          </div>
        )}
      </div>

      <div className="flex items-end gap-3">
        <span className="text-3xl font-bold text-slate-800">{value}</span>
        {trend && (
          <span
            className={`flex items-center gap-0.5 text-xs font-semibold mb-1 ${
              up ? "text-emerald-500" : "text-red-400"
            }`}
          >
            {up ? (
              <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}>
                <polyline points="18 15 12 9 6 15" />
              </svg>
            ) : (
              <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}>
                <polyline points="6 9 12 15 18 9" />
              </svg>
            )}
            {Math.abs(trend.value)}%
          </span>
        )}
      </div>

      {sub && <p className="text-xs text-slate-400">{sub}</p>}
    </div>
  );
}
