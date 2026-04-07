import type { ReactNode } from "react";

export type PageHeroTone = "teal" | "sky" | "amber" | "rose" | "violet" | "indigo" | "pink";

const shells: Record<PageHeroTone, string> = {
  teal: "border-teal-100/85 bg-gradient-to-br from-white via-teal-50/35 to-cyan-50/25 ring-teal-100/45",
  sky: "border-sky-100/85 bg-gradient-to-br from-white via-sky-50/40 to-teal-50/20 ring-sky-100/45",
  amber: "border-amber-100/85 bg-gradient-to-br from-white via-amber-50/35 to-orange-50/25 ring-amber-100/45",
  rose: "border-rose-100/85 bg-gradient-to-br from-white via-rose-50/30 to-pink-50/25 ring-rose-100/45",
  violet: "border-violet-100/85 bg-gradient-to-br from-white via-violet-50/35 to-slate-50/40 ring-violet-100/45",
  indigo: "border-indigo-100/85 bg-gradient-to-br from-white via-indigo-50/30 to-violet-50/25 ring-indigo-100/45",
  pink: "border-pink-100/85 bg-gradient-to-br from-white via-pink-50/35 to-orange-50/30 ring-pink-100/45",
};

const iconShells: Record<PageHeroTone, string> = {
  teal: "bg-teal-100/50 text-teal-700 ring-teal-200/40",
  sky: "bg-sky-100/50 text-sky-700 ring-sky-200/40",
  amber: "bg-amber-100/55 text-amber-800 ring-amber-200/45",
  rose: "bg-rose-100/50 text-rose-700 ring-rose-200/40",
  violet: "bg-violet-100/50 text-violet-700 ring-violet-200/40",
  indigo: "bg-indigo-100/50 text-indigo-700 ring-indigo-200/40",
  pink: "bg-pink-100/50 text-pink-700 ring-pink-200/40",
};

interface PageHeroProps {
  tone?: PageHeroTone;
  eyebrow?: string;
  title: string;
  description?: ReactNode;
  icon?: ReactNode;
  aside?: ReactNode;
  children?: ReactNode;
}

export default function PageHero({
  tone = "teal",
  eyebrow,
  title,
  description,
  icon,
  aside,
  children,
}: PageHeroProps) {
  return (
    <div
      className={`relative overflow-hidden rounded-2xl border px-5 sm:px-6 py-5 shadow-sm ring-1 ${shells[tone]}`}
    >
      <div className="pointer-events-none absolute -right-8 -top-10 h-36 w-36 rounded-full bg-white/40 blur-2xl" />
      <div className="relative flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="flex gap-4 min-w-0">
          {icon && (
            <div
              className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl ring-1 ${iconShells[tone]}`}
            >
              {icon}
            </div>
          )}
          <div className="min-w-0">
            {eyebrow && (
              <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">{eyebrow}</p>
            )}
            <h1 className="text-2xl font-semibold tracking-tight text-slate-900 mt-0.5">{title}</h1>
            {description && <div className="text-sm text-slate-600 mt-1.5 max-w-2xl leading-relaxed">{description}</div>}
            {children}
          </div>
        </div>
        {aside && <div className="flex flex-wrap items-start gap-2 shrink-0 lg:justify-end">{aside}</div>}
      </div>
    </div>
  );
}
