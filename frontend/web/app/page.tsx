"use client";

/**
 * frontend/web/app/page.tsx
 * Unified Command Center Dashboard for Trade Wolf OS.
 * Features: Live Business Health Score Gauge, HITL Human Approval Gate, and AI Saved Metrics.
 */

import React, { useState } from "react";
import {
  ShieldAlert,
  CheckCircle2,
  XCircle,
  TrendingUp,
  Clock,
  Sparkles,
  AlertTriangle,
  ArrowUpRight,
  FileText,
  Mic,
  Share2,
} from "lucide-react";

interface ApprovalItem {
  id: string;
  action_type: string;
  summary: string;
  risk_level: "MEDIUM" | "CRITICAL";
  customer_or_target: string;
  time: string;
  status: "PENDING" | "APPROVED" | "REJECTED";
}

export default function CommandCenterDashboard() {
  // Mock live state for Human Approval Gate
  const [approvals, setApprovals] = useState<ApprovalItem[]>([
    {
      id: "app-001",
      action_type: "send_whatsapp_debt_notice",
      summary: "Send MODERATE WhatsApp payment reminder to Babul Store (৳45,000 overdue for 24 days)",
      risk_level: "MEDIUM",
      customer_or_target: "বাবুল স্টোর (01811223344)",
      time: "১০ মিনিট আগে",
      status: "PENDING",
    },
    {
      id: "app-002",
      action_type: "adjust_stock_bulk",
      summary: "Auto-deplete 50 bags of damaged Miniket rice from warehouse inventory",
      risk_level: "CRITICAL",
      customer_or_target: "মিনিকেট চাল ২৫ কেজি (-৫০ বস্তা)",
      time: "২৫ মিনিট আগে",
      status: "PENDING",
    },
  ]);

  const handleResolveApproval = (id: string, decision: "APPROVED" | "REJECTED") => {
    setApprovals((prev) =>
      prev.map((item) => (item.id === id ? { ...item, status: decision } : item))
    );
  };

  const pendingCount = approvals.filter((a) => a.status === "PENDING").length;

  return (
    <div className="space-y-6">
      {/* 1. Header Telemetry Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-surface-border">
        <div>
          <h1 className="text-2xl font-bold font-mono tracking-tight text-[#eaecef]">
            কমার্শিয়াল কমান্ড সেন্টার <span className="text-wolf-gold text-lg">/ OVERVIEW</span>
          </h1>
          <p className="text-sm text-wolf-muted">
            লাইভ অডিট, নগদ প্রবাহ, অনাদায়ী দেনা এবং এআই অটোমেশন মনিটর
          </p>
        </div>

        {/* Quick Trigger Buttons */}
        <div className="flex items-center gap-3">
          <a
            href="/orders"
            className="flex items-center gap-2 px-3 py-2 bg-surface hover:bg-surface-hover border border-surface-border rounded text-xs font-mono text-[#eaecef] transition-colors"
          >
            <Mic className="h-4 w-4 text-wolf-gold" />
            <span>ভয়েস অর্ডার এন্ট্রি</span>
          </a>
          <a
            href="/scanner"
            className="flex items-center gap-2 px-3 py-2 bg-surface hover:bg-surface-hover border border-surface-border rounded text-xs font-mono text-[#eaecef] transition-colors"
          >
            <FileText className="h-4 w-4 text-wolf-gold" />
            <span>হাতে লেখা মেমো স্ক্যান</span>
          </a>
          <a
            href="/orders"
            className="flex items-center gap-2 px-4 py-2 bg-wolf-gold hover:bg-[#dfaa05] text-[#0b0e11] font-semibold rounded text-xs font-mono transition-colors"
          >
            <span>+ নতুন ক্যাশ মেমো</span>
          </a>
        </div>
      </div>

      {/* 2. Top Metric Cards (Binance Dark Matte Aesthetic) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: Monthly Sales */}
        <div className="bg-surface border border-surface-border rounded-lg p-4 relative overflow-hidden">
          <div className="flex items-center justify-between text-xs text-wolf-muted font-mono">
            <span>মাসিক বিক্রয় (REVENUE)</span>
            <TrendingUp className="h-4 w-4 text-wolf-green" />
          </div>
          <div className="mt-2 text-2xl font-bold font-mono text-[#eaecef]">
            ৳৪,৮০,০০০
          </div>
          <div className="mt-1 flex items-center text-xs text-wolf-green font-mono">
            <ArrowUpRight className="h-3 w-3 mr-0.5" /> +১২.৫% বিগত মাসের তুলনায়
          </div>
        </div>

        {/* Metric 2: Total Receivables (Baki) */}
        <div className="bg-surface border border-surface-border rounded-lg p-4 relative overflow-hidden">
          <div className="flex items-center justify-between text-xs text-wolf-muted font-mono">
            <span>মোট বাকি / অনাদায়ী দেনা</span>
            <AlertTriangle className="h-4 w-4 text-wolf-red" />
          </div>
          <div className="mt-2 text-2xl font-bold font-mono text-wolf-red">
            ৳১,৪৫,০০০
          </div>
          <div className="mt-1 text-xs text-wolf-muted font-mono">
            মোট ১২ জন পাইকারি ক্রেতার নিকট বকেয়া
          </div>
        </div>

        {/* Metric 3: AI Saved Hours */}
        <div className="bg-surface border border-surface-border rounded-lg p-4 relative overflow-hidden">
          <div className="flex items-center justify-between text-xs text-wolf-muted font-mono">
            <span>এআই দিয়ে বাঁচানো কর্মঘণ্টা</span>
            <Clock className="h-4 w-4 text-wolf-gold" />
          </div>
          <div className="mt-2 text-2xl font-bold font-mono text-wolf-gold">
            ৪২.৫ ঘণ্টা
          </div>
          <div className="mt-1 text-xs text-wolf-muted font-mono">
            মেমো ওসিআর ও ভয়েস রেকর্ডিং বাবদ
          </div>
        </div>

        {/* Metric 4: AI Value Generated */}
        <div className="bg-surface border border-surface-border rounded-lg p-4 relative overflow-hidden">
          <div className="flex items-center justify-between text-xs text-wolf-muted font-mono">
            <span>এআই অর্জিত নেট ভ্যালু</span>
            <Sparkles className="h-4 w-4 text-wolf-green" />
          </div>
          <div className="mt-2 text-2xl font-bold font-mono text-wolf-green">
            ৳৯১,৩৭৫
          </div>
          <div className="mt-1 text-xs text-wolf-muted font-mono">
            উদ্ধারকৃত বকেয়া + ম্যানুয়াল শ্রম সাশ্রয়
          </div>
        </div>
      </div>

      {/* 3. Main Dashboard Grid: Health Gauge (Left) + HITL Approval Gate (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Business Health Score Gauge */}
        <div className="bg-surface border border-surface-border rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-surface-border pb-3">
            <h2 className="font-mono text-sm font-bold text-[#eaecef] uppercase tracking-wide">
              বিজনেস হেলথ স্কোর 🧠
            </h2>
            <span className="px-2 py-0.5 text-xs font-mono rounded bg-wolf-gold/10 text-wolf-gold border border-wolf-gold/20">
              MODERATE STABLE
            </span>
          </div>

          {/* Central Score Dial */}
          <div className="flex flex-col items-center justify-center py-4 bg-[#0b0e11] rounded border border-surface-border">
            <div className="text-5xl font-mono font-extrabold text-wolf-gold">
              ৭৮.৫<span className="text-xl text-wolf-muted font-normal">/১০০</span>
            </div>
            <p className="text-xs text-wolf-muted mt-1 font-mono">লাইভ ফাইন্যান্সিয়াল স্ট্যাবিলিটি ইনডেক্স</p>
          </div>

          {/* Sub-component Breakdowns */}
          <div className="space-y-3 text-xs font-mono">
            <div>
              <div className="flex justify-between text-wolf-muted mb-1">
                <span>নগদ প্রবাহ তারল্য (Liquidity)</span>
                <span className="text-[#eaecef]">৮২%</span>
              </div>
              <div className="w-full bg-[#0b0e11] h-1.5 rounded-full overflow-hidden">
                <div className="bg-wolf-green h-full rounded-full" style={{ width: "82%" }}></div>
              </div>
            </div>

            <div>
              <div className="flex justify-between text-wolf-muted mb-1">
                <span>বকেয়ার চাপ (Debt Burden)</span>
                <span className="text-wolf-red">৬৮.৫%</span>
              </div>
              <div className="w-full bg-[#0b0e11] h-1.5 rounded-full overflow-hidden">
                <div className="bg-wolf-red h-full rounded-full" style={{ width: "68.5%" }}></div>
              </div>
            </div>

            <div>
              <div className="flex justify-between text-wolf-muted mb-1">
                <span>ইনভেন্টরি ঘূর্ণন (Velocity)</span>
                <span className="text-[#eaecef]">৮৫%</span>
              </div>
              <div className="w-full bg-[#0b0e11] h-1.5 rounded-full overflow-hidden">
                <div className="bg-wolf-gold h-full rounded-full" style={{ width: "85%" }}></div>
              </div>
            </div>
          </div>

          {/* Actionable Insights */}
          <div className="p-3 bg-[#0b0e11] border border-surface-border rounded text-xs space-y-2">
            <div className="flex items-start gap-2 text-wolf-gold">
              <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
              <span>বকেয়ার পরিমাণ মাসিক বিক্রয়ের ৩০% ছাড়িয়েছে। রিমাইন্ডার পাঠানো জরুরি।</span>
            </div>
          </div>
        </div>

        {/* Right Column (2 spans): Human Approval Gate (HITL Queue) */}
        <div className="lg:col-span-2 bg-surface border border-surface-border rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-surface-border pb-3">
            <div className="flex items-center gap-2">
              <ShieldAlert className="h-5 w-5 text-wolf-gold" />
              <h2 className="font-mono text-sm font-bold text-[#eaecef] uppercase tracking-wide">
                হিউম্যান অ্যাপ্রুভাল গেট (HITL QUEUE)
              </h2>
            </div>
            <span className="px-2.5 py-0.5 text-xs font-mono font-bold rounded bg-wolf-red/10 text-wolf-red border border-wolf-red/20">
              {pendingCount} টি অ্যাকশন অনুমোদনের অপেক্ষায়
            </span>
          </div>

          {/* Queue List */}
          <div className="space-y-3">
            {approvals.map((item) => (
              <div
                key={item.id}
                className={`p-4 rounded border transition-all ${
                  item.status === "PENDING"
                    ? "bg-[#0b0e11] border-surface-border"
                    : item.status === "APPROVED"
                    ? "bg-wolf-green/5 border-wolf-green/30"
                    : "bg-wolf-red/5 border-wolf-red/30 opacity-60"
                }`}
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold uppercase ${
                        item.risk_level === "CRITICAL"
                          ? "bg-wolf-red/20 text-wolf-red border border-wolf-red/30"
                          : "bg-wolf-gold/20 text-wolf-gold border border-wolf-gold/30"
                      }`}
                    >
                      {item.risk_level} RISK
                    </span>
                    <span className="text-xs text-wolf-muted font-mono">{item.time}</span>
                  </div>

                  {item.status !== "PENDING" && (
                    <span
                      className={`text-xs font-mono font-bold ${
                        item.status === "APPROVED" ? "text-wolf-green" : "text-wolf-red"
                      }`}
                    >
                      [{item.status}]
                    </span>
                  )}
                </div>

                <p className="mt-2 text-sm text-[#eaecef] font-medium leading-relaxed">
                  {item.summary}
                </p>

                <div className="mt-2 text-xs font-mono text-wolf-muted">
                  টার্গেট: <span className="text-[#eaecef]">{item.customer_or_target}</span>
                </div>

                {/* Decision Actions */}
                {item.status === "PENDING" && (
                  <div className="mt-4 pt-3 border-t border-surface-border/50 flex items-center justify-end gap-3">
                    <button
                      onClick={() => handleResolveApproval(item.id, "REJECTED")}
                      className="flex items-center gap-1.5 px-3 py-1.5 bg-transparent hover:bg-wolf-red/10 border border-wolf-red/30 text-wolf-red rounded text-xs font-mono transition-colors"
                    >
                      <XCircle className="h-3.5 w-3.5" />
                      <span>বাতিল করুন (Reject)</span>
                    </button>
                    <button
                      onClick={() => handleResolveApproval(item.id, "APPROVED")}
                      className="flex items-center gap-1.5 px-4 py-1.5 bg-wolf-green hover:bg-[#0bb372] text-[#0b0e11] font-semibold rounded text-xs font-mono transition-colors"
                    >
                      <CheckCircle2 className="h-3.5 w-3.5" />
                      <span>অনুমোদন ও এক্সেকিউট (Approve)</span>
                    </button>
                  </div>
                )}
              </div>
            ))}

            {approvals.length === 0 && (
              <div className="py-8 text-center text-wolf-muted font-mono text-xs">
                কোনো পেন্ডিং অনুমোদন নেই। সিস্টেম নিরাপদে রান করছে।
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}