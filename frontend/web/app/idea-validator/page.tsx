"use client";

/**
 * frontend/web/app/idea-validator/page.tsx
 * Module 7 from legacy-streamlit-mvp/app.py:
 * 🚀 Business Idea Validator (Free Beta) — Evaluates gadget/SME business feasibility in Bangladesh.
 */

import React, { useState } from "react";
import { Sparkles, Lock, CheckCircle2 } from "lucide-react";
import { validateBusinessIdeaApi } from "../../lib/api";

export default function BusinessIdeaValidatorPage() {
  const [location, setLocation] = useState("Dhaka");
  const [category, setCategory] = useState("TWS / Earbuds");
  const [businessModel, setBusinessModel] = useState("Local Wholesale & Retail");
  const [budget, setBudget] = useState(20000);
  const [margin, setMargin] = useState(15);
  const [riskTolerance, setRiskTolerance] = useState("Medium (Balanced)");

  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<string | null>(null);
  const [premiumUnlockedMsg, setPremiumUnlockedMsg] = useState(false);

  const handleGenerate = async () => {
    setLoading(true);
    setPremiumUnlockedMsg(false);
    const res = await validateBusinessIdeaApi({
      location,
      category,
      business_model: businessModel,
      budget,
      margin,
      risk: riskTolerance,
    });
    setReport(res.report_markdown);
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-surface-border pb-4">
        <h1 className="text-2xl font-bold font-mono text-[#eaecef]">
          🚀 Business Idea Validator (Free Beta)
        </h1>
        <p className="text-sm text-wolf-muted mt-1">
          Thinking of starting a new gadget business? Validate your market feasibility, calculate dropshipping vs retail risks, and get a realistic success score before investing a single taka.
        </p>
      </div>

      {/* Form Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Left: Target Market & Niche */}
        <div className="bg-surface border border-surface-border rounded-lg p-5 space-y-4 text-xs font-mono">
          <h3 className="text-sm font-bold text-wolf-gold uppercase">
            🎯 Target Market & Niche
          </h3>

          <div>
            <label className="block text-wolf-muted mb-1">Target City/Region:</label>
            <select
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="w-full px-3 py-2 rounded bg-[#0b0e11] border border-surface-border text-[#eaecef]"
            >
              {["Dhaka", "Cumilla", "Chattogram", "Sylhet", "Rajshahi"].map((loc) => (
                <option key={loc} value={loc}>
                  {loc}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-wolf-muted mb-1">Product Category:</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full px-3 py-2 rounded bg-[#0b0e11] border border-surface-border text-[#eaecef]"
            >
              {[
                "TWS / Earbuds",
                "Smartwatches",
                "Premium Audio",
                "Mobile Accessories",
              ].map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-wolf-muted mb-1.5">Business Model:</label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {["Local Wholesale & Retail", "Dropshipping (Online)"].map((model) => (
                <button
                  key={model}
                  type="button"
                  onClick={() => setBusinessModel(model)}
                  className={`p-2.5 rounded border text-left font-semibold transition-colors ${
                    businessModel === model
                      ? "bg-wolf-gold/15 border-wolf-gold text-wolf-gold"
                      : "bg-[#0b0e11] border-surface-border text-wolf-muted"
                  }`}
                >
                  {model}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Right: Financial Strategy */}
        <div className="bg-surface border border-surface-border rounded-lg p-5 space-y-4 text-xs font-mono">
          <h3 className="text-sm font-bold text-wolf-gold uppercase">
            💰 Financial Strategy
          </h3>

          <div>
            <label className="block text-wolf-muted mb-1">
              Initial Investment Capital (BDT):
            </label>
            <input
              type="number"
              min={5000}
              step={5000}
              value={budget}
              onChange={(e) => setBudget(Math.max(5000, Number(e.target.value)))}
              className="w-full px-3 py-2 rounded bg-[#0b0e11] border border-surface-border text-[#eaecef] font-bold"
            />
          </div>

          <div>
            <div className="flex justify-between text-wolf-muted mb-1">
              <span>Expected Profit Margin (%)</span>
              <span className="text-wolf-green font-bold">{margin}%</span>
            </div>
            <input
              type="range"
              min={5}
              max={50}
              value={margin}
              onChange={(e) => setMargin(Number(e.target.value))}
              className="w-full accent-wolf-green cursor-pointer"
            />
          </div>

          <div>
            <label className="block text-wolf-muted mb-1.5">Your Risk Tolerance:</label>
            <div className="grid grid-cols-3 gap-2">
              {["Low (Safe)", "Medium (Balanced)", "High (Aggressive)"].map((r) => (
                <button
                  key={r}
                  type="button"
                  onClick={() => setRiskTolerance(r)}
                  className={`p-2 rounded border text-center font-semibold transition-colors ${
                    riskTolerance === r
                      ? "bg-wolf-green/15 border-wolf-green text-wolf-green"
                      : "bg-[#0b0e11] border-surface-border text-wolf-muted"
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Generate Button */}
      <button
        type="button"
        onClick={handleGenerate}
        disabled={loading}
        className="w-full py-3 bg-wolf-gold hover:bg-[#dfaa05] text-[#0b0e11] font-mono font-bold text-sm rounded-lg flex items-center justify-center gap-2 transition-colors"
      >
        <Sparkles className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
        <span>
          {loading
            ? `Analyzing ${category} market heat in ${location}...`
            : "🧠 Generate Feasibility Report"}
        </span>
      </button>

      {/* Output Report */}
      {report && (
        <div className="bg-surface border border-surface-border rounded-lg p-6 space-y-5">
          <div className="p-3 rounded bg-wolf-green/10 border border-wolf-green/30 text-wolf-green text-xs font-mono font-bold flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4" />
            <span>✅ Custom Market Analysis Complete!</span>
          </div>

          <div className="p-4 rounded bg-[#0b0e11] border border-surface-border text-xs font-mono text-[#eaecef] whitespace-pre-line leading-relaxed">
            {report}
          </div>

          <div className="pt-4 border-t border-surface-border text-center space-y-3">
            <h4 className="text-sm font-mono font-bold text-wolf-gold">
              Want the live WhatsApp supplier list and real-time margin tracking for this specific idea?
            </h4>
            <button
              type="button"
              onClick={() => setPremiumUnlockedMsg(true)}
              className="inline-flex items-center gap-2 px-6 py-2.5 bg-wolf-green hover:bg-[#0bb372] text-[#0b0e11] font-mono font-bold text-xs rounded-lg transition-colors"
            >
              <Lock className="h-3.5 w-3.5" />
              <span>🔒 Unlock Premium Dashboard</span>
            </button>
            {premiumUnlockedMsg && (
              <p className="text-xs font-mono text-wolf-green">
                ✅ You have full access! Visit &quot;Trusted Suppliers 🛡️&quot; and &quot;Live Market 🔴&quot; in the sidebar.
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

