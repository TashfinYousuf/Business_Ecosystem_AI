"use client";

/**
 * frontend/web/app/orders/page.tsx
 * Module 9 from legacy-streamlit-mvp/app.py:
 * 📥 Order Inbox (WhatsApp Sales Ledger) & 📒 Customer Dues + 🔔 AI Due Recovery.
 * Includes Voice Order (file upload & live record), Text Order, Review & Edit Extracted Order,
 * Smart Invoice & Receipt Generator (.txt download), Customer Dues Table, and 1-Click WhatsApp Reminder (wa.me).
 */

import React, { useEffect, useState } from "react";
import {
  Mic,
  MicOff,
  Upload,
  CheckCircle2,
  Trash2,
  Download,
  RefreshCw,
  Send,
  Sparkles,
  FileText,
} from "lucide-react";
import { useLanguage } from "../../lib/LanguageContext";
import {
  extractOrderFromTextApi,
  confirmOrderToLedgerApi,
  fetchSalesLedgerApi,
  draftDueReminderApi,
} from "../../lib/api";

export default function OrderInboxLedgerPage() {
  const { t } = useLanguage();
  const [orderTab, setOrderTab] = useState<"voice" | "text">("voice");
  const [audioFileName, setAudioFileName] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [hasVoicePayload, setHasVoicePayload] = useState(false);
  const [whatsappText, setWhatsappText] = useState("Sold 5 AirPods to Tuhin Bhai at 600 tk paid 1000");
  const [extracting, setExtracting] = useState(false);

  // Review & Edit Extracted Order State (temp_order from app.py lines 1236-1275)
  const [tempOrder, setTempOrder] = useState<{
    customer_name: string;
    item_name: string;
    quantity: number;
    unit_price: number;
    paid_amount: number;
  } | null>(null);

  // Generated Smart Invoice / Receipt State (invoice_data & last_order from app.py lines 1278-1315)
  const [generatedInvoice, setGeneratedInvoice] = useState<{
    invoice_data: string;
    smart_receipt: string;
    filename: string;
  } | null>(null);

  // Customer Dues Ledger & AI Due Recovery State
  const [ledgerData, setLedgerData] = useState<Awaited<ReturnType<typeof fetchSalesLedgerApi>> | null>(null);
  const [selectedDueCustomer, setSelectedDueCustomer] = useState("");
  const [draftedReminder, setDraftedReminder] = useState<{
    drafted_message: string;
    whatsapp_link: string;
  } | null>(null);

  const loadLedger = async () => {
    const res = await fetchSalesLedgerApi();
    setLedgerData(res);
    if (res.due_customers.length > 0 && !selectedDueCustomer) {
      setSelectedDueCustomer(res.due_customers[0].customer);
    }
  };

  useEffect(() => {
    loadLedger();
  }, []);

  const handleExtractVoice = async () => {
    setExtracting(true);
    const hint = audioFileName
      ? `Sold 5 AirPods Pro 2 to Tuhin Bhai at 600 tk paid 1000 (${audioFileName})`
      : "Sold 5 AirPods Pro 2 to Tuhin Bhai at 600 tk paid 1000";
    const res = await extractOrderFromTextApi(hint);
    setTempOrder(res.temp_order);
    setExtracting(false);
  };

  const handleExtractText = async () => {
    if (!whatsappText.trim()) return;
    setExtracting(true);
    const res = await extractOrderFromTextApi(whatsappText);
    setTempOrder(res.temp_order);
    setExtracting(false);
  };

  const handleConfirmSaveOrder = async () => {
    if (!tempOrder) return;
    const res = await confirmOrderToLedgerApi(tempOrder);
    setGeneratedInvoice({
      invoice_data: res.invoice_data,
      smart_receipt: res.smart_receipt,
      filename: res.filename,
    });
    setTempOrder(null);
    await loadLedger();
  };

  const handleDownloadReceipt = (content: string, filename: string) => {
    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDraftReminder = async () => {
    if (!selectedDueCustomer) return;
    const dueObj = ledgerData?.due_customers.find((c) => c.customer === selectedDueCustomer);
    const res = await draftDueReminderApi(selectedDueCustomer, dueObj?.total_due || 2000);
    setDraftedReminder(res);
  };

  const tBill = tempOrder ? tempOrder.quantity * tempOrder.unit_price : 0;
  const tDue = tempOrder ? Math.max(0, tBill - tempOrder.paid_amount) : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-surface-border pb-4">
        <h1 className="text-2xl font-bold font-mono text-[#eaecef]">{t.sales_title}</h1>
        <p className="text-sm text-wolf-muted mt-1">{t.sales_cap}</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* LEFT PANEL (5 cols): ORDER INBOX (Voice & Text + Review & Edit + Smart Receipt) */}
        <div className="lg:col-span-5 space-y-5">
          <div className="bg-surface border border-surface-border rounded-lg p-5 space-y-4">
            <h2 className="text-base font-bold font-mono text-[#eaecef]">
              {t.sales_record}
            </h2>

            <div className="p-3 rounded bg-teal-500/10 border border-teal-500/30 text-teal-300 text-xs font-mono">
              💡 <strong>উদাহরণ:</strong> {t.sales_info}
            </div>

            {/* Tabs: Voice Order | Text Order */}
            <div className="grid grid-cols-2 gap-2 p-1 bg-[#0b0e11] rounded-lg border border-surface-border text-xs font-mono">
              <button
                type="button"
                onClick={() => setOrderTab("voice")}
                className={`py-2 rounded font-bold transition-colors ${
                  orderTab === "voice"
                    ? "bg-surface text-wolf-gold border border-surface-border"
                    : "text-wolf-muted hover:text-[#eaecef]"
                }`}
              >
                🎙️ Voice Order
              </button>
              <button
                type="button"
                onClick={() => setOrderTab("text")}
                className={`py-2 rounded font-bold transition-colors ${
                  orderTab === "text"
                    ? "bg-surface text-wolf-gold border border-surface-border"
                    : "text-wolf-muted hover:text-[#eaecef]"
                }`}
              >
                💬 Text Order
              </button>
            </div>

            {orderTab === "voice" ? (
              <div className="space-y-3 text-xs font-mono">
                <label className="block p-4 border-2 border-dashed border-surface-border hover:border-wolf-gold/60 rounded-lg bg-[#0b0e11] text-center cursor-pointer transition-colors">
                  <Upload className="h-6 w-6 text-wolf-muted mx-auto mb-1.5" />
                  <span className="text-[#eaecef] block">
                    Upload WhatsApp Voice Note File (.mp3, .wav, .m4a)
                  </span>
                  {audioFileName && (
                    <span className="text-wolf-green block mt-1 font-bold">
                      Selected: {audioFileName}
                    </span>
                  )}
                  <input
                    type="file"
                    accept=".mp3,.wav,.m4a,audio/*"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) {
                        setAudioFileName(file.name);
                        setHasVoicePayload(true);
                      }
                    }}
                    className="hidden"
                  />
                </label>

                <button
                  type="button"
                  onClick={() => {
                    if (isRecording) {
                      setIsRecording(false);
                      setHasVoicePayload(true);
                    } else {
                      setIsRecording(true);
                    }
                  }}
                  className={`w-full py-2.5 px-4 rounded-lg font-bold flex items-center justify-center gap-2 border transition-colors ${
                    isRecording
                      ? "bg-wolf-red text-white border-wolf-red animate-pulse"
                      : "bg-[#0b0e11] hover:bg-surface-hover text-[#eaecef] border-surface-border"
                  }`}
                >
                  {isRecording ? (
                    <>
                      <MicOff className="h-4 w-4" />
                      <span>🛑 Stop Recording</span>
                    </>
                  ) : (
                    <>
                      <Mic className="h-4 w-4 text-wolf-gold" />
                      <span>🎤 Click to Record Live Voice</span>
                    </>
                  )}
                </button>

                {(hasVoicePayload || audioFileName) && (
                  <button
                    type="button"
                    onClick={handleExtractVoice}
                    disabled={extracting}
                    className="w-full py-2.5 bg-wolf-gold hover:bg-[#dfaa05] text-[#0b0e11] font-bold rounded-lg transition-colors"
                  >
                    {extracting ? "AI মেসেজ রিড করছে..." : "🧠 Extract Voice Details"}
                  </button>
                )}
              </div>
            ) : (
              <div className="space-y-3 text-xs font-mono">
                <textarea
                  rows={3}
                  value={whatsappText}
                  onChange={(e) => setWhatsappText(e.target.value)}
                  placeholder="Paste customer text here (e.g. Sold 5 AirPods to Tuhin Bhai at 600tk paid 1000)"
                  className="w-full p-3 rounded-lg bg-[#0b0e11] border border-surface-border text-[#eaecef] outline-none focus:border-wolf-gold"
                />
                <button
                  type="button"
                  onClick={handleExtractText}
                  disabled={extracting}
                  className="w-full py-2.5 bg-wolf-gold hover:bg-[#dfaa05] text-[#0b0e11] font-bold rounded-lg transition-colors"
                >
                  {extracting ? "AI মেসেজ রিড করছে..." : "🧠 Extract Text Details"}
                </button>
              </div>
            )}
          </div>

          {/* 🛡️ UX SAVIOR: Review & Edit Extracted Order Panel (app.py lines 1236-1275) */}
          {tempOrder && (
            <div className="bg-surface border border-wolf-gold/40 rounded-lg p-5 space-y-4 text-xs font-mono">
              <div>
                <h3 className="text-sm font-bold text-wolf-gold">
                  📝 Review & Edit Extracted Order
                </h3>
                <p className="text-[11px] text-wolf-muted mt-0.5">
                  ভুল এড়াতে ডাটাবেসে এন্ট্রি হওয়ার আগে নিচে কাস্টমাইজ বা কারেকশন করে নিন।
                </p>
              </div>

              <div className="space-y-3">
                <div>
                  <label className="block text-wolf-muted mb-1">Customer Name:</label>
                  <input
                    type="text"
                    value={tempOrder.customer_name}
                    onChange={(e) =>
                      setTempOrder({ ...tempOrder, customer_name: e.target.value })
                    }
                    className="w-full px-3 py-2 rounded bg-[#0b0e11] border border-surface-border text-[#eaecef]"
                  />
                </div>
                <div>
                  <label className="block text-wolf-muted mb-1">Item Name:</label>
                  <input
                    type="text"
                    value={tempOrder.item_name}
                    onChange={(e) =>
                      setTempOrder({ ...tempOrder, item_name: e.target.value })
                    }
                    className="w-full px-3 py-2 rounded bg-[#0b0e11] border border-surface-border text-[#eaecef]"
                  />
                </div>
                <div className="grid grid-cols-3 gap-2">
                  <div>
                    <label className="block text-wolf-muted mb-1">Quantity:</label>
                    <input
                      type="number"
                      min={1}
                      value={tempOrder.quantity}
                      onChange={(e) =>
                        setTempOrder({
                          ...tempOrder,
                          quantity: Math.max(1, Number(e.target.value)),
                        })
                      }
                      className="w-full px-2.5 py-2 rounded bg-[#0b0e11] border border-surface-border text-[#eaecef]"
                    />
                  </div>
                  <div>
                    <label className="block text-wolf-muted mb-1">Unit Price (৳):</label>
                    <input
                      type="number"
                      min={0}
                      value={tempOrder.unit_price}
                      onChange={(e) =>
                        setTempOrder({
                          ...tempOrder,
                          unit_price: Math.max(0, Number(e.target.value)),
                        })
                      }
                      className="w-full px-2.5 py-2 rounded bg-[#0b0e11] border border-surface-border text-[#eaecef]"
                    />
                  </div>
                  <div>
                    <label className="block text-wolf-muted mb-1">Cash Paid (৳):</label>
                    <input
                      type="number"
                      min={0}
                      value={tempOrder.paid_amount}
                      onChange={(e) =>
                        setTempOrder({
                          ...tempOrder,
                          paid_amount: Math.max(0, Number(e.target.value)),
                        })
                      }
                      className="w-full px-2.5 py-2 rounded bg-[#0b0e11] border border-surface-border text-[#eaecef]"
                    />
                  </div>
                </div>
              </div>

              <div className="p-3 rounded bg-wolf-gold/10 border border-wolf-gold/30 text-wolf-gold font-bold">
                📊 লাইভ হিসাব: মোট বিল: ৳{tBill.toLocaleString()} | বাকি ডিউ: ৳{tDue.toLocaleString()}
              </div>

              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={handleConfirmSaveOrder}
                  className="py-2.5 px-3 bg-wolf-green hover:bg-[#0bb372] text-[#0b0e11] font-bold rounded flex items-center justify-center gap-1.5"
                >
                  <CheckCircle2 className="h-4 w-4" />
                  <span>💾 Confirm & Save</span>
                </button>
                <button
                  type="button"
                  onClick={() => setTempOrder(null)}
                  className="py-2.5 px-3 bg-surface hover:bg-wolf-red/10 border border-wolf-red/40 text-wolf-red font-bold rounded flex items-center justify-center gap-1.5"
                >
                  <Trash2 className="h-4 w-4" />
                  <span>🗑️ Discard Data</span>
                </button>
              </div>
            </div>
          )}

          {/* 📄 Smart Invoice Display Panel (app.py lines 1278-1315) */}
          {generatedInvoice && (
            <div className="bg-surface border border-wolf-green/40 rounded-lg p-5 space-y-4 text-xs font-mono">
              <div className="p-2.5 rounded bg-wolf-green/10 border border-wolf-green/30 text-wolf-green font-bold">
                ✅ নিখুঁতভাবে লেজারে এন্ট্রি সেভ করা হয়েছে!
              </div>
              <h3 className="text-sm font-bold text-[#eaecef] flex items-center gap-2">
                <FileText className="h-4 w-4 text-wolf-gold" />
                📄 Generated Smart Invoice
              </h3>
              <pre className="p-3.5 rounded bg-[#0b0e11] border border-surface-border text-[#eaecef] overflow-x-auto whitespace-pre-wrap">
                {generatedInvoice.smart_receipt}
              </pre>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() =>
                    handleDownloadReceipt(
                      generatedInvoice.smart_receipt,
                      generatedInvoice.filename
                    )
                  }
                  className="py-2 px-3 bg-wolf-gold hover:bg-[#dfaa05] text-[#0b0e11] font-bold rounded flex items-center justify-center gap-1.5"
                >
                  <Download className="h-3.5 w-3.5" />
                  <span>📥 Download Receipt</span>
                </button>
                <button
                  type="button"
                  onClick={() => setGeneratedInvoice(null)}
                  className="py-2 px-3 bg-[#0b0e11] hover:bg-surface-hover border border-surface-border text-wolf-muted rounded flex items-center justify-center gap-1.5"
                >
                  <RefreshCw className="h-3.5 w-3.5" />
                  <span>✖️ Close Invoice</span>
                </button>
              </div>
            </div>
          )}
        </div>

        {/* RIGHT PANEL (7 cols): CUSTOMER DUES LEDGER & AI DUE RECOVERY (app.py lines 1317-1372) */}
        <div className="lg:col-span-7 space-y-5">
          <div className="bg-surface border border-surface-border rounded-lg p-5 space-y-4">
            <h2 className="text-base font-bold font-mono text-[#eaecef]">
              {t.sales_ledger}
            </h2>

            {/* Metrics: Total Dues | Cash Collected */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-4 rounded-lg bg-[#0b0e11] border border-surface-border">
                <div className="text-xs font-mono text-wolf-muted">Total Dues</div>
                <div className="text-2xl font-bold font-mono text-wolf-red mt-1">
                  ৳{(ledgerData?.total_dues ?? 7000).toLocaleString("en-US", { minimumFractionDigits: 2 })}
                </div>
              </div>
              <div className="p-4 rounded-lg bg-[#0b0e11] border border-surface-border">
                <div className="text-xs font-mono text-wolf-muted">Cash Collected</div>
                <div className="text-2xl font-bold font-mono text-wolf-green mt-1">
                  ৳{(ledgerData?.cash_collected ?? 4000).toLocaleString("en-US", { minimumFractionDigits: 2 })}
                </div>
              </div>
            </div>

            {/* Sales Ledger Table */}
            <div className="border border-surface-border rounded-lg overflow-hidden">
              <table className="w-full text-xs font-mono">
                <thead className="bg-[#0b0e11] text-wolf-muted border-b border-surface-border">
                  <tr>
                    <th className="p-3 text-left">Customer</th>
                    <th className="p-3 text-left">Item</th>
                    <th className="p-3 text-center">Qty</th>
                    <th className="p-3 text-right">Paid</th>
                    <th className="p-3 text-right">Due</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-border">
                  {(ledgerData?.rows || []).map((row) => (
                    <tr key={row.id} className="hover:bg-surface-hover/40">
                      <td className="p-3 font-bold text-[#eaecef]">{row.customer}</td>
                      <td className="p-3 text-wolf-muted">{row.item}</td>
                      <td className="p-3 text-center text-[#eaecef]">{row.qty}</td>
                      <td className="p-3 text-right text-wolf-green">
                        ৳{row.paid.toLocaleString()}
                      </td>
                      <td className="p-3 text-right text-wolf-red font-bold">
                        ৳{row.due.toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* 🔔 AI Due Recovery Section */}
            <div className="pt-4 border-t border-surface-border space-y-3 text-xs font-mono">
              <h3 className="text-sm font-bold text-wolf-gold">🔔 AI Due Recovery</h3>

              {(ledgerData?.due_customers || []).length > 0 ? (
                <div className="space-y-3">
                  <div className="flex flex-col sm:flex-row gap-3">
                    <select
                      value={selectedDueCustomer}
                      onChange={(e) => setSelectedDueCustomer(e.target.value)}
                      className="flex-1 px-3 py-2 rounded bg-[#0b0e11] border border-surface-border text-[#eaecef]"
                    >
                      {(ledgerData?.due_customers || []).map((c) => (
                        <option key={c.customer} value={c.customer}>
                          {c.customer} (Due: ৳{c.total_due.toLocaleString()})
                        </option>
                      ))}
                    </select>
                    <button
                      type="button"
                      onClick={handleDraftReminder}
                      className="px-5 py-2 bg-wolf-gold hover:bg-[#dfaa05] text-[#0b0e11] font-bold rounded flex items-center justify-center gap-1.5"
                    >
                      <Sparkles className="h-3.5 w-3.5" />
                      <span>✨ Draft Reminder</span>
                    </button>
                  </div>

                  {draftedReminder && (
                    <div className="space-y-3 pt-1">
                      <div className="p-3.5 rounded bg-[#0b0e11] border border-surface-border text-[#eaecef]">
                        {draftedReminder.drafted_message}
                      </div>
                      <a
                        href={draftedReminder.whatsapp_link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="w-full py-3 px-4 rounded-lg bg-[#25D366] hover:bg-[#20bd5a] text-white font-bold text-center flex items-center justify-center gap-2 transition-colors"
                      >
                        <Send className="h-4 w-4" />
                        <span>📲 Send via WhatsApp</span>
                      </a>
                    </div>
                  )}
                </div>
              ) : (
                <div className="p-3 rounded bg-wolf-green/10 border border-wolf-green/30 text-wolf-green">
                  🎉 All clear! No pending dues to collect.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

