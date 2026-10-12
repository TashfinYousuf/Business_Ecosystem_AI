"use client";

/**
 * frontend/web/app/risk-simulator/page.tsx
 * Module 6 from legacy-streamlit-mvp/app.py:
 * 🛡️ AI Capital Shield & Interactive Risk Simulator
 * Interactive Sliders (Capital Usage %, Expected Retail Margin %, Simulate Market Price Spike/Drop %),
 * AI Risk Meter Gauge (0-100), Portfolio Allocation Breakdown, and Trade Wolf Guard Alerts.
 */

import React, { useEffect, useState } from "react";
import { ShieldAlert, ShieldCheck } from "lucide-react";
import { simulateCapitalRiskApi } from "../../lib/api";

export default function RiskSimulatorPage() {
  const [capital, setCapital] = useState(100000);
  const [selectedAsset, setSelectedAsset] = useState("AirPods Pro 2");
  const [capitalUsagePct, setCapitalUsagePct] = useState(30);
  const [markupPct, setMarkupPct] = useState(25);
  const [priceChangePct, setPriceChangePct] = useState(0);

  const [simResult, setSimResult] = useState<Awaited<ReturnType<typeof simulateCapitalRiskApi>> | null>(null);

  useEffect(() => {
    simulateCapitalRiskApi({
      capital,
      selected_asset: selectedAsset,
      capital_usage_pct: capitalUsagePct,
      markup_pct: markupPct,
      price_change_pct: priceChangePct,
    }).then(setSimResult);
  }, [capital, selectedAsset, capitalUsagePct, markupPct, priceChangePct]);

  const riskScore = simResult?.risk_score ?? 30;
  const gaugeColor =
    riskScore <= 40 ? "#00E676" : riskScore <= 75 ? "#FFC107" : "#FF5252";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-surface-border pb-4">
        <h1 className="text-2xl font-bold font-mono text-[#eaecef]">
          🛡️ AI Capital Shield & Interactive Risk Simulator
        </h1>
        <p className="text-sm text-wolf-muted mt-1">
          Calculate safe inventory sizing, simulate market drops/hikes, and view your AI Risk Meter based on live wholesale data and market sentiment.
        </p>
      </div>

      {/* Top Interactive Inputs */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 bg-surface border border-surface-border rounded-lg p-5">
        <div className="space-y-4 text-xs font-mono">
          <div>
            <label className="block text-wolf-muted mb-1">Total Capital (BDT):</label>
            <input
              type="number"
              min={10000}
              step={10000}
              value={capital}
              onChange={(e) => setCapital(Math.max(10000, Number(e.target.value)))}
              className="w-full px-3 py-2 rounded bg-[#0b0e11] border border-surface-border text-[#eaecef] font-bold text-sm"
            />
          </div>

          <div>
            <label className="block text-wolf-muted mb-1">Target Import Asset:</label>
            <select
              value={selectedAsset}
              onChange={(e) => setSelectedAsset(e.target.value)}
              className="w-full px-3 py-2 rounded bg-[#0b0e11] border border-surface-border text-[#eaecef] font-bold text-sm"
            >
              <option value="AirPods Pro 2">AirPods Pro 2</option>
              <option value="Lenovo LP40 TWS">Lenovo LP40 TWS</option>
              <option value="Apple Watch S9">Apple Watch S9</option>
              <option value="Smart Keyboard">Smart Keyboard</option>
            </select>
          </div>
        </div>

        <div className="flex flex-col justify-center space-y-2">
          <h3 className="text-sm font-mono font-bold text-[#eaecef]">
            📊 Market Pulse for {selectedAsset}
          </h3>
          <div
            className={`p-4 rounded-lg border text-xs font-mono font-bold ${
              (simResult?.safe_limit ?? 40) >= 60
                ? "bg-wolf-green/10 border-wolf-green/40 text-wolf-green"
                : "bg-wolf-gold/10 border-wolf-gold/40 text-wolf-gold"
            }`}
          >
            {simResult?.sentiment_status || "⚖️ Sentiment: Stable (Proceed with Caution)"}
            <div className="text-[11px] text-wolf-muted font-normal mt-1">
              Baseline Wholesale Cost: ৳{simResult?.import_cost?.toLocaleString() || "1,250"} / unit
            </div>
          </div>
        </div>
      </div>

      {/* Interactive Sliders */}
      <div className="bg-surface border border-surface-border rounded-lg p-5 space-y-4">
        <h3 className="text-sm font-mono font-bold text-wolf-gold uppercase">
          ⚙️ Adjust Market Variables (Interactive Slider)
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-xs font-mono">
          <div className="p-3 rounded bg-[#0b0e11] border border-surface-border space-y-2">
            <div className="flex justify-between">
              <span className="text-wolf-muted">Capital Usage (%)</span>
              <span className="text-wolf-gold font-bold">{capitalUsagePct}%</span>
            </div>
            <input
              type="range"
              min={10}
              max={100}
              value={capitalUsagePct}
              onChange={(e) => setCapitalUsagePct(Number(e.target.value))}
              className="w-full accent-wolf-gold cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-wolf-muted">
              <span>10%</span>
              <span>100%</span>
            </div>
          </div>

          <div className="p-3 rounded bg-[#0b0e11] border border-surface-border space-y-2">
            <div className="flex justify-between">
              <span className="text-wolf-muted">Expected Retail Margin (%)</span>
              <span className="text-wolf-green font-bold">{markupPct}%</span>
            </div>
            <input
              type="range"
              min={5}
              max={100}
              value={markupPct}
              onChange={(e) => setMarkupPct(Number(e.target.value))}
              className="w-full accent-wolf-green cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-wolf-muted">
              <span>5%</span>
              <span>100%</span>
            </div>
          </div>

          <div className="p-3 rounded bg-[#0b0e11] border border-surface-border space-y-2">
            <div className="flex justify-between">
              <span className="text-wolf-muted">Simulate Price Spike/Drop (%)</span>
              <span
                className={`font-bold ${
                  priceChangePct >= 0 ? "text-wolf-green" : "text-wolf-red"
                }`}
              >
                {priceChangePct > 0 ? `+${priceChangePct}%` : `${priceChangePct}%`}
              </span>
            </div>
            <input
              type="range"
              min={-40}
              max={40}
              value={priceChangePct}
              onChange={(e) => setPriceChangePct(Number(e.target.value))}
              className="w-full accent-wolf-gold cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-wolf-muted">
              <span>-40% (Drop)</span>
              <span>+40% (Spike)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Simulation Results */}
      <div className="space-y-3">
        <h3 className="text-sm font-mono font-bold text-[#eaecef] uppercase">
          📊 Simulation Results
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-surface border border-surface-border rounded-lg p-4">
            <div className="text-xs font-mono text-wolf-muted">Units You Can Buy</div>
            <div className="text-2xl font-bold font-mono text-[#eaecef] mt-1">
              {simResult?.max_units ?? 24} pcs
            </div>
            <div className="text-xs font-mono text-wolf-muted mt-1">
              Invest: ৳{(simResult?.actual_investment ?? 30000).toLocaleString()}
            </div>
          </div>

          <div className="bg-surface border border-surface-border rounded-lg p-4">
            <div className="text-xs font-mono text-wolf-muted">Target Profit (Normal)</div>
            <div className="text-2xl font-bold font-mono text-wolf-green mt-1">
              ৳{(simResult?.target_profit ?? 7500).toLocaleString()}
            </div>
            <div className="text-xs font-mono text-wolf-muted mt-1">
              Retail: ৳{(simResult?.expected_sell_price ?? 1562).toLocaleString()}
            </div>
          </div>

          <div className="bg-surface border border-surface-border rounded-lg p-4">
            <div className="text-xs font-mono text-wolf-muted">
              {simResult?.delta_label || "0% Hike (Bullish)"}
            </div>
            <div
              className={`text-2xl font-bold font-mono mt-1 ${
                (simResult?.simulated_profit_loss ?? 0) >= 0
                  ? "text-wolf-green"
                  : "text-wolf-red"
              }`}
            >
              ৳{(simResult?.simulated_profit_loss ?? 7500).toLocaleString()}
            </div>
            <div className="text-xs font-mono text-wolf-muted mt-1">
              Simulated Price Impact ({priceChangePct}%)
            </div>
          </div>
        </div>
      </div>

      {/* AI Risk Meter Gauge + Portfolio Allocation Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* AI Risk Meter Gauge */}
        <div className="bg-surface border border-surface-border rounded-lg p-5 flex flex-col items-center justify-center">
          <h4 className="text-sm font-mono font-bold text-[#eaecef] mb-3">
            AI Risk Meter (0 - 100)
          </h4>
          <div className="w-full max-w-xs space-y-3 text-center">
            <div className="text-5xl font-extrabold font-mono" style={{ color: gaugeColor }}>
              {riskScore}
            </div>
            <div className="w-full h-4 bg-[#0b0e11] rounded-full overflow-hidden border border-surface-border flex">
              <div className="h-full bg-[#00E676]" style={{ width: "40%" }} title="Safe (0-40)" />
              <div className="h-full bg-[#FFC107]" style={{ width: "35%" }} title="Moderate (40-75)" />
              <div className="h-full bg-[#FF5252]" style={{ width: "25%" }} title="Danger (75-100)" />
            </div>
            <div className="relative w-full h-2">
              <div
                className="w-3 h-3 rounded-full bg-white border-2 border-[#0b0e11] absolute -top-3 transition-all"
                style={{ left: `calc(${Math.min(100, Math.max(0, riskScore))}% - 6px)` }}
              />
            </div>
            <div className="flex justify-between text-[10px] font-mono text-wolf-muted">
              <span>0 (Safe)</span>
              <span>40 (Caution)</span>
              <span>75 (Danger)</span>
              <span>100</span>
            </div>
          </div>
        </div>

        {/* Portfolio Allocation Breakdown */}
        <div className="bg-surface border border-surface-border rounded-lg p-5 space-y-3 font-mono text-xs">
          <h4 className="text-sm font-bold text-[#eaecef]">
            💰 Portfolio Allocation Breakdown
          </h4>
          <div className="p-3.5 rounded bg-wolf-green/10 border border-wolf-green/30 text-wolf-green">
            📦 <strong>Active Inventory ({capitalUsagePct}%):</strong> ৳
            {(simResult?.portfolio_allocation.active_inventory ?? 30000).toLocaleString()}
          </div>
          <div className="p-3.5 rounded bg-wolf-gold/10 border border-wolf-gold/30 text-wolf-gold">
            📣 <strong>Marketing & Ads Buffer (15%):</strong> ৳
            {(simResult?.portfolio_allocation.marketing_buffer ?? 10500).toLocaleString()}
          </div>
          <div className="p-3.5 rounded bg-teal-500/10 border border-teal-500/30 text-teal-300">
            🛡️ <strong>Emergency Cash Backup (85%):</strong> ৳
            {(simResult?.portfolio_allocation.emergency_cash ?? 59500).toLocaleString()}
          </div>
        </div>
      </div>

      {/* Trade Wolf Guard Alerts */}
      <div className="space-y-2">
        <h4 className="text-sm font-mono font-bold text-[#eaecef] uppercase">
          🚨 Trade Wolf Guard Alerts
        </h4>
        <div
          className={`p-4 rounded-lg border text-xs font-mono font-bold flex items-center gap-3 ${
            simResult?.guard_alert.status === "DANGER"
              ? "bg-wolf-red/10 border-wolf-red/40 text-wolf-red"
              : "bg-wolf-green/10 border-wolf-green/40 text-wolf-green"
          }`}
        >
          {simResult?.guard_alert.status === "DANGER" ? (
            <ShieldAlert className="h-5 w-5 shrink-0" />
          ) : (
            <ShieldCheck className="h-5 w-5 shrink-0" />
          )}
          <span>{simResult?.guard_alert.message}</span>
        </div>
      </div>
    </div>
  );
}

