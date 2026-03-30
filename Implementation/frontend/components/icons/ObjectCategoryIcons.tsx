import type { ObjectCategory } from "@/lib/api";

const cls = "w-5 h-5 shrink-0 text-teal-600/90";

/** Outline icons aligned with dashboard / sidebar (teal, minimal stroke) */
export function ObjectCategoryIcon({ category, className = cls }: { category: ObjectCategory; className?: string }) {
  switch (category) {
    case "WEAPON":
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} className={className} aria-hidden>
          <path d="M14.5 4l2.5 2.5-9 9-3 1 1-3 9-9z" />
          <path d="M12.5 6.5l1 1M5 19l2-1" />
        </svg>
      );
    case "SECURITY_THREAT":
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} className={className} aria-hidden>
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
          <path d="M12 8v4M12 16h.01" />
        </svg>
      );
    case "PARCEL":
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} className={className} aria-hidden>
          <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
          <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
          <line x1="12" y1="22.08" x2="12" y2="12" />
        </svg>
      );
    case "MOBILITY_AID":
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} className={className} aria-hidden>
          <circle cx="8" cy="8" r="3" />
          <circle cx="18" cy="17" r="3" />
          <path d="M10.5 10.5L16 16" />
          <path d="M5 21h14" />
        </svg>
      );
    case "OPERATIONAL":
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} className={className} aria-hidden>
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14 2 14 8 20 8" />
          <line x1="9" y1="15" x2="15" y2="15" />
        </svg>
      );
    default:
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} className={className} aria-hidden>
          <circle cx="12" cy="12" r="10" />
        </svg>
      );
  }
}
