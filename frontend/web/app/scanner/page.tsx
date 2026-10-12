"use client";

/**
 * frontend/web/app/scanner/page.tsx
 * Interactive Memo Scanner & Voice Order Ingestion Terminal.
 * Converts raw handwritten slips or bilingual speech notes into structured invoices.
 */

import React, { useState } from "react";
import {
  UploadCloud,
  FileImage,
  Mic,
  MicOff,
  Check,
  AlertCircle,
  Share2,
  Printer,
  Sparkles,
  ArrowRight,
  MessageSquare,
  Plus,
  Trash2,
  Save,
} from "lucide-react";
import { extractPurchaseTextApi, commitInventoryStockApi } from "../../lib/api";

interface ExtractedItem {
  name: string;
  quantity: number;
  unit_price: number;
  total_price: number;
}

export default function MemoScannerPage() {
  const [isProcessing, setIsProcessing] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [uploadedImage, setUploadedImage] = useState<string | null>(null);

  // Legacy 3-Tab Wholesale Purchase Ingestion State (app.py lines 422-563)
  const [scanTab, setScanTab] = useState<"image" | "voice" | "text">("image");
  const [bulkPurchaseText, setBulkPurchaseText] = useState(
    "Bought 10 AirPods Pro 2 at 1250 tk wholesale"
  );
  const [voiceFileName, setVoiceFileName] = useState("");
  const [editableStockItems, setEditableStockItems] = useState<
    Array<{ product_name: string; unit_price: number; quantity: number }>
  >([]);
  const [commitMessage, setCommitMessage] = useState("");

  // Extracted transactional state from Vision/Audio AI
  const [extractedData, setExtractedData] = useState<{
    customer_name: string;
    customer_phone: string;
    items: ExtractedItem[];
    subtotal: number;
    discount: number;
    grand_total: number;
    paid_amount: number;
    due_amount: number;
    confidence: number;
  } | null>(null);

  // Simulated AI Vision Extraction Trigger
  const handleSimulateScan = () => {
    setIsProcessing(true);
    setCommitMessage("");
    setUploadedImage("https://placehold.co/600x400/181a20/f0b90b?text=Sample+Handwritten+Voucher");

    setTimeout(() => {
      const sampleItems = [
        { name: "তীর সয়াবিন তেল ৫ লিটার", quantity: 4, unit_price: 820, total_price: 3280 },
        { name: "মিনিকেট চাল ২৫ কেজি বস্তা", quantity: 2, unit_price: 1850, total_price: 3700 },
        { name: "মসুর ডাল চিকন ১ কেজি", quantity: 10, unit_price: 135, total_price: 1350 },
      ];
      setExtractedData({
        customer_name: "আলমগীর ভ্যারাইটি স্টোর",
        customer_phone: "01822334455",
        items: sampleItems,
        subtotal: 8330,
        discount: 130,
        grand_total: 8200,
        paid_amount: 5000,
        due_amount: 3200,
        confidence: 0.96,
      });
      setEditableStockItems(
        sampleItems.map((it) => ({
          product_name: it.name,
          unit_price: it.unit_price,
          quantity: it.quantity,
        }))
      );
      setIsProcessing(false);
    }, 1000);
  };

  const handleProcessTextOrVoicePurchase = async (inputStr: string) => {
    setIsProcessing(true);
    setCommitMessage("");
    const res = await extractPurchaseTextApi(inputStr);
    const p = res.temp_purchase;
    setEditableStockItems([
      {
        product_name: p.product_name || "AirPods Pro 2",
        unit_price: Number(p.unit_price || 1250),
        quantity: Number(p.quantity || 5),
      },
    ]);
    setIsProcessing(false);
  };

  const handleCommitToInventory = async () => {
    if (editableStockItems.length === 0) return;
    const res = await commitInventoryStockApi(editableStockItems);
    setCommitMessage(res.message);
    setEditableStockItems([]);
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="border-b border-surface-border pb-4">
        <h1 className="text-2xl font-bold font-mono text-[#eaecef]">
          মাল্টি-মোডাল মেমো স্ক্যানার <span className="text-wolf-gold text-lg">/ INGESTION</span>
        </h1>
        <p className="text-sm text-wolf-muted">
          হাতে লেখা রসিদের ছবি বা মুখের বাংলা অডিও রেকর্ড থেকে স্বয়ংক্রিয় ডিজিটাল ইনভয়েস ও ইনভেন্টরি স্টক তৈরি করুন
        </p>
      </div>

      {/* 3 Ingestion Mode Tabs from legacy-streamlit-mvp/app.py line 422 */}
      <div className="flex flex-wrap gap-2 border-b border-surface-border pb-3 text-xs font-mono">
        <button
          type="button"
          onClick={() => setScanTab("image")}
          className={`px-4 py-2 rounded-lg font-bold transition-colors ${
            scanTab === "image"
              ? "bg-wolf-gold/20 text-wolf-gold border border-wolf-gold/40"
              : "bg-surface text-wolf-muted hover:text-[#eaecef] border border-surface-border"
          }`}
        >
          📸 Scan Image Memo
        </button>
        <button
          type="button"
          onClick={() => setScanTab("voice")}
          className={`px-4 py-2 rounded-lg font-bold transition-colors ${
            scanTab === "voice"
              ? "bg-wolf-green/20 text-wolf-green border border-wolf-green/40"
              : "bg-surface text-wolf-muted hover:text-[#eaecef] border border-surface-border"
          }`}
        >
          🎙️ Voice Purchase
        </button>
        <button
          type="button"
          onClick={() => setScanTab("text")}
          className={`px-4 py-2 rounded-lg font-bold transition-colors ${
            scanTab === "text"
              ? "bg-teal-500/20 text-teal-300 border border-teal-500/40"
              : "bg-surface text-wolf-muted hover:text-[#eaecef] border border-surface-border"
          }`}
        >
          💬 Text Purchase
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Upload / Capture Area */}
        <div className="space-y-4">
          {scanTab === "image" && (
            <div className="bg-surface border border-surface-border rounded-lg p-5">
              <h2 className="font-mono text-sm font-bold text-[#eaecef] uppercase mb-3 flex items-center gap-2">
                <FileImage className="h-4 w-4 text-wolf-gold" />
                মেমো ছবি আপলোড বা ক্যামেরা ক্যাপচার
              </h2>

              {/* Upload Dropzone */}
              <div
                onClick={handleSimulateScan}
                className="border-2 border-dashed border-surface-border hover:border-wolf-gold/60 bg-[#0b0e11] rounded-lg p-8 flex flex-col items-center justify-center cursor-pointer transition-colors"
              >
                <UploadCloud className="h-10 w-10 text-wolf-muted mb-3" />
                <p className="text-sm font-mono text-[#eaecef] text-center">
                  এখানে ক্লিক করে মেমোর ছবি আপলোড করুন
                </p>
                <span className="text-xs text-wolf-muted mt-1 font-mono">
                  JPG, PNG, HEIC (হাতে লেখা ভাউচার সমর্থিত)
                </span>

                <button
                  type="button"
                  className="mt-4 px-4 py-2 bg-surface hover:bg-surface-hover border border-surface-border text-wolf-gold rounded text-xs font-mono"
                >
                  টেস্ট মেমো দিয়ে ডেমো ট্রাই করুন
                </button>
              </div>

              {/* Voice Audio Alternate */}
              <div className="mt-4 pt-4 border-t border-surface-border flex items-center justify-between">
                <div className="text-xs font-mono text-wolf-muted">
                  অথবা মুখে বলে অর্ডার দিন (বাংলা/বাংলিশ):
                </div>
                <button
                  onClick={() => setIsRecording(!isRecording)}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded text-xs font-mono font-semibold transition-colors ${
                    isRecording
                      ? "bg-wolf-red text-white animate-pulse"
                      : "bg-surface hover:bg-surface-hover border border-surface-border text-[#eaecef]"
                  }`}
                >
                  {isRecording ? <MicOff className="h-3.5 w-3.5" /> : <Mic className="h-3.5 w-3.5 text-wolf-gold" />}
                  <span>{isRecording ? "রেকর্ডিং থামান" : "ভয়েস রেকর্ড শুরু"}</span>
                </button>
              </div>
            </div>
          )}

          {scanTab === "voice" && (
            <div className="bg-surface border border-surface-border rounded-lg p-5 space-y-4 text-xs font-mono">
              <h2 className="text-sm font-bold text-[#eaecef] uppercase flex items-center gap-2">
                <Mic className="h-4 w-4 text-wolf-green" />
                🎙️ Voice Wholesale Purchase Entry
              </h2>
              <label className="block p-6 border-2 border-dashed border-surface-border hover:border-wolf-green/60 rounded-lg bg-[#0b0e11] text-center cursor-pointer">
                <UploadCloud className="h-8 w-8 text-wolf-muted mx-auto mb-2" />
                <span className="text-[#eaecef] block">
                  Upload Purchase Audio File (.mp3, .wav, .m4a)
                </span>
                {voiceFileName && (
                  <span className="text-wolf-green font-bold block mt-1">
                    Loaded: {voiceFileName}
                  </span>
                )}
                <input
                  type="file"
                  accept=".mp3,.wav,.m4a,audio/*"
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f) setVoiceFileName(f.name);
                  }}
                  className="hidden"
                />
              </label>

              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setIsRecording(!isRecording)}
                  className={`py-2.5 px-3 rounded font-bold border flex items-center justify-center gap-2 ${
                    isRecording
                      ? "bg-wolf-red text-white border-wolf-red animate-pulse"
                      : "bg-[#0b0e11] border-surface-border text-[#eaecef]"
                  }`}
                >
                  <Mic className="h-4 w-4 text-wolf-gold" />
                  <span>{isRecording ? "🛑 Stop" : "🎤 Or Record Live"}</span>
                </button>

                <button
                  type="button"
                  onClick={() =>
                    handleProcessTextOrVoicePurchase(
                      "Bought 12 AirPods Pro 2 at 1250 tk wholesale"
                    )
                  }
                  className="py-2.5 px-3 rounded bg-wolf-green hover:bg-[#0bb372] text-[#0b0e11] font-bold"
                >
                  🧠 Process Voice Purchase
                </button>
              </div>
            </div>
          )}

          {scanTab === "text" && (
            <div className="bg-surface border border-surface-border rounded-lg p-5 space-y-4 text-xs font-mono">
              <h2 className="text-sm font-bold text-[#eaecef] uppercase flex items-center gap-2">
                <MessageSquare className="h-4 w-4 text-teal-400" />
                💬 Bulk Text Wholesale Purchase Entry
              </h2>
              <textarea
                rows={4}
                value={bulkPurchaseText}
                onChange={(e) => setBulkPurchaseText(e.target.value)}
                placeholder="Paste bulk purchase text message..."
                className="w-full p-3 rounded bg-[#0b0e11] border border-surface-border text-[#eaecef] outline-none focus:border-wolf-gold"
              />
              <button
                type="button"
                onClick={() => handleProcessTextOrVoicePurchase(bulkPurchaseText)}
                className="w-full py-2.5 bg-wolf-gold hover:bg-[#dfaa05] text-[#0b0e11] font-bold rounded transition-colors"
              >
                🧠 Process Text Purchase
              </button>
            </div>
          )}

          {/* AI Status Panel */}
          {isProcessing && (
            <div className="bg-surface border border-wolf-gold/30 rounded-lg p-4 flex items-center gap-3 text-wolf-gold">
              <Sparkles className="h-5 w-5 animate-spin" />
              <span className="text-xs font-mono">
                জেমিনাই ২.৫ ভিশন মেমোর হিসাব যাচাই করছে...
              </span>
            </div>
          )}

          {commitMessage && (
            <div className="p-3.5 rounded-lg bg-wolf-green/10 border border-wolf-green/40 text-wolf-green text-xs font-mono font-bold">
              {commitMessage}
            </div>
          )}

          {/* 🛠️ INVENTORY PREVIEW & EDIT ACTION BOX BEFORE DB SAVE (from app.py lines 510-563) */}
          {editableStockItems.length > 0 && (
            <div className="bg-surface border border-wolf-gold/40 rounded-lg p-5 space-y-4 text-xs font-mono">
              <div>
                <h3 className="text-sm font-bold text-wolf-gold">
                  📦 Review & Edit Incoming Inventory Stock
                </h3>
                <p className="text-[11px] text-wolf-muted mt-0.5">
                  স্টক ডেটাবেসে পুশ করার আগে আইটেমের নাম, পাইকারি রেট এবং কোয়ান্টিটি চেক বা এডিট করে নিন।
                </p>
              </div>

              <div className="space-y-2">
                {editableStockItems.map((item, idx) => (
                  <div
                    key={idx}
                    className="grid grid-cols-12 gap-2 items-center bg-[#0b0e11] p-2.5 rounded border border-surface-border"
                  >
                    <input
                      type="text"
                      value={item.product_name}
                      onChange={(e) => {
                        const copy = [...editableStockItems];
                        copy[idx].product_name = e.target.value;
                        setEditableStockItems(copy);
                      }}
                      placeholder="Product Name"
                      className="col-span-6 px-2 py-1.5 rounded bg-surface border border-surface-border text-[#eaecef]"
                    />
                    <input
                      type="number"
                      min={0}
                      value={item.unit_price}
                      onChange={(e) => {
                        const copy = [...editableStockItems];
                        copy[idx].unit_price = Number(e.target.value);
                        setEditableStockItems(copy);
                      }}
                      placeholder="Price (৳)"
                      className="col-span-3 px-2 py-1.5 rounded bg-surface border border-surface-border text-wolf-gold"
                    />
                    <input
                      type="number"
                      min={1}
                      value={item.quantity}
                      onChange={(e) => {
                        const copy = [...editableStockItems];
                        copy[idx].quantity = Math.max(1, Number(e.target.value));
                        setEditableStockItems(copy);
                      }}
                      placeholder="Qty"
                      className="col-span-2 px-2 py-1.5 rounded bg-surface border border-surface-border text-[#eaecef]"
                    />
                    <button
                      type="button"
                      onClick={() =>
                        setEditableStockItems(editableStockItems.filter((_, i) => i !== idx))
                      }
                      className="col-span-1 text-wolf-red hover:opacity-80 flex justify-center"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>

              <div className="flex items-center justify-between gap-2">
                <button
                  type="button"
                  onClick={() =>
                    setEditableStockItems([
                      ...editableStockItems,
                      { product_name: "New Wholesale Asset", unit_price: 500, quantity: 1 },
                    ])
                  }
                  className="px-3 py-1.5 rounded bg-[#0b0e11] border border-surface-border text-wolf-muted hover:text-[#eaecef] flex items-center gap-1"
                >
                  <Plus className="h-3.5 w-3.5" />
                  <span>Add Row</span>
                </button>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setEditableStockItems([])}
                    className="px-3 py-2 rounded border border-wolf-red/40 text-wolf-red hover:bg-wolf-red/10 font-bold"
                  >
                    🗑️ Discard Entry
                  </button>
                  <button
                    type="button"
                    onClick={handleCommitToInventory}
                    className="px-4 py-2 rounded bg-wolf-green hover:bg-[#0bb372] text-[#0b0e11] font-bold flex items-center gap-1.5"
                  >
                    <Save className="h-3.5 w-3.5" />
                    <span>💾 Commit Whole Invoice to Inventory</span>
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: AI Extraction & Invoice Review */}
        <div className="bg-surface border border-surface-border rounded-lg p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-surface-border pb-3 mb-4">
              <h2 className="font-mono text-sm font-bold text-[#eaecef] uppercase">
                এক্সট্রাক্টেড ডিজিটাল মেমো প্রিভিউ
              </h2>
              {extractedData && (
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-wolf-green/10 text-wolf-green border border-wolf-green/20">
                  CONFIDENCE: {Math.round(extractedData.confidence * 100)}%
                </span>
              )}
            </div>

            {!extractedData ? (
              <div className="py-20 text-center text-wolf-muted font-mono text-xs">
                বামে মেমো ছবি আপলোড করলে এখানে স্বয়ংক্রিয় হিসাব প্রদর্শিত হবে।
              </div>
            ) : (
              <div className="space-y-4">
                {/* Customer Meta */}
                <div className="grid grid-cols-2 gap-3 p-3 bg-[#0b0e11] rounded border border-surface-border text-xs font-mono">
                  <div>
                    <span className="text-wolf-muted">ক্রেতার নাম:</span>
                    <p className="text-[#eaecef] font-bold mt-0.5">{extractedData.customer_name}</p>
                  </div>
                  <div>
                    <span className="text-wolf-muted">মোবাইল:</span>
                    <p className="text-[#eaecef] mt-0.5">{extractedData.customer_phone}</p>
                  </div>
                </div>

                {/* Line Items Table */}
                <div className="border border-surface-border rounded overflow-hidden">
                  <table className="w-full text-xs font-mono">
                    <thead className="bg-[#0b0e11] text-wolf-muted border-b border-surface-border">
                      <tr>
                        <th className="p-2 text-left">বিবরণ</th>
                        <th className="p-2 text-center">পরিমাণ</th>
                        <th className="p-2 text-right">দর</th>
                        <th className="p-2 text-right">মোট</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-surface-border">
                      {extractedData.items.map((item, idx) => (
                        <tr key={idx} className="hover:bg-surface-hover/40">
                          <td className="p-2 text-[#eaecef]">{item.name}</td>
                          <td className="p-2 text-center text-wolf-muted">{item.quantity}</td>
                          <td className="p-2 text-right text-wolf-muted">৳{item.unit_price}</td>
                          <td className="p-2 text-right text-[#eaecef] font-semibold">৳{item.total_price}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Financial Summary */}
                <div className="p-3 bg-[#0b0e11] rounded border border-surface-border space-y-1.5 text-xs font-mono">
                  <div className="flex justify-between text-wolf-muted">
                    <span>মোট মূল্য:</span>
                    <span>৳{extractedData.subtotal}</span>
                  </div>
                  <div className="flex justify-between text-wolf-muted">
                    <span>ছাড় (ডিসকাউন্ট):</span>
                    <span>-৳{extractedData.discount}</span>
                  </div>
                  <div className="flex justify-between text-base font-bold text-[#eaecef] pt-1 border-t border-surface-border">
                    <span>সর্বমোট প্রদেয়:</span>
                    <span className="text-wolf-gold">৳{extractedData.grand_total}</span>
                  </div>
                  <div className="flex justify-between text-wolf-green pt-1">
                    <span>নগদ জমা:</span>
                    <span>৳{extractedData.paid_amount}</span>
                  </div>
                  <div className="flex justify-between text-wolf-red font-bold">
                    <span>বাকি (Due):</span>
                    <span>৳{extractedData.due_amount}</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Action Footer */}
          {extractedData && (
            <div className="mt-6 pt-4 border-t border-surface-border flex items-center justify-end gap-3">
              <button className="flex items-center gap-1.5 px-3 py-2 bg-surface hover:bg-surface-hover border border-surface-border text-[#eaecef] rounded text-xs font-mono">
                <Printer className="h-4 w-4" />
                <span>প্রিন্ট রসিদ</span>
              </button>
              <button className="flex items-center gap-1.5 px-4 py-2 bg-wolf-green hover:bg-[#0bb372] text-[#0b0e11] font-bold rounded text-xs font-mono">
                <Share2 className="h-4 w-4" />
                <span>হোয়াটসঅ্যাপে পাঠান</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}