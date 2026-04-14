"use client";

import { useEffect, useMemo, useState } from "react";
import { getAccessLogs, getUsers, deleteUser, AccessLog, User } from "@/lib/api";
import { DEMO_LOGS, DEMO_USERS, emptyOrDemo } from "@/lib/demoData";
import AccessLogsTable from "@/components/AccessLogsTable";
import PageHero from "@/components/PageHero";
import LogsDoorSummary from "@/components/logs/LogsDoorSummary";
import { IconClipboard, IconDoorPanel } from "@/components/icons/DoorIcons";

function enrolledRoleLabel(role: string | undefined): string {
  const r = (role ?? "resident").trim().toLowerCase();
  if (r === "staff") return "Staff";
  if (r === "resident") return "Resident";
  if (!r) return "Resident";
  return r.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function enrolledRolePillClass(role: string | undefined): string {
  const r = (role ?? "resident").trim().toLowerCase();
  if (r === "staff") return "bg-sky-50 text-sky-900 ring-1 ring-inset ring-sky-200/80";
  if (r === "resident") return "bg-teal-50 text-teal-900 ring-1 ring-inset ring-teal-200/70";
  return "bg-slate-100 text-slate-700 ring-1 ring-inset ring-slate-200/70";
}

export default function LogsPage() {
  const [logs, setLogs] = useState<AccessLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [limit, setLimit] = useState(20);
  const [usingDemo, setUsingDemo] = useState(false);
  const [showAll, setShowAll] = useState(false);
  const [peopleModalOpen, setPeopleModalOpen] = useState(false);
  const [registeredUsers, setRegisteredUsers] = useState<User[]>([]);
  const [usersLoading, setUsersLoading] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState<{ user_id: string; name: string } | null>(null);
  const [deleting, setDeleting] = useState(false);

  const load = async (l: number) => {
    setLoading(true);
    const data = await getAccessLogs(l);

    const hasRealPeople = data?.logs.some((log) => log.person_id != null && log.name != null);

    if (hasRealPeople) {
      setLogs(data!.logs);
      setUsingDemo(false);
    } else {
      setLogs(showAll ? DEMO_LOGS : DEMO_LOGS.slice(0, l));
      setUsingDemo(true);
    }
    setLoading(false);
  };

  useEffect(() => {
    load(limit);
  }, [limit, showAll]); // eslint-disable-line

  useEffect(() => {
    getUsers().then((data) => setRegisteredUsers(emptyOrDemo(data?.users, DEMO_USERS)));
  }, []);

  const openPeopleModal = async () => {
    setPeopleModalOpen(true);
    setConfirmDelete(null);
    setUsersLoading(true);
    const data = await getUsers();
    setRegisteredUsers(emptyOrDemo(data?.users, DEMO_USERS));
    setUsersLoading(false);
  };

  const handleConfirmRemove = async () => {
    if (!confirmDelete) return;
    setDeleting(true);
    const ok = await deleteUser(confirmDelete.user_id);
    setDeleting(false);
    if (ok) {
      setConfirmDelete(null);
      const data = await getUsers();
      setRegisteredUsers(data?.users ?? []);
    }
  };

  const displayed = logs;
  const registeredCount = registeredUsers.length;
  const hasMore = usingDemo ? displayed.length < DEMO_LOGS.length : displayed.length === limit;

  const successRate = useMemo(() => {
    if (displayed.length === 0) return null;
    const ok = displayed.filter((l) => l.status === "success").length;
    return Math.round((ok / displayed.length) * 100);
  }, [displayed]);

  return (
    <div className="space-y-6">
      <PageHero
        tone="teal"
        eyebrow="Face panel · Access memory"
        title="Access logs"
        icon={<IconDoorPanel className="w-6 h-6" />}
        description={
          <>
            Every verified entry and exit at the smart entrance — who approached, which way they crossed, and whether the
            door released.
          </>
        }
        aside={
          <div className="flex flex-wrap gap-2">
            {usingDemo && (
              <span className="bg-amber-50/95 text-amber-900 text-xs font-semibold px-2.5 py-1 rounded-full border border-amber-200/80">
                Demo data
              </span>
            )}
            <span className="bg-white/95 text-slate-700 text-sm font-medium px-3 py-1.5 rounded-full border border-slate-200/80">
              {displayed.length} in view
            </span>
          </div>
        }
      />

      {!loading && displayed.length > 0 && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <div className="rounded-2xl border border-emerald-100/80 bg-gradient-to-br from-emerald-50/90 to-white px-4 py-3 flex items-center justify-between gap-2 ring-1 ring-emerald-50/60">
              <div>
                <span className="text-[11px] text-emerald-800/90 font-semibold uppercase tracking-wide">Granted</span>
                <p className="text-xs text-slate-500 mt-0.5">Door released after face match</p>
              </div>
              <span className="text-2xl font-bold text-emerald-700 tabular-nums">
                {displayed.filter((l) => l.status === "success").length}
              </span>
            </div>
            <div className="rounded-2xl border border-rose-100/80 bg-gradient-to-br from-rose-50/80 to-white px-4 py-3 flex items-center justify-between gap-2">
              <div>
                <span className="text-[11px] text-rose-800/90 font-semibold uppercase tracking-wide">Blocked</span>
                <p className="text-xs text-slate-500 mt-0.5">Failed or unknown at panel</p>
              </div>
              <span className="text-2xl font-bold text-rose-600 tabular-nums">
                {displayed.filter((l) => l.status !== "success").length}
              </span>
            </div>
            <button
              type="button"
              onClick={openPeopleModal}
              className="rounded-2xl border border-sky-100/90 bg-white/95 px-4 py-3 flex items-center justify-between gap-2 text-left hover:bg-sky-50/50 transition-colors ring-1 ring-sky-50/50"
            >
              <div>
                <span className="text-[11px] text-sky-900/80 font-semibold uppercase tracking-wide">Enrolled faces</span>
                <p className="text-xs text-slate-500 mt-0.5">Residents & staff on file</p>
              </div>
              <span className="text-2xl font-bold text-sky-900 tabular-nums">{registeredCount}</span>
            </button>
            <div className="rounded-2xl border border-slate-100 bg-slate-50/50 px-4 py-3 flex items-center justify-between gap-2">
              <div>
                <span className="text-[11px] text-slate-600 font-semibold uppercase tracking-wide">Match rate</span>
                <p className="text-xs text-slate-500 mt-0.5">Success / rows in list</p>
              </div>
              <span className="text-2xl font-bold text-slate-800 tabular-nums">{successRate ?? "—"}%</span>
            </div>
          </div>

          <LogsDoorSummary logs={displayed} />
        </>
      )}

      {peopleModalOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
          onClick={() => setPeopleModalOpen(false)}
        >
          <div
            className="bg-white rounded-2xl shadow-xl max-w-lg w-full max-h-[80vh] overflow-hidden ring-1 ring-slate-200/80"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between bg-gradient-to-r from-teal-50/40 to-white">
              <div className="flex items-center gap-2">
                <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-teal-100/70 text-teal-700">
                  <IconClipboard className="w-5 h-5" />
                </span>
                <h2 className="text-lg font-semibold text-slate-800">Enrolled people</h2>
              </div>
              <button
                type="button"
                onClick={() => setPeopleModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-100"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
            <div className="p-5 overflow-y-auto max-h-[60vh]">
              {confirmDelete && (
                <div className="mb-4 p-3 rounded-xl bg-amber-50 border border-amber-200">
                  <p className="text-sm text-slate-700 mb-3">
                    Remove <strong>{confirmDelete.name}</strong> from enrolled faces? They will not be recognized until
                    re-registered.
                  </p>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => setConfirmDelete(null)}
                      className="px-3 py-1.5 text-sm font-medium text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50"
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      onClick={handleConfirmRemove}
                      disabled={deleting}
                      className="px-3 py-1.5 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 disabled:opacity-50"
                    >
                      {deleting ? "Removing…" : "Remove"}
                    </button>
                  </div>
                </div>
              )}
              {usersLoading ? (
                <p className="text-sm text-slate-500">Loading…</p>
              ) : registeredUsers.length === 0 ? (
                <p className="text-sm text-slate-500">No enrolled people yet.</p>
              ) : (
                <div>
                  <div className="flex gap-2 items-center pb-2.5 mb-0.5 border-b border-slate-100 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                    <span className="w-[9.5rem] sm:w-[11rem] shrink-0 pl-0.5">Name</span>
                    <div className="flex-1 flex justify-between items-center gap-3 min-w-0 pr-1">
                      <span>Role</span>
                      <span className="font-mono font-normal tracking-normal normal-case text-slate-400">
                        Person ID
                      </span>
                    </div>
                    <span className="w-9 shrink-0" />
                  </div>
                  <ul className="divide-y divide-slate-100">
                    {registeredUsers.map((u) => (
                      <li key={u.user_id} className="flex gap-2 items-center py-2.5 first:pt-1">
                        <span className="w-[9.5rem] sm:w-[11rem] shrink-0 min-w-0 truncate font-medium text-slate-800 pl-0.5">
                          {u.name}
                        </span>
                        <div className="flex-1 flex justify-between items-center gap-3 min-w-0 pl-1 pr-1 border-l border-slate-100/90">
                          <span
                            className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-semibold ${enrolledRolePillClass(u.role)}`}
                          >
                            {enrolledRoleLabel(u.role)}
                          </span>
                          <span className="text-sm text-slate-600 font-mono tabular-nums shrink-0 tracking-tight">
                            {u.display_id}
                          </span>
                        </div>
                        <button
                          type="button"
                          onClick={() => setConfirmDelete({ user_id: u.user_id, name: u.name })}
                          className="shrink-0 w-9 h-9 flex items-center justify-center text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                          title="Remove enrollment"
                        >
                          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                            <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" />
                            <line x1="10" y1="11" x2="10" y2="17" />
                            <line x1="14" y1="11" x2="14" y2="17" />
                          </svg>
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      <AccessLogsTable logs={displayed} loading={loading} />

      {hasMore && (
        <button
          type="button"
          onClick={() => {
            if (usingDemo) setShowAll(true);
            else setLimit((p) => p + 30);
          }}
          className="inline-flex items-center gap-2 bg-white border border-teal-200/80 text-teal-900 text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-teal-50/80 transition-colors shadow-sm"
        >
          Load more
          <span className="text-teal-600/70 text-xs font-medium">
            ({usingDemo ? DEMO_LOGS.length - displayed.length : "30"} more)
          </span>
        </button>
      )}
    </div>
  );
}
