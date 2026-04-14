"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import {
  IconAuditTrail,
  IconBell,
  IconChevronLeft,
  IconChevronRight,
  IconClipboard,
  IconDashboard,
  IconDoorPanel,
  IconFaceScan,
  IconFallMotion,
  IconSearchObject,
  IconUser,
} from "@/components/icons/DoorIcons";

const icons = {
  dashboard: <IconDashboard className="w-5 h-5" />,
  alerts: <IconBell className="w-5 h-5" />,
  falls: <IconFallMotion className="w-5 h-5" />,
  objects: <IconSearchObject className="w-5 h-5" />,
  logs: <IconClipboard className="w-5 h-5" />,
  compliance: <IconAuditTrail className="w-5 h-5" />,
  demo: <IconFaceScan className="w-5 h-5" />,
  chevronRight: <IconChevronRight className="w-4 h-4" />,
  chevronLeft: <IconChevronLeft className="w-4 h-4" />,
  door: <IconDoorPanel className="w-6 h-6" />,
  user: <IconUser className="w-8 h-8" />,
};

type NavAccent = "teal" | "amber" | "rose" | "violet" | "sky" | "indigo";

const navAccent = {
  active: {
    teal: "bg-teal-50/90 text-teal-900 ring-1 ring-teal-200/50",
    amber: "bg-amber-50/90 text-amber-950 ring-1 ring-amber-200/50",
    rose: "bg-rose-50/90 text-rose-950 ring-1 ring-rose-200/50",
    violet: "bg-violet-50/90 text-violet-950 ring-1 ring-violet-200/50",
    sky: "bg-sky-50/90 text-sky-950 ring-1 ring-sky-200/50",
    indigo: "bg-indigo-50/90 text-indigo-950 ring-1 ring-indigo-200/50",
  },
  idle: {
    teal: "text-slate-500 hover:bg-teal-50/50 hover:text-teal-900",
    amber: "text-slate-500 hover:bg-amber-50/45 hover:text-amber-950",
    rose: "text-slate-500 hover:bg-rose-50/45 hover:text-rose-950",
    violet: "text-slate-500 hover:bg-violet-50/45 hover:text-violet-950",
    sky: "text-slate-500 hover:bg-sky-50/45 hover:text-sky-950",
    indigo: "text-slate-500 hover:bg-indigo-50/45 hover:text-indigo-950",
  },
  iconActive: {
    teal: "text-teal-600",
    amber: "text-amber-600",
    rose: "text-rose-600",
    violet: "text-violet-600",
    sky: "text-sky-600",
    indigo: "text-indigo-600",
  },
  iconIdle: {
    teal: "text-teal-500/70 group-hover:text-teal-700",
    amber: "text-amber-500/70 group-hover:text-amber-700",
    rose: "text-rose-500/70 group-hover:text-rose-700",
    violet: "text-violet-500/70 group-hover:text-violet-700",
    sky: "text-sky-500/70 group-hover:text-sky-700",
    indigo: "text-indigo-500/70 group-hover:text-indigo-700",
  },
} as const;

const sectionLabelTint: Record<string, string> = {
  MONITORING: "text-teal-600/55",
  SECURITY: "text-amber-700/45",
  COMPLIANCE: "text-indigo-600/50",
  DEMO: "text-violet-600/50",
};

const sections: {
  label: string;
  /** Thin rule below this section (e.g. after Dashboard, after Security group). */
  separatorAfter?: boolean;
  items: { href: string; label: string; icon: keyof typeof icons; accent: NavAccent }[];
}[] = [
  {
    label: "MONITORING",
    separatorAfter: true,
    items: [{ href: "/", label: "Dashboard", icon: "dashboard", accent: "teal" }],
  },
  {
    label: "SECURITY",
    separatorAfter: true,
    items: [
      { href: "/alerts", label: "Alerts", icon: "alerts", accent: "amber" },
      { href: "/falls", label: "Falls", icon: "falls", accent: "rose" },
      { href: "/objects", label: "Object Detection", icon: "objects", accent: "violet" },
      { href: "/logs", label: "Access Logs", icon: "logs", accent: "sky" },
    ],
  },
  {
    label: "COMPLIANCE",
    separatorAfter: true,
    items: [{ href: "/compliance", label: "Audit Trail", icon: "compliance", accent: "indigo" }],
  },
  {
    label: "DEMO",
    items: [{ href: "/demo", label: "Demo Center", icon: "demo", accent: "violet" }],
  },
];

