import type { ReactNode } from "react";
import { auditActionFill } from "@/lib/theme";

const stroke = 1.5;

function IconKey({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={stroke} className={className} aria-hidden>
      <circle cx="7.5" cy="15.5" r="3.5" />
      <path d="M10.5 12.5L21 2M15 2h6v6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function IconUserPlus({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={stroke} className={className} aria-hidden>
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <line x1="19" y1="8" x2="19" y2="14" />
      <line x1="22" y1="11" x2="16" y2="11" />
    </svg>
  );
}

function IconBan({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={stroke} className={className} aria-hidden>
      <circle cx="12" cy="12" r="10" />
      <line x1="4.93" y1="4.93" x2="19.07" y2="19.07" />
    </svg>
  );
}

function IconSliders({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={stroke} className={className} aria-hidden>
      <line x1="4" y1="21" x2="4" y2="14" />
      <line x1="4" y1="10" x2="4" y2="3" />
      <line x1="12" y1="21" x2="12" y2="12" />
      <line x1="12" y1="8" x2="12" y2="3" />
      <line x1="20" y1="21" x2="20" y2="16" />
      <line x1="20" y1="12" x2="20" y2="3" />
    </svg>
  );
}

function IconDatabase({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={stroke} className={className} aria-hidden>
      <ellipse cx="12" cy="5" rx="9" ry="3" />
      <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
      <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
    </svg>
  );
}

function IconFileDown({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={stroke} className={className} aria-hidden>
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <path d="M12 18v-6M9 15l3 3 3-3" />
    </svg>
  );
}

function IconActivity({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={stroke} className={className} aria-hidden>
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
    </svg>
  );
}

function IconShield({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={stroke} className={className} aria-hidden>
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    </svg>
  );
}

function IconDoorSmall({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={stroke} className={className} aria-hidden>
      <path d="M4 21V5a2 2 0 0 1 2-2h8v18H4z" />
      <path d="M14 3h6v18h-6" opacity={0.4} />
      <circle cx="12" cy="12" r="1" fill="currentColor" stroke="none" />
    </svg>
  );
}

export function AuditActionIcon({ action, className = "w-4 h-4" }: { action: string; className?: string }) {
  const fill = auditActionFill[action] ?? "#94a3b8";
  let glyph: ReactNode;
  switch (action) {
    case "ACCESS_GRANTED":
      glyph = <IconKey className={className} />;
      break;
    case "ACCESS_DENIED":
      glyph = <IconBan className={className} />;
      break;
    case "FACE_REGISTRATION":
      glyph = <IconUserPlus className={className} />;
      break;
    case "THREAT_CREATED":
    case "THREAT_RESOLVED":
      glyph = <IconShield className={className} />;
      break;
    case "ANOMALY_DETECTED":
      glyph = <IconActivity className={className} />;
      break;
    case "DATA_EXPORT":
      glyph = <IconFileDown className={className} />;
      break;
    case "SYSTEM_CONFIG_CHANGE":
      glyph = <IconSliders className={className} />;
      break;
    case "BACKUP_COMPLETED":
      glyph = <IconDatabase className={className} />;
      break;
    default:
      glyph = <IconDoorSmall className={className} />;
  }
  return (
    <span
      className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-xl ring-1 ring-black/[0.04]"
      style={{ backgroundColor: `${fill}33`, color: fill }}
    >
      {glyph}
    </span>
  );
}
