"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { getAuditLog, AuditEntry } from "@/lib/api";
import { exportAuditTrailCsv } from "@/lib/reportExport";
import { DEMO_AUDIT, demoFallbackEnabled, emptyOrDemo } from "@/lib/demoData";
import AuditTable from "@/components/AuditTable";
import PageHero from "@/components/PageHero";
import ComplianceActionChart from "@/components/compliance/ComplianceActionChart";
import { IconAuditTrail, IconDownload } from "@/components/icons/DoorIcons";

export default function CompliancePage() {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [limit, setLimit] = useState(50);
  const [usingDemo, setUsingDemo] = useState(false);
  const [exporting, setExporting] = useState(false);

  const load = async (l: number) => {
    setLoading(true);
    const data = await getAuditLog(l);
    const merged = emptyOrDemo(data?.audit_log, DEMO_AUDIT);
    setUsingDemo((data?.audit_log?.length ?? 0) === 0 && demoFallbackEnabled());
    setEntries(merged.slice(0, Math.min(l, merged.length)));
    setLoading(false);
  };

  useEffect(() => {
    load(limit);
  }, [limit]); // eslint-disable-line

  const stats = useMemo(() => {
    const ok = entries.filter((e) => e.result === "success").length;
    const fail = entries.length - ok;
    const access = entries.filter((e) => e.action === "ACCESS_GRANTED" || e.action === "ACCESS_DENIED").length;
    return { ok, fail, access, total: entries.length };
  }, [entries]);

  const handleExportCsv = useCallback(async () => {
    setExporting(true);
    const params = new URLSearchParams({
      format: "csv",
      limit: String(Math.max(limit, 500)),
    });
    try {
      await exportAuditTrailCsv(`/api/compliance/audit?${params.toString()}`, entries);
    } finally {
      setExporting(false);
    }
  }, [entries, limit]);

  return (
    <div className="space-y-6">
      <PageHero
        tone="indigo"
        eyebrow="Governance · Smart entrance"
        title="Audit trail"
        icon={<IconAuditTrail className="w-6 h-6" />}
        description={
          <>
            Tamper-evident record of door access, enrollments, exports, and configuration — structured for PIPEDA & GDPR
            reviews.
          </>
        }
        aside={
          <div className="flex flex-wrap gap-2">
            {usingDemo && (
              <span className="bg-amber-50/95 text-amber-900 text-xs font-semibold px-2.5 py-1 rounded-full border border-amber-200/80">
                Demo data
              </span>
            )}
            <button
              type="button"
              onClick={handleExportCsv}
              disabled={exporting}
              className="inline-flex items-center gap-2 bg-white/95 border border-violet-200/80 text-violet-900 text-sm font-semibold px-4 py-2 rounded-xl hover:bg-violet-50/80 transition-colors shadow-sm disabled:opacity-60 disabled:pointer-events-none"
            >
              <IconDownload className="w-4 h-4" />
              {exporting ? "Preparing…" : "Export CSV"}
            </button>
          </div>
        }
      />

      {!loading && entries.length > 0 && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <div className="rounded-2xl border border-emerald-100/80 bg-emerald-50/40 px-4 py-3">
            <p className="text-[11px] font-semibold text-emerald-900 uppercase tracking-wide">Successful steps</p>
            <p className="text-2xl font-bold text-emerald-800 tabular-nums mt-0.5">{stats.ok}</p>
          </div>
          <div className="rounded-2xl border border-rose-100/80 bg-rose-50/35 px-4 py-3">
            <p className="text-[11px] font-semibold text-rose-900 uppercase tracking-wide">Failed / denied</p>
            <p className="text-2xl font-bold text-rose-800 tabular-nums mt-0.5">{stats.fail}</p>
          </div>
          <div className="rounded-2xl border border-teal-100/80 bg-teal-50/30 px-4 py-3">
            <p className="text-[11px] font-semibold text-teal-900 uppercase tracking-wide">Door access rows</p>
            <p className="text-2xl font-bold text-teal-900 tabular-nums mt-0.5">{stats.access}</p>
            <p className="text-[10px] text-slate-500 mt-1">Granted + denied events</p>
          </div>
          <div className="rounded-2xl border border-slate-100 bg-slate-50/50 px-4 py-3">
            <p className="text-[11px] font-semibold text-slate-600 uppercase tracking-wide">Events loaded</p>
            <p className="text-2xl font-bold text-slate-800 tabular-nums mt-0.5">{stats.total}</p>
          </div>
        </div>
      )}

      <ComplianceActionChart entries={entries} />

      <AuditTable entries={entries} loading={loading} />

      <button
        type="button"
        onClick={() => setLimit((p) => p + 50)}
        className="inline-flex items-center gap-2 bg-white border border-violet-200/70 text-violet-900 text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-violet-50/60 transition-colors shadow-sm"
      >
        Load more
      </button>
    </div>
  );
}
