"use client";

/**
 * frontend/web/app/analytics/page.tsx
 * Module 5 from legacy-streamlit-mvp/app.py:
 * 📦 AI Product & Trend Analytics (The Flywheel Engine)
 * Tabs:
 * 1. 📊 My Ledger Analytics (Top Selling Asset, Total Units Sold, Item-wise Market Demand, AI Product Insight)
 * 2. 🌐 Community Trends (National Crowd-Sourced Trends, Price Benchmark: You vs Market)
 * 3. 🔔 Proactive AI Alerts (Trade Wolf Copilot Restock & Capital Liquidity Alerts)
 */

import React, { useEffect, useState } from "react";
import { Sparkles, AlertTriangle, CheckCircle2, Bell } from "lucide-react";
import { fetchFlywheelAnalytics, generateProductInsightApi } from "../../lib/api";

export default function ProductTrendAnalyticsPage() {
  const [activeTab, setActiveTab] = useState<"personal" | "community" | "alerts">("personal");
  const [data, setData] = useState<Awaited<ReturnType<typeof fetchFlywheelAnalytics>> | null>(null);
  const [selectedProduct, setSelectedProduct] = useState("AirPods Pro 2");
  const [insightLoading, setInsightLoading] = useState(false);
  const [productInsight, setProductInsight] = useState("");

  useEffect(() => {
    fetchFlywheelAnalytics().then(setData);
  }, []);

  const handleGenerateInsight = async () => {
    setInsightLoading(true);
    const res = await generateProductInsightApi(selectedProduct);
    setProductInsight(res.report_markdown);
    setInsightLoading(false);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-surface-border pb-4">
        <h1 className="text-2xl font-bold font-mono text-[#eaecef]">
          📦 AI Product & Trend Analytics
        </h1>
        <p className="text-sm text-wolf-muted mt-1">
          Track your personal performance, compare with the community, and get AI-driven alerts.
        </p>
      </div>

      {/* 3 Tabs */}
      <div className="flex flex-wrap gap-2 border-b border-surface-border pb-3">
        <button
          type="button"
          onClick={() => setActiveTab("personal")}
          className={`px-4 py-2 rounded-lg text-xs font-mono font-bold transition-colors ${
            activeTab === "personal"
              ? "bg-wolf-gold/20 text-wolf-gold border border-wolf-gold/40"
              : "bg-surface text-wolf-muted hover:text-[#eaecef] border border-surface-border"
          }`}
        >
          📊 My Ledger Analytics
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("community")}
          className={`px-4 py-2 rounded-lg text-xs font-mono font-bold transition-colors ${
            activeTab === "community"
              ? "bg-wolf-green/20 text-wolf-green border border-wolf-green/40"
              : "bg-surface text-wolf-muted hover:text-[#eaecef] border border-surface-border"
          }`}
        >
          🌐 Community Trends
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("alerts")}
          className={`px-4 py-2 rounded-lg text-xs font-mono font-bold transition-colors ${
            activeTab === "alerts"
              ? "bg-wolf-red/20 text-wolf-red border border-wolf-red/40"
              : "bg-surface text-wolf-muted hover:text-[#eaecef] border border-surface-border"
          }`}
        >
          🔔 Proactive AI Alerts
        </button>
      </div>

      {/* TAB 1: MY LEDGER ANALYTICS */}
      {activeTab === "personal" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-surface border border-surface-border rounded-lg p-4">
              <div className="text-xs font-mono text-wolf-muted">🔥 Top Selling Asset (Yours)</div>
              <div className="text-2xl font-bold font-mono text-wolf-gold mt-1">
                {data?.personal_ledger.top_selling_asset || "AirPods Pro 2"}
              </div>
              <div className="text-xs font-mono text-wolf-green mt-1">Highest Volume</div>
            </div>

            <div className="bg-surface border border-surface-border rounded-lg p-4">
              <div className="text-xs font-mono text-wolf-muted">Total Units Sold</div>
              <div className="text-2xl font-bold font-mono text-[#eaecef] mt-1">
                {data?.personal_ledger.total_units_sold ?? 20} Units
              </div>
              <div className="text-xs font-mono text-wolf-green mt-1">Live Data</div>
            </div>
          </div>

          <div className="space-y-3">
            <h3 className="text-sm font-mono font-bold text-[#eaecef] uppercase">
              📊 Item-wise Market Demand (Your Shop)
            </h3>
            <div className="bg-surface border border-surface-border rounded-lg overflow-hidden">
              <table className="w-full text-xs font-mono">
                <thead className="bg-[#0b0e11] text-wolf-muted border-b border-surface-border">
                  <tr>
                    <th className="p-3.5 text-left">Product Name</th>
                    <th className="p-3.5 text-left">Units Sold</th>
                    <th className="p-3.5 text-left">Revenue Generated</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-border">
                  {(data?.personal_ledger.items || []).map((row, idx) => (
                    <tr key={idx} className="hover:bg-surface-hover/40">
                      <td className="p-3.5 font-bold text-[#eaecef]">{row.product_name}</td>
                      <td className="p-3.5 text-wolf-muted">{row.units_sold}</td>
                      <td className="p-3.5 text-wolf-green font-bold">{row.revenue_generated}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Dual-Perspective AI Product Intelligence Generator (from ai_engine.py:generate_product_insight) */}
          <div className="bg-surface border border-surface-border rounded-lg p-5 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h3 className="text-sm font-mono font-bold text-wolf-gold">
                  🧠 AI Product Intelligence (Importers vs New Entrepreneurs)
                </h3>
                <p className="text-xs text-wolf-muted mt-0.5">
                  Generate dual-perspective actionable advice based on wholesale price history.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <select
                  value={selectedProduct}
                  onChange={(e) => setSelectedProduct(e.target.value)}
                  className="px-3 py-2 rounded bg-[#0b0e11] border border-surface-border text-xs font-mono text-[#eaecef]"
                >
                  <option value="AirPods Pro 2">AirPods Pro 2</option>
                  <option value="Lenovo LP40 TWS">Lenovo LP40 TWS</option>
                  <option value="Apple Watch S9">Apple Watch S9</option>
                </select>
                <button
                  type="button"
                  onClick={handleGenerateInsight}
                  disabled={insightLoading}
                  className="flex items-center gap-1.5 px-4 py-2 bg-wolf-gold hover:bg-[#dfaa05] text-[#0b0e11] font-mono font-bold text-xs rounded"
                >
                  <Sparkles className="h-3.5 w-3.5" />
                  <span>{insightLoading ? "Analyzing..." : "Generate AI Insight"}</span>
                </button>
              </div>
            </div>

            {productInsight && (
              <div className="p-4 rounded bg-[#0b0e11] border border-surface-border text-xs font-mono text-[#eaecef] whitespace-pre-line leading-relaxed">
                {productInsight}
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: COMMUNITY TRENDS & PRICE BENCHMARK */}
      {activeTab === "community" && (
        <div className="space-y-6">
          <div>
            <h3 className="text-sm font-mono font-bold text-[#eaecef] uppercase">
              🧠 National Crowd-Sourced Trends
            </h3>
            <p className="text-xs text-wolf-muted mt-0.5">
              Anonymized trend analysis from the entire Trade Wolf merchant network.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-surface border border-surface-border rounded-lg p-4">
              <div className="text-xs font-mono text-wolf-muted">Trending Nationwide</div>
              <div className="text-xl font-bold font-mono text-[#eaecef] mt-1">
                {data?.community_trends.highlights.trending_nationwide.item || "AirPods Pro 2"}
              </div>
              <div className="text-xs font-mono text-wolf-green mt-1">
                {data?.community_trends.highlights.trending_nationwide.delta || "+24% Demand"}
              </div>
            </div>

            <div className="bg-surface border border-surface-border rounded-lg p-4">
              <div className="text-xs font-mono text-wolf-muted">Market Saturated</div>
              <div className="text-xl font-bold font-mono text-[#eaecef] mt-1">
                {data?.community_trends.highlights.market_saturated.item || "Wired Earphones"}
              </div>
              <div className="text-xs font-mono text-wolf-red mt-1">
                {data?.community_trends.highlights.market_saturated.delta || "-15% Demand"}
              </div>
            </div>

            <div className="bg-surface border border-surface-border rounded-lg p-4">
              <div className="text-xs font-mono text-wolf-muted">Upcoming Hype</div>
              <div className="text-xl font-bold font-mono text-wolf-gold mt-1">
                {data?.community_trends.highlights.upcoming_hype.item || "Smart Rings"}
              </div>
              <div className="text-xs font-mono text-wolf-green mt-1">
                {data?.community_trends.highlights.upcoming_hype.delta || "+45% Search Volume"}
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <h3 className="text-sm font-mono font-bold text-[#eaecef] uppercase">
              ⚖️ Price Benchmark (You vs Market)
            </h3>
            <div className="bg-surface border border-surface-border rounded-lg overflow-hidden">
              <table className="w-full text-xs font-mono">
                <thead className="bg-[#0b0e11] text-wolf-muted border-b border-surface-border">
                  <tr>
                    <th className="p-3.5 text-left">Product</th>
                    <th className="p-3.5 text-left">National Avg. Retail</th>
                    <th className="p-3.5 text-left">Your Avg. Retail</th>
                    <th className="p-3.5 text-left">AI Verdict</th>
                    <th className="p-3.5 text-left">National Demand</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-border">
                  {(data?.community_trends.benchmark_table || []).map((row, idx) => (
                    <tr key={idx} className="hover:bg-surface-hover/40">
                      <td className="p-3.5 font-bold text-[#eaecef]">{row.product}</td>
                      <td className="p-3.5 text-wolf-gold">{row.national_avg_retail}</td>
                      <td className="p-3.5 text-[#eaecef] font-semibold">{row.your_avg_retail}</td>
                      <td className="p-3.5 font-bold">{row.ai_verdict}</td>
                      <td className="p-3.5">{row.national_demand}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: PROACTIVE AI ALERTS (THE DATA FLYWHEEL ENGINE) */}
      {activeTab === "alerts" && (
        <div className="space-y-4">
          <div>
            <h3 className="text-sm font-mono font-bold text-[#eaecef] uppercase flex items-center gap-2">
              <Bell className="h-4 w-4 text-wolf-gold" />
              🤖 Trade Wolf Copilot (Live Business Advice)
            </h3>
            <p className="text-xs text-wolf-muted mt-0.5">
              AI reads your inventory velocity, cross-matches with community trends, and triggers warnings.
            </p>
          </div>

          <div className="space-y-3">
            {(data?.proactive_alerts.alerts || []).map((alert, idx) => (
              <div
                key={idx}
                className={`p-4 rounded-lg border text-xs font-mono leading-relaxed ${
                  alert.type === "CRITICAL"
                    ? "bg-wolf-red/10 border-wolf-red/40 text-[#eaecef]"
                    : "bg-wolf-gold/10 border-wolf-gold/40 text-[#eaecef]"
                }`}
              >
                <div
                  className={`font-bold text-sm mb-1 ${
                    alert.type === "CRITICAL" ? "text-wolf-red" : "text-wolf-gold"
                  }`}
                >
                  {alert.title}
                </div>
                <p>{alert.message}</p>
              </div>
            ))}

            {data?.proactive_alerts.all_systems_optimal && (
              <div className="p-4 rounded-lg bg-wolf-green/10 border border-wolf-green/40 text-xs font-mono text-wolf-green flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 shrink-0" />
                <span>
                  🟢 All Systems Optimal: Your stock levels match current velocity and market dues are well within safe thresholds. No urgent actions needed.
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

