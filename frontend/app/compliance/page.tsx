"use client";

import { useEffect, useState } from "react";
import { getAuditLog, AuditEntry } from "@/lib/api";
import { DEMO_AUDIT } from "@/lib/demoData";
import AuditTable from "@/components/AuditTable";

export default function CompliancePage() {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [limit, setLimit]     = useState(50);
  const [usingDemo, setUsingDemo] = useState(false);

  const load = async (l: number) => {
    setLoading(true);
    const data = await getAuditLog(l);
    if (data && data.audit_log.length > 0) {
      setEntries(data.audit_log);
      setUsingDemo(false);
    } else {
      setEntries(DEMO_AUDIT.slice(0, l));
      setUsingDemo(true);
    }
    setLoading(false);
  };

  useEffect(() => { load(limit); }, [limit]); // eslint-disable-line

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Audit Trail</h1>
          <p className="text-sm text-slate-400 mt-0.5">PIPEDA &amp; GDPR compliance audit log</p>
          {usingDemo && (
            <span className="inline-block mt-1.5 bg-amber-50 text-amber-600 text-xs font-medium px-2.5 py-0.5 rounded-full border border-amber-200">
              Demo data
            </span>
          )}
        </div>
        <a
          href="/api/compliance/audit?format=csv"
          className="flex items-center gap-2 bg-white border border-slate-200 text-slate-600 text-sm font-medium px-4 py-2 rounded-lg hover:bg-slate-50 transition-colors shadow-sm"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} className="w-4 h-4">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
          Export CSV
        </a>
      </div>

      <AuditTable entries={entries} loading={loading} />

      <button
        onClick={() => setLimit((p) => p + 50)}
        className="flex items-center gap-2 bg-white border border-slate-200 text-slate-600 text-sm font-medium px-4 py-2 rounded-lg hover:bg-slate-50 transition-colors shadow-sm"
      >
        Load more
      </button>
    </div>
  );
}