function NavSeparator() {
  return (
    <div
      className="mx-1 my-2 h-px bg-gradient-to-r from-transparent via-slate-200/90 to-transparent"
      role="separator"
      aria-hidden="true"
    />
  );
}

export default function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(true);

  return (
    <aside
      className={`relative flex flex-col bg-white/70 backdrop-blur-md border-r border-slate-100/80 h-screen sticky top-0 transition-all duration-300 ${
        collapsed ? "w-[68px]" : "w-56"
      }`}
    >
      {/* Logo — always visible; centered when collapsed */}
      <div
        className={`flex items-center gap-3 py-5 border-b border-slate-100/90 ${
          collapsed ? "justify-center px-2" : "px-4"
        }`}
      >
        <div className="flex-shrink-0 w-9 h-9 rounded-xl bg-gradient-to-br from-teal-300/85 via-cyan-300/80 to-violet-200/90 flex items-center justify-center text-white shadow-sm ring-1 ring-teal-200/35">
          {icons.door}
        </div>
        {!collapsed && (
          <div className="min-w-0">
            <span className="font-bold text-slate-800 text-sm leading-tight block">Door Face Panels</span>
            <span className="text-[10px] font-medium text-slate-500 uppercase tracking-wider">Smart entrance</span>
          </div>
        )}
      </div>

      {/* Nav sections */}
      <nav className="flex-1 overflow-y-auto py-4 px-2 space-y-5">
        {sections.map((section) => (
          <div key={section.label}>
            {!collapsed && (
              <p
                className={`text-[10px] font-semibold tracking-widest px-3 mb-1 ${sectionLabelTint[section.label] ?? "text-slate-400"}`}
              >
                {section.label}
              </p>
            )}
            <ul className="space-y-0.5">
              {section.items.map((item) => {
                const active = pathname === item.href;
                const a = item.accent;
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      title={collapsed ? item.label : undefined}
                      className={`group flex items-center gap-3 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                        collapsed ? "justify-center px-2" : "px-3"
                      } ${active ? navAccent.active[a] : navAccent.idle[a]}`}
                    >
                      <span className={active ? navAccent.iconActive[a] : navAccent.iconIdle[a]}>
                        {icons[item.icon]}
                      </span>
                      {!collapsed && <span>{item.label}</span>}
                    </Link>
                  </li>
                );
              })}
            </ul>
            {section.separatorAfter ? <NavSeparator /> : null}
          </div>
        ))}
      </nav>

      {/* User profile */}
      <div className="border-t border-slate-100 p-3">
        <div
          className={`flex items-center gap-3 px-2 py-2 rounded-xl bg-slate-50/80 ${
            collapsed ? "justify-center" : ""
          }`}
        >
          <div className="flex-shrink-0 w-9 h-9 rounded-full bg-white border border-slate-200 flex items-center justify-center text-slate-500">
            {icons.user}
          </div>
          {!collapsed && (
            <div className="min-w-0">
              <p className="text-sm font-medium text-slate-700 truncate">Admin</p>
              <p className="text-xs text-slate-400 truncate">Caregiver Dashboard</p>
              <Link href="/demo" className="text-[11px] font-semibold text-violet-700 hover:underline mt-1 inline-block">
                Open Demo Center
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* Collapse toggle */}
      <button
        type="button"
        aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        onClick={() => setCollapsed((c) => !c)}
        className="absolute -right-3 top-[4.5rem] w-6 h-6 bg-white border border-slate-200 rounded-full flex items-center justify-center text-slate-400 hover:text-slate-700 shadow-sm z-10"
      >
        {collapsed ? icons.chevronRight : icons.chevronLeft}
      </button>
    </aside>
  );
}
