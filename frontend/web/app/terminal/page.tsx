"use client";

/**
 * frontend/web/app/terminal/page.tsx
 * Module 2 from legacy-streamlit-mvp/app.py:
 * ⚡ Live Market Terminal (Gainers, Losers, 7-Day Pulse Sparklines, Live StarTech Scraper & AI Quant Arbitrage).
 */

import React, { useEffect, useState } from "react";
import { RefreshCw, TrendingUp, TrendingDown, Zap, ChevronDown, ChevronUp } from "lucide-react";
import { useLanguage } from "../../lib/LanguageContext";
import { fetchTerminalSnapshot, runLiveArbitrageScan } from "../../lib/api";

function Sparkline({ data, positive = true }: { data: number[]; positive?: boolean }) {
  if (!data || data.length < 2) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const width = 120;
  const height = 32;
  const points = data
    .map((val, idx) => {
      const x = (idx / (data.length - 1)) * width;
      const y = height - ((val - min) / range) * (height - 6) - 3;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <svg width={width} height={height} className="overflow-visible">
      <polyline
        fill="none"
        stroke={positive ? "#0ecb81" : "#f6465d"}
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        points={points}
      />
    </svg>
  );
}

export default function LiveMarketTerminalPage() {
  const { t } = useLanguage();
  const [activeTab, setActiveTab] = useState<"gainers" | "losers" | "arbitrage">("gainers");
  const [terminalData, setTerminalData] = useState<Awaited<ReturnType<typeof fetchTerminalSnapshot>> | null>(null);
  const [scraping, setScraping] = useState(false);
  const [scrapeMessage, setScrapeMessage] = useState("");
  const [arbitrageItems, setArbitrageItems] = useState<
    Array<{
      product_name: string;
      wholesale_price: number;
      retail_price: number;
      gross_margin_pct: number;
      net_profit_bdt: number;
      risk_index: string;
      verdict: string;
      analysis_markdown: string;
    }>
  >([]);
  const [expandedIdx, setExpandedIdx] = useState<number | null>(0);

  useEffect(() => {
    fetchTerminalSnapshot().then(setTerminalData);
  }, []);

  const handleRunScraper = async () => {
    setScraping(true);
    setScrapeMessage("");
    const res = await runLiveArbitrageScan("smart-watch");
    setArbitrageItems(res.opportunities || []);
    setScrapeMessage(t.msg_success);
    setScraping(false);
    setExpandedIdx(0);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-surface-border pb-4">
        <h1 className="text-2xl font-bold font-mono text-[#eaecef]">{t.term_title}</h1>
        <p className="text-sm text-wolf-muted mt-1">{t.term_cap}</p>
      </div>

      {/* Top 3 Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-surface border border-surface-border rounded-lg p-4">
          <div className="text-xs font-mono text-wolf-muted">{t.vol_title}</div>
          <div className="text-2xl font-bold font-mono text-[#eaecef] mt-1">
            {terminalData?.metrics.market_heat.value || "৳ 1.2B"}
          </div>
          <div className="text-xs font-mono text-wolf-green mt-1">
            {terminalData?.metrics.market_heat.delta || "+8.2% (MoM)"}
          </div>
        </div>

        <div className="bg-surface border border-surface-border rounded-lg p-4">
          <div className="text-xs font-mono text-wolf-muted">{t.sentiment_title}</div>
          <div className="text-2xl font-bold font-mono text-wolf-gold mt-1">
            {terminalData?.metrics.buyer_mood.value || "🔥 Highly Bullish"}
          </div>
          <div className="text-xs font-mono text-wolf-green mt-1">
            {terminalData?.metrics.buyer_mood.delta || "Buyers Dominating"}
          </div>
        </div>

        <div className="bg-surface border border-surface-border rounded-lg p-4">
          <div className="text-xs font-mono text-wolf-muted">{t.margin_title}</div>
          <div className="text-2xl font-bold font-mono text-wolf-green mt-1">
            {terminalData?.metrics.avg_profit.value || "22.5%"}
          </div>
          <div className="text-xs font-mono text-wolf-muted mt-1">
            {terminalData?.metrics.avg_profit.delta || "+1.1% (Due to USD)"}
          </div>
        </div>
      </div>

      {/* 3 Tabs: High Demand (Gainers), Slow Moving (Losers), Cheapest Deals (Arbitrage) */}
      <div className="flex flex-wrap gap-2 border-b border-surface-border pb-3">
        <button
          type="button"
          onClick={() => setActiveTab("gainers")}
          className={`px-4 py-2 rounded-lg text-xs font-mono font-bold transition-colors ${
            activeTab === "gainers"
              ? "bg-wolf-green/20 text-wolf-green border border-wolf-green/40"
              : "bg-surface text-wolf-muted hover:text-[#eaecef] border border-surface-border"
          }`}
        >
          {t.tab_gainers}
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("losers")}
          className={`px-4 py-2 rounded-lg text-xs font-mono font-bold transition-colors ${
            activeTab === "losers"
              ? "bg-wolf-red/20 text-wolf-red border border-wolf-red/40"
              : "bg-surface text-wolf-muted hover:text-[#eaecef] border border-surface-border"
          }`}
        >
          {t.tab_losers}
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("arbitrage")}
          className={`px-4 py-2 rounded-lg text-xs font-mono font-bold transition-colors ${
            activeTab === "arbitrage"
              ? "bg-wolf-gold/20 text-wolf-gold border border-wolf-gold/40"
              : "bg-surface text-wolf-muted hover:text-[#eaecef] border border-surface-border"
          }`}
        >
          {t.tab_arbitrage}
        </button>
      </div>

      {/* Tab Content */}
      {activeTab === "gainers" && (
        <div className="bg-surface border border-surface-border rounded-lg overflow-hidden">
          <table className="w-full text-xs font-mono">
            <thead className="bg-[#0b0e11] text-wolf-muted border-b border-surface-border">
              <tr>
                <th className="p-3.5 text-left">Asset / Product</th>
                <th className="p-3.5 text-left">Wholesale</th>
                <th className="p-3.5 text-left">24h Trend</th>
                <th className="p-3.5 text-left">7-Day Pulse</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-border">
              {(terminalData?.gainers || []).map((row, idx) => (
                <tr key={idx} className="hover:bg-surface-hover/50">
                  <td className="p-3.5 font-bold text-[#eaecef]">{row.asset_product}</td>
                  <td className="p-3.5 text-wolf-gold font-semibold">{row.wholesale}</td>
                  <td className="p-3.5 text-wolf-green font-bold">{row.trend_24h}</td>
                  <td className="p-3.5">
                    <Sparkline data={row.pulse_7d} positive={true} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === "losers" && (
        <div className="bg-surface border border-surface-border rounded-lg overflow-hidden">
          <table className="w-full text-xs font-mono">
            <thead className="bg-[#0b0e11] text-wolf-muted border-b border-surface-border">
              <tr>
                <th className="p-3.5 text-left">Asset / Product</th>
                <th className="p-3.5 text-left">Wholesale</th>
                <th className="p-3.5 text-left">24h Trend</th>
                <th className="p-3.5 text-left">7-Day Pulse</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-border">
              {(terminalData?.losers || []).map((row, idx) => (
                <tr key={idx} className="hover:bg-surface-hover/50">
                  <td className="p-3.5 font-bold text-[#eaecef]">{row.asset_product}</td>
                  <td className="p-3.5 text-wolf-muted font-semibold">{row.wholesale}</td>
                  <td className="p-3.5 text-wolf-red font-bold">{row.trend_24h}</td>
                  <td className="p-3.5">
                    <Sparkline data={row.pulse_7d} positive={false} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === "arbitrage" && (
        <div className="bg-surface border border-surface-border rounded-lg p-5 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h3 className="text-base font-bold font-mono text-[#eaecef]">
                🕸️ Live Scraper & AI Arbitrage
              </h3>
              <p className="text-xs text-wolf-muted mt-0.5">
                Scraping real-time retail prices from BD E-commerce (Star Tech) and matching with AI predictive logic.
              </p>
            </div>
            <button
              type="button"
              onClick={handleRunScraper}
              disabled={scraping}
              className="flex items-center gap-2 px-4 py-2.5 bg-wolf-gold hover:bg-[#dfaa05] text-[#0b0e11] font-mono font-bold text-xs rounded transition-colors shrink-0"
            >
              <RefreshCw className={`h-4 w-4 ${scraping ? "animate-spin" : ""}`} />
              <span>{scraping ? "Scraping Star Tech servers..." : t.btn_scrape}</span>
            </button>
          </div>

          {scrapeMessage && (
            <div className="p-3 rounded bg-wolf-green/10 border border-wolf-green/30 text-wolf-green text-xs font-mono font-bold">
              {scrapeMessage}
            </div>
          )}

          {arbitrageItems.length > 0 && (
            <div className="space-y-3 pt-2">
              {arbitrageItems.map((item, idx) => {
                const isOpen = expandedIdx === idx;
                return (
                  <div
                    key={idx}
                    className="border border-surface-border rounded-lg bg-[#0b0e11] overflow-hidden"
                  >
                    <button
                      type="button"
                      onClick={() => setExpandedIdx(isOpen ? null : idx)}
                      className="w-full flex items-center justify-between p-4 text-left hover:bg-surface-hover/40 transition-colors"
                    >
                      <span className="text-xs font-mono font-bold text-[#eaecef]">
                        📊 {item.product_name} | Retail: ৳{item.retail_price.toLocaleString()}
                      </span>
                      {isOpen ? (
                        <ChevronUp className="h-4 w-4 text-wolf-muted" />
                      ) : (
                        <ChevronDown className="h-4 w-4 text-wolf-muted" />
                      )}
                    </button>

                    {isOpen && (
                      <div className="p-4 border-t border-surface-border space-y-4">
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                          <div className="p-3 rounded bg-surface border border-surface-border">
                            <div className="text-[11px] font-mono text-wolf-muted">
                              Live Retail (Scraped)
                            </div>
                            <div className="text-xl font-bold font-mono text-[#eaecef] mt-1">
                              ৳{item.retail_price.toLocaleString()}
                            </div>
                          </div>
                          <div className="p-3 rounded bg-surface border border-surface-border">
                            <div className="text-[11px] font-mono text-wolf-muted">
                              Est. Wholesale (65% Index)
                            </div>
                            <div className="text-xl font-bold font-mono text-wolf-gold mt-1">
                              ৳{item.wholesale_price.toLocaleString()}
                            </div>
                          </div>
                        </div>

                        <div className="p-4 rounded bg-surface border border-wolf-gold/30 space-y-2 text-xs font-mono">
                          <div className="font-bold text-wolf-gold text-sm">
                            🧠 AI Quant Analysis
                          </div>
                          <div>
                            <span className="text-wolf-muted">Gross Margin: </span>
                            <span className="text-wolf-green font-bold">
                              {item.gross_margin_pct}%
                            </span>
                          </div>
                          <div>
                            <span className="text-wolf-muted">Net Profit Estimate: </span>
                            <span className="text-[#eaecef] font-bold">
                              ৳{item.net_profit_bdt.toLocaleString()} per unit (after 5% marketing & 2% return loss)
                            </span>
                          </div>
                          <div>
                            <span className="text-wolf-muted">Risk Index: </span>
                            <span className="text-wolf-green font-bold">{item.risk_index}</span>
                          </div>
                          <div>
                            <span className="text-wolf-muted">AI Verdict: </span>
                            <span className="text-[#eaecef]">{item.verdict}</span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

