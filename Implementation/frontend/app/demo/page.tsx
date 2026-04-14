"use client";

import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import PageHero from "@/components/PageHero";
import {
  IconCameraDoor,
  IconFaceScan,
  IconFallMotion,
  IconObjectFrame,
  IconUser,
} from "@/components/icons/DoorIcons";
import { getDemoTools, startDemoTool, startDemoToolWithPayload, stopDemoTool, type DemoToolStatus } from "@/lib/api";

const toolMeta: Record<string, { title: string; tone: string; icon: ReactNode; summary: string }> = {
  "face-register": {
    title: "Register Face",
    tone: "teal",
    icon: <IconUser className="w-5 h-5" />,
    summary: "Opens capture UI for a sample person (`demo_user`) and saves photos in samples.",
  },
  "face-test": {
    title: "Face Detection Interface",
    tone: "sky",
    icon: <IconFaceScan className="w-5 h-5" />,
    summary: "Runs live face recognition UI using `/api/recognize` in continuous mode.",
  },
  "fall-test": {
    title: "Fall Detection Interface",
    tone: "rose",
    icon: <IconFallMotion className="w-5 h-5" />,
    summary: "Runs live fall detection camera interface (rules mode by default).",
  },
  "object-test": {
    title: "Object Detection Interface",
    tone: "violet",
    icon: <IconObjectFrame className="w-5 h-5" />,
    summary: "Runs live object detection UI with YOLO26L.",
  },
};

function statusPill(running: boolean) {
  return running
    ? "bg-emerald-50 text-emerald-800 border border-emerald-200/80"
    : "bg-slate-50 text-slate-600 border border-slate-200/80";
}

export default function DemoPage() {
  const [tools, setTools] = useState<DemoToolStatus[]>([]);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(true);
  const [personId, setPersonId] = useState("");
  const [personName, setPersonName] = useState("");
  const [role, setRole] = useState<"resident" | "caregiver">("resident");

  const refresh = useCallback(async () => {
    setRefreshing(true);
    const data = await getDemoTools();
    setTools(data?.tools ?? []);
    setRefreshing(false);
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 2500);
    return () => clearInterval(id);
  }, [refresh]);

  const anyRunning = useMemo(() => tools.some((t) => t.running), [tools]);

  const handleStart = useCallback(async (id: string) => {
    setBusyId(id);
    if (id === "face-register") {
      const cleanId = personId.trim();
      const cleanName = personName.trim();
      if (!cleanId || !cleanName) {
        setBusyId(null);
        return;
      }
      await startDemoToolWithPayload(id, {
        person_id: cleanId,
        name: cleanName,
        role,
        photos: 40,
      });
    } else {
      await startDemoTool(id);
    }
    await refresh();
    setBusyId(null);
  }, [personId, personName, refresh, role]);

  const handleStop = useCallback(async (id: string) => {
    setBusyId(id);
    await stopDemoTool(id);
    await refresh();
    setBusyId(null);
  }, [refresh]);

  return (
    <div className="space-y-6">
      <PageHero
        tone="teal"
        eyebrow="Demo Lab · Live Interfaces"
        title="Demo Control Center"
        icon={<IconCameraDoor className="w-6 h-6" />}
        description={
          <>
            Launch and stop demo camera interfaces from one page: face registration, face detection, fall detection, and
            object detection. Styling follows the same dashboard theme.
          </>
        }
        aside={
          <div className="flex flex-wrap gap-2 items-center">
            <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${statusPill(anyRunning)}`}>
              {anyRunning ? "Interface running" : "All interfaces idle"}
            </span>
            <button
              type="button"
              onClick={refresh}
              className="text-xs font-semibold px-3 py-1.5 rounded-xl border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 shadow-sm"
            >
              {refreshing ? "Refreshing..." : "Refresh"}
            </button>
          </div>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {tools.map((tool) => {
          const meta = toolMeta[tool.id] ?? {
            title: tool.label,
            tone: "teal",
            icon: <IconCameraDoor className="w-5 h-5" />,
            summary: "Demo interface launcher",
          };
          const running = tool.running;
          const busy = busyId === tool.id;
          const accentClass =
            meta.tone === "rose"
              ? "from-rose-50/70 to-white border-rose-100/80"
              : meta.tone === "violet"
                ? "from-violet-50/70 to-white border-violet-100/80"
                : meta.tone === "sky"
                  ? "from-sky-50/70 to-white border-sky-100/80"
                  : "from-teal-50/70 to-white border-teal-100/80";

          return (
            <section key={tool.id} className={`rounded-2xl border bg-gradient-to-br ${accentClass} p-5 shadow-sm`}>
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-3 min-w-0">
                  <span className="mt-0.5 h-9 w-9 rounded-xl bg-white border border-slate-200/80 text-slate-700 flex items-center justify-center">
                    {meta.icon}
                  </span>
                  <div>
                    <h2 className="text-base font-semibold text-slate-900">{meta.title}</h2>
                    <p className="text-xs text-slate-600 mt-1 leading-relaxed">{meta.summary}</p>
                  </div>
                </div>
                <span className={`text-[11px] font-semibold px-2.5 py-1 rounded-full ${statusPill(running)}`}>
                  {running ? `Running${tool.pid ? ` · PID ${tool.pid}` : ""}` : "Stopped"}
                </span>
              </div>

              <div className="mt-4 rounded-xl bg-slate-900/95 text-slate-100 text-[11px] px-3 py-2 font-mono overflow-x-auto">
                {tool.command}
              </div>

              {tool.id === "face-register" && (
                <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-2">
                  <input
                    value={personId}
                    onChange={(e) => setPersonId(e.target.value)}
                    placeholder="Person ID (e.g. resident_001)"
                    className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800"
                  />
                  <input
                    value={personName}
                    onChange={(e) => setPersonName(e.target.value)}
                    placeholder="Name (e.g. John Doe)"
                    className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800"
                  />
                  <div className="sm:col-span-2">
                    <label className="text-xs text-slate-500 mr-2">Role</label>
                    <select
                      value={role}
                      onChange={(e) => setRole(e.target.value as "resident" | "caregiver")}
                      className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800"
                    >
                      <option value="resident">Resident</option>
                      <option value="caregiver">Caregiver</option>
                    </select>
                    <span className="ml-2 text-xs text-slate-500">Photo target: 40</span>
                  </div>
                </div>
              )}

              <div className="mt-4 flex items-center gap-2">
                <button
                  type="button"
                  disabled={busy || running || (tool.id === "face-register" && (!personId.trim() || !personName.trim()))}
                  onClick={() => handleStart(tool.id)}
                  className="text-sm font-semibold px-3.5 py-2 rounded-xl bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-50 disabled:pointer-events-none"
                >
                  {busy ? "Starting..." : "Start"}
                </button>
                <button
                  type="button"
                  disabled={busy || !running}
                  onClick={() => handleStop(tool.id)}
                  className="text-sm font-semibold px-3.5 py-2 rounded-xl border border-rose-200/90 text-rose-800 bg-rose-50/80 hover:bg-rose-100 disabled:opacity-50 disabled:pointer-events-none"
                >
                  {busy ? "Stopping..." : "Stop"}
                </button>
              </div>
            </section>
          );
        })}
      </div>
    </div>
  );
}

