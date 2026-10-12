"use client";

/**
 * frontend/web/app/trust-radar/page.tsx
 * Module 3 from legacy-streamlit-mvp/app.py:
 * 🛡️ Supplier Trust Radar (SME Guardian) — Crowdsourced memo price consistency & Red Flag Scam Alerts.
 */

import React, { useEffect, useState } from "react";
import { Search, ShieldCheck, AlertOctagon } from "lucide-react";
import { fetchSupplierTrustRadar } from "../../lib/api";

export default function SupplierTrustRadarPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [radarData, setRadarData] = useState<Awaited<ReturnType<typeof fetchSupplierTrustRadar>> | null>(null);

  useEffect(() => {
    fetchSupplierTrustRadar("").then(setRadarData);
  }, []);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    const res = await fetchSupplierTrustRadar(searchQuery);
    setRadarData(res);
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-surface-border pb-4">
        <h1 className="text-2xl font-bold font-mono text-[#eaecef]">
          🛡️ Supplier Trust Radar (SME Guardian)
        </h1>
        <p className="text-sm text-wolf-muted mt-1">
          We use AI and crowdsourced memo analysis to detect honest suppliers and flag market manipulators based on price consistency.
        </p>
      </div>

      {/* Search Bar */}
      <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="h-4 w-4 text-wolf-muted absolute left-3.5 top-3" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="🔍 Search Wholesaler Name or Location (e.g., 'Multiplan Shop 302')"
            className="w-full pl-10 pr-4 py-2.5 rounded-lg bg-surface border border-surface-border text-xs font-mono text-[#eaecef] focus:border-wolf-gold outline-none"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="px-6 py-2.5 bg-wolf-gold hover:bg-[#dfaa05] text-[#0b0e11] font-mono font-bold text-xs rounded-lg transition-colors"
        >
          {loading ? "Analyzing Memos..." : "Search Radar"}
        </button>
      </form>

      {radarData?.is_simulated && (
        <div className="p-3 rounded-lg bg-surface border border-wolf-gold/30 text-xs font-mono text-wolf-gold">
          💡 Note: Displaying crowdsourced & simulated market trust scores synchronized with your scanner database.
        </div>
      )}

      {/* Top Verified Titans */}
      <div className="space-y-3">
        <h2 className="text-sm font-mono font-bold text-[#eaecef] uppercase flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-wolf-green" />
          🏆 Top Verified Titans (Safe to Trade)
        </h2>

        <div className="bg-surface border border-surface-border rounded-lg overflow-hidden">
          <table className="w-full text-xs font-mono">
            <thead className="bg-[#0b0e11] text-wolf-muted border-b border-surface-border">
              <tr>
                <th className="p-3.5 text-left">Wholesaler / Importer</th>
                <th className="p-3.5 text-left">Dominant Product</th>
                <th className="p-3.5 text-left">Trust Score</th>
                <th className="p-3.5 text-left">AI Remarks</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-border">
              {(radarData?.verified_titans || []).map((row, idx) => (
                <tr key={idx} className="hover:bg-surface-hover/40">
                  <td className="p-3.5 font-bold text-[#eaecef]">{row.wholesaler_importer}</td>
                  <td className="p-3.5 text-wolf-gold">{row.dominant_product}</td>
                  <td className="p-3.5 font-bold">{row.trust_score}</td>
                  <td className="p-3.5 text-wolf-muted">{row.ai_remarks}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Red Flag / Scam Alerts */}
      <div className="space-y-3 pt-2">
        <h2 className="text-sm font-mono font-bold text-wolf-red uppercase flex items-center gap-2">
          <AlertOctagon className="h-4 w-4 text-wolf-red" />
          🚨 Red Flag / Scam Alerts
        </h2>
        {(radarData?.red_flag_alerts || []).map((alert, idx) => (
          <div
            key={idx}
            className="p-4 rounded-lg bg-wolf-red/10 border border-wolf-red/40 text-xs font-mono text-[#eaecef]"
          >
            <strong className="text-wolf-red">{alert.supplier}</strong> — {alert.message}
          </div>
        ))}
      </div>
    </div>
  );
}

