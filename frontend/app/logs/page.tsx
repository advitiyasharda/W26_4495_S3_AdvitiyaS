"use client";

import { useEffect, useState } from "react";
import { getAccessLogs, getUsers, deleteUser, AccessLog, User } from "@/lib/api";
import { DEMO_LOGS } from "@/lib/demoData";
import AccessLogsTable from "@/components/AccessLogsTable";

export default function LogsPage() {
  const [logs, setLogs]           = useState<AccessLog[]>([]);
  const [loading, setLoading]     = useState(true);
  const [limit, setLimit]         = useState(20);
  const [usingDemo, setUsingDemo] = useState(false);
  const [showAll, setShowAll]     = useState(false);
  const [peopleModalOpen, setPeopleModalOpen] = useState(false);
  const [registeredUsers, setRegisteredUsers] = useState<User[]>([]);
  const [usersLoading, setUsersLoading] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState<{ user_id: string; name: string } | null>(null);
  const [deleting, setDeleting] = useState(false);

  const load = async (l: number) => {
    setLoading(true);
    const data = await getAccessLogs(l);

    // Use real data only when at least one record has a known person
    // Use != null (loose) to catch both null and undefined (field name mismatches)
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

  useEffect(() => { load(limit); }, [limit, showAll]); // eslint-disable-line

  // Load registered people so the count matches the modal list
  useEffect(() => {
    getUsers().then((data) => setRegisteredUsers(data?.users ?? []));
  }, []);

  const openPeopleModal = async () => {
    setPeopleModalOpen(true);
    setConfirmDelete(null);
    setUsersLoading(true);
    const data = await getUsers();
    setRegisteredUsers(data?.users ?? []);
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
  const hasMore   = usingDemo
    ? displayed.length < DEMO_LOGS.length
    : displayed.length === limit;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Access Logs</h1>
          <div className="flex items-center gap-2 mt-0.5">
            <p className="text-sm text-slate-400">Full audit trail of all door access events</p>
            {usingDemo && (
              <span className="bg-amber-50 text-amber-600 text-xs font-medium px-2.5 py-0.5 rounded-full border border-amber-200">
                Demo data
              </span>
            )}
          </div>
        </div>
        <span className="bg-slate-100 text-slate-600 text-sm font-medium px-3 py-1 rounded-full">
          {displayed.length} records
        </span>
      </div>

      {/* Summary strip */}
      {!loading && displayed.length > 0 && (
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-emerald-50 rounded-xl px-4 py-3 flex items-center justify-between">
            <span className="text-xs text-slate-500 font-medium">Successful</span>
            <span className="text-xl font-bold text-emerald-600">
              {displayed.filter((l) => l.status === "success").length}
            </span>
          </div>
          <div className="bg-red-50 rounded-xl px-4 py-3 flex items-center justify-between">
            <span className="text-xs text-slate-500 font-medium">Failed</span>
            <span className="text-xl font-bold text-red-500">
              {displayed.filter((l) => l.status !== "success").length}
            </span>
          </div>
          <button
            type="button"
            onClick={openPeopleModal}
            className="bg-slate-50 rounded-xl px-4 py-3 flex items-center justify-between text-left hover:bg-slate-100 transition-colors cursor-pointer border border-transparent hover:border-slate-200"
          >
            <span className="text-xs text-slate-500 font-medium">Registered People</span>
            <span className="text-xl font-bold text-slate-700">{registeredCount}</span>
          </button>
        </div>
      )}

      {/* Registered people modal */}
      {peopleModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" onClick={() => setPeopleModalOpen(false)}>
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full max-h-[80vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
            <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-800">Registered People</h2>
              <button type="button" onClick={() => setPeopleModalOpen(false)} className="text-slate-400 hover:text-slate-600 p-1">
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </button>
            </div>
            <div className="p-5 overflow-y-auto max-h-[60vh]">
              {confirmDelete && (
                <div className="mb-4 p-3 rounded-lg bg-amber-50 border border-amber-200">
                  <p className="text-sm text-slate-700 mb-3">
                    Are you sure you want to remove <strong>{confirmDelete.name}</strong> from registered people?
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
                <p className="text-sm text-slate-500">No registered people yet.</p>
              ) : (
                <ul className="space-y-2">
                  {registeredUsers.map((u) => (
                    <li key={u.user_id} className="flex items-center justify-between py-2 border-b border-slate-50 last:border-0 gap-2">
                      <span className="font-medium text-slate-800">{u.name}</span>
                      <span className="text-sm text-slate-500 font-mono shrink-0">{u.display_id}</span>
                      <button
                        type="button"
                        onClick={() => setConfirmDelete({ user_id: u.user_id, name: u.name })}
                        className="shrink-0 p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                        title="Remove from registered people"
                      >
                        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}><path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Table */}
      <AccessLogsTable logs={displayed} loading={loading} />

      {/* Load more */}
      {hasMore && (
        <button
          onClick={() => {
            if (usingDemo) setShowAll(true);
            else setLimit((p) => p + 30);
          }}
          className="flex items-center gap-2 bg-white border border-slate-200 text-slate-600 text-sm font-medium px-4 py-2 rounded-lg hover:bg-slate-50 transition-colors shadow-sm"
        >
          Load more
          <span className="text-slate-400 text-xs">
            ({usingDemo ? DEMO_LOGS.length - displayed.length : "30"} remaining)
          </span>
        </button>
      )}
    </div>
  );
}
