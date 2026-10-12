"use client";

/**
 * frontend/web/app/market-overview/page.tsx
 * Module 4 from legacy-streamlit-mvp/app.py:
 * 🌍 Macro & Micro Market Overview (National Sector Pulse, Live USD/BDT Rate,
 * Global Economic Indicators: Gold, Crude Oil, S&P 500 with Sparklines, and Live Local Inventory Private Wallet).
 */

import React, { useEffect, useState } from "react";
import { Globe, Wallet, TrendingUp } from "lucide-react";
import { useLanguage } from "../../lib/LanguageContext";
import { fetchMarketOverview } from "../../lib/api";

function MiniSparkline({ history, delta }: { history: number[]; delta: number }) {
  if (!history || history.length < 2) return null;
  const min = Math.min(...history);
  const max = Math.max(...history);
  const range = max - min || 1;
  const width = 180;
  const height = 35;
  const points = history
    .map((val, idx) => {
      const x = (idx / (history.length - 1)) * width;
      const y = height - ((val - min) / range) * (height - 6) - 3;
      return `${x},${y}`;
    })
    .join(" ");

  const color = delta >= 0 ? "#00E676" : "#FF5252";

  return (
    <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} className="mt-2">
      <polyline
        fill="none"
        stroke={color}
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        points={points}
      />
    </svg>
  );
}

export default function MarketOverviewPage() {
  const { t } = useLanguage();
  const [data, setData] = useState<Awaited<ReturnType<typeof fetchMarketOverview>> | null>(null);

  useEffect(() => {
    fetchMarketOverview().then(setData);
  }, []);

  const pulse = data?.national_pulse;
  const usd = data?.usd_rate;
  const globalInd = data?.global_indicators;
  const wallet = data?.private_wallet || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-surface-border pb-4">
        <h1 className="text-2xl font-bold font-mono text-[#eaecef]">
          🌍 Macro & Micro Market Overview
        </h1>
        <p className="text-sm text-wolf-muted mt-1">{t.over_cap}</p>
      </div>

      {/* 1. National Sector Pulse & Volume */}
      <div className="space-y-3">
        <h2 className="text-sm font-mono font-bold text-wolf-gold uppercase">
          📊 National Sector Pulse & Volume
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-surface border border-surface-border rounded-lg p-4">
            <div className="text-xs font-mono text-wolf-muted">24h Nat. Trade Volume</div>
            <div className="text-2xl font-bold font-mono text-[#eaecef] mt-1">
              {pulse?.market_volume || "৳ 1.48B"}
            </div>
            <div className="text-xs font-mono text-wolf-green mt-1">
              {pulse?.volume_change || "+3.4% (24h)"}
            </div>
          </div>

          <div className="bg-surface border border-surface-border rounded-lg p-4">
            <div className="text-xs font-mono text-wolf-muted">Market Sentiment</div>
            <div className="text-2xl font-bold font-mono text-wolf-gold mt-1">
              {pulse?.sentiment || "🔥 Bullish"}
            </div>
            <div className="text-xs font-mono text-wolf-green mt-1">
              Avg Margin: {pulse?.avg_margin || "18.8%"}
            </div>
          </div>

          <div className="bg-surface border border-surface-border rounded-lg p-4">
            <div className="text-xs font-mono text-wolf-muted">Live USD/BDT Rate</div>
            <div className="flex items-baseline justify-between mt-1">
              <span className="text-2xl font-bold font-mono text-[#eaecef]">
                ৳ {usd?.price?.toFixed(2) || "118.50"}
              </span>
              <span className="text-xs font-mono text-wolf-green">
                +{usd?.change ?? 0.42}%
              </span>
            </div>
            {usd?.history && <MiniSparkline history={usd.history} delta={usd.change} />}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-surface border border-surface-border rounded-lg p-4">
            <div className="text-xs font-mono text-wolf-muted">🔥 Hottest Sector</div>
            <div className="text-lg font-bold font-mono text-[#eaecef] mt-1">
              {pulse?.trending_sector || "TWS & Audio"}
            </div>
            <div className="text-xs font-mono text-wolf-green mt-1">High Demand</div>
          </div>

          <div className="bg-surface border border-surface-border rounded-lg p-4">
            <div className="text-xs font-mono text-wolf-muted">🩸 Struggling Sector</div>
            <div className="text-lg font-bold font-mono text-[#eaecef] mt-1">
              {pulse?.struggling_sector || "Wired Accessories"}
            </div>
            <div className="text-xs font-mono text-wolf-red mt-1">Saturated</div>
          </div>

          <div className="bg-surface border border-surface-border rounded-lg p-4">
            <div className="text-xs font-mono text-wolf-muted">Active Wholesalers Tracked</div>
            <div className="text-lg font-bold font-mono text-[#eaecef] mt-1">
              {pulse?.active_wholesalers || 364} Hubs
            </div>
            <div className="text-xs font-mono text-wolf-green mt-1">Live Network</div>
          </div>
        </div>
      </div>

      {/* 2. Global Economic Indicators (Import Factors) */}
      <div className="space-y-3 pt-2 border-t border-surface-border">
        <h2 className="text-sm font-mono font-bold text-wolf-gold uppercase">
          🌍 Global Economic Indicators (Import Factors)
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-surface border border-surface-border rounded-lg p-4">
            <div className="text-xs font-mono text-wolf-muted">Gold (per oz)</div>
            <div className="flex items-baseline justify-between mt-1">
              <span className="text-xl font-bold font-mono text-[#eaecef]">
                ${globalInd?.Gold.price.toLocaleString() || "2,350.50"}
              </span>
              <span className="text-xs font-mono text-wolf-green">
                +{globalInd?.Gold.change ?? 0.65}%
              </span>
            </div>
            {globalInd?.Gold.history && (
              <MiniSparkline history={globalInd.Gold.history} delta={globalInd.Gold.change} />
            )}
          </div>

          <div className="bg-surface border border-surface-border rounded-lg p-4">
            <div className="text-xs font-mono text-wolf-muted">Crude Oil (per bbl)</div>
            <div className="flex items-baseline justify-between mt-1">
              <span className="text-xl font-bold font-mono text-[#eaecef]">
                ${globalInd?.Oil.price || "82.30"}
              </span>
              <span className="text-xs font-mono text-wolf-green">
                +{globalInd?.Oil.change ?? 0.37}%
              </span>
            </div>
            {globalInd?.Oil.history && (
              <MiniSparkline history={globalInd.Oil.history} delta={globalInd.Oil.change} />
            )}
          </div>

          <div className="bg-surface border border-surface-border rounded-lg p-4">
            <div className="text-xs font-mono text-wolf-muted">S&P 500 Index</div>
            <div className="flex items-baseline justify-between mt-1">
              <span className="text-xl font-bold font-mono text-[#eaecef]">
                {globalInd?.SP500.price.toLocaleString() || "5,200.10"}
              </span>
              <span className="text-xs font-mono text-wolf-green">
                +{globalInd?.SP500.change ?? 0.48}%
              </span>
            </div>
            {globalInd?.SP500.history && (
              <MiniSparkline history={globalInd.SP500.history} delta={globalInd.SP500.change} />
            )}
          </div>
        </div>
      </div>

      {/* 3. Live Local Inventory (Private Wallet) */}
      <div className="space-y-3 pt-2 border-t border-surface-border">
        <h2 className="text-sm font-mono font-bold text-wolf-gold uppercase">
          💼 Live Local Inventory (Private Wallet)
        </h2>

        {wallet.length === 0 ? (
          <div className="p-6 bg-surface border border-surface-border rounded-lg text-xs font-mono text-wolf-muted">
            📭 Your asset wallet is empty. Scan wholesale memos or record a sale to build inventory.
          </div>
        ) : (
          <div className="bg-surface border border-surface-border rounded-lg overflow-hidden">
            <table className="w-full text-xs font-mono">
              <thead className="bg-[#0b0e11] text-wolf-muted border-b border-surface-border">
                <tr>
                  <th className="p-3 text-left">Asset / Product</th>
                  <th className="p-3 text-left">Current Wholesale</th>
                  <th className="p-3 text-left">Stock Status</th>
                  <th className="p-3 text-left">Last Updated</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-border">
                {wallet.map((item, idx) => (
                  <tr key={idx} className="hover:bg-surface-hover/40">
                    <td className="p-3 font-bold text-[#eaecef]">{item.asset_product}</td>
                    <td className="p-3 text-wolf-gold font-semibold">
                      ৳{Number(item.current_wholesale).toLocaleString()}
                    </td>
                    <td className="p-3">
                      <span className="px-2 py-0.5 rounded bg-wolf-green/10 text-wolf-green border border-wolf-green/20">
                        {item.stock_status}
                      </span>
                    </td>
                    <td className="p-3 text-wolf-muted">{item.last_updated}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

