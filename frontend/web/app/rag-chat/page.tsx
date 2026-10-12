"use client";

/**
 * frontend/web/app/rag-chat/page.tsx
 * Module 8 from legacy-streamlit-mvp/app.py:
 * 📄 AI Report Analysis (RAG) — Upload any Market Survey (PDF) or Sales Report (CSV)
 * and chat directly with your data using Groq (Fast & Free) or Gemini.
 */

import React, { useState } from "react";
import { Upload, FileText, Send, Sparkles, CheckCircle2, Bot, User } from "lucide-react";
import { processRagDocumentApi, chatWithRagDocumentApi } from "../../lib/api";

const SAMPLE_CSV_DATA = `Product_Name,Category,Dhaka_Wholesale_BDT,Retail_Avg_BDT,Monthly_Units_Sold,Return_Rate_Pct,Top_Hub
AirPods Pro 2 (Master Clone),TWS / Earbuds,1250,1850,1420,4.2%,Multiplan Center
Lenovo LP40 Pro TWS,TWS / Earbuds,550,850,2150,3.1%,Motaleb Plaza
Apple Watch S9 Clone,Smartwatches,2400,3400,680,5.5%,Bashundhara City
K68 RGB Mechanical Keyboard,Accessories,1800,2550,510,2.0%,Multiplan Center
MagSafe Battery Pack 5000mAh,Power Bank,850,1350,940,3.8%,Gulistan Underground`;

export default function DocumentRagChatPage() {
  const [filename, setFilename] = useState("BD_Gadget_Market_Survey_2026.csv");
  const [rawText, setRawText] = useState(SAMPLE_CSV_DATA);
  const [aiModel, setAiModel] = useState<"groq" | "gemini">("groq");
  const [processing, setProcessing] = useState(false);
  const [isProcessed, setIsProcessed] = useState(false);
  const [chunkCount, setChunkCount] = useState(0);

  const [query, setQuery] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState<
    Array<{ role: "user" | "assistant"; content: string }>
  >([]);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setFilename(file.name);
    const reader = new FileReader();
    reader.onload = () => {
      const text = typeof reader.result === "string" ? reader.result : "";
      setRawText(text || SAMPLE_CSV_DATA);
    };
    reader.readAsText(file);
  };

  const handleProcessDocument = async () => {
    setProcessing(true);
    const res = await processRagDocumentApi(filename, rawText);
    setChunkCount(res.chunk_count);
    setIsProcessed(true);
    setChatHistory([]);
    setProcessing(false);
  };

  const handleSendQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    const currentQuery = query.trim();
    setQuery("");
    setChatHistory((prev) => [...prev, { role: "user", content: currentQuery }]);
    setChatLoading(true);
    const res = await chatWithRagDocumentApi(currentQuery, aiModel);
    setChatHistory((prev) => [...prev, { role: "assistant", content: res.answer }]);
    setChatLoading(false);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-surface-border pb-4">
        <h1 className="text-2xl font-bold font-mono text-[#eaecef]">
          📄 AI Report Analysis (RAG)
        </h1>
        <p className="text-sm text-wolf-muted mt-1">
          Upload any Market Survey (PDF) or Sales Report (CSV) and chat directly with your data.
        </p>
      </div>

      {/* Document Upload & Configuration Expander */}
      <div className="bg-surface border border-surface-border rounded-lg p-5 space-y-4">
        <h2 className="text-sm font-mono font-bold text-wolf-gold uppercase flex items-center gap-2">
          <FileText className="h-4 w-4" />
          📁 Document Upload & Configuration
        </h2>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 text-xs font-mono">
          {/* Upload Column (2 spans) */}
          <div className="lg:col-span-2 space-y-3">
            <label className="block p-6 border-2 border-dashed border-surface-border hover:border-wolf-gold/60 rounded-lg bg-[#0b0e11] text-center cursor-pointer transition-colors">
              <Upload className="h-8 w-8 text-wolf-muted mx-auto mb-2" />
              <span className="text-[#eaecef] font-bold block">
                Upload your PDF or CSV file here
              </span>
              <span className="text-wolf-muted text-[11px] block mt-1">
                Active Document: <strong className="text-wolf-gold">{filename}</strong>
              </span>
              <input
                type="file"
                accept=".pdf,.csv,.txt"
                onChange={handleFileUpload}
                className="hidden"
              />
            </label>

            <div>
              <label className="block text-wolf-muted mb-1">
                Document Text Preview / Editable Context:
              </label>
              <textarea
                rows={4}
                value={rawText}
                onChange={(e) => setRawText(e.target.value)}
                className="w-full p-3 rounded bg-[#0b0e11] border border-surface-border text-[#eaecef] text-[11px] font-mono outline-none"
              />
            </div>
          </div>

          {/* Model Selection & Process Button */}
          <div className="space-y-4 flex flex-col justify-between bg-[#0b0e11] p-4 rounded-lg border border-surface-border">
            <div className="space-y-2">
              <div className="text-wolf-muted font-bold">Select AI Engine:</div>
              <button
                type="button"
                onClick={() => setAiModel("groq")}
                className={`w-full p-2.5 rounded border text-left font-bold transition-colors ${
                  aiModel === "groq"
                    ? "bg-wolf-gold/15 border-wolf-gold text-wolf-gold"
                    : "border-surface-border text-wolf-muted"
                }`}
              >
                ⚡ Groq (Fast & Free — Llama 3.1)
              </button>
              <button
                type="button"
                onClick={() => setAiModel("gemini")}
                className={`w-full p-2.5 rounded border text-left font-bold transition-colors ${
                  aiModel === "gemini"
                    ? "bg-wolf-green/15 border-wolf-green text-wolf-green"
                    : "border-surface-border text-wolf-muted"
                }`}
              >
                ✨ Gemini 2.5 Flash
              </button>
            </div>

            <button
              type="button"
              onClick={handleProcessDocument}
              disabled={processing}
              className="w-full py-3 bg-wolf-gold hover:bg-[#dfaa05] text-[#0b0e11] font-bold rounded-lg transition-colors"
            >
              {processing ? "Building Vector DB..." : "🚀 Process Document"}
            </button>
          </div>
        </div>

        {isProcessed && (
          <div className="p-3 rounded bg-wolf-green/10 border border-wolf-green/30 text-wolf-green text-xs font-mono font-bold flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4" />
            <span>
              ✅ Document processed ({chunkCount} vector chunks indexed)! You can now chat below.
            </span>
          </div>
        )}
      </div>

      {/* Chat with your Data */}
      <div className="bg-surface border border-surface-border rounded-lg p-5 space-y-4">
        <h3 className="text-sm font-mono font-bold text-[#eaecef] uppercase">
          💬 Chat with your Data
        </h3>

        <div className="space-y-3 max-h-96 overflow-y-auto p-3 rounded bg-[#0b0e11] border border-surface-border min-h-[180px]">
          {chatHistory.length === 0 ? (
            <div className="py-12 text-center text-xs font-mono text-wolf-muted">
              {isProcessed
                ? 'Ask any question about the processed report (e.g., "Which product has the highest monthly units sold?")'
                : 'Click "🚀 Process Document" above first, then ask questions here.'}
            </div>
          ) : (
            chatHistory.map((msg, idx) => (
              <div
                key={idx}
                className={`p-3.5 rounded-lg text-xs font-mono leading-relaxed flex items-start gap-3 ${
                  msg.role === "user"
                    ? "bg-surface border border-surface-border text-[#eaecef]"
                    : "bg-wolf-gold/10 border border-wolf-gold/30 text-[#eaecef]"
                }`}
              >
                {msg.role === "user" ? (
                  <User className="h-4 w-4 text-wolf-gold shrink-0 mt-0.5" />
                ) : (
                  <Bot className="h-4 w-4 text-wolf-green shrink-0 mt-0.5" />
                )}
                <div className="whitespace-pre-line">{msg.content}</div>
              </div>
            ))
          )}
          {chatLoading && (
            <div className="text-xs font-mono text-wolf-gold flex items-center gap-2 p-2">
              <Sparkles className="h-4 w-4 animate-spin" />
              <span>Analyzing document context...</span>
            </div>
          )}
        </div>

        <form onSubmit={handleSendQuery} className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a question about the report..."
            className="flex-1 px-4 py-2.5 rounded-lg bg-[#0b0e11] border border-surface-border text-xs font-mono text-[#eaecef] focus:border-wolf-gold outline-none"
          />
          <button
            type="submit"
            disabled={chatLoading}
            className="px-5 py-2.5 bg-wolf-green hover:bg-[#0bb372] text-[#0b0e11] font-mono font-bold text-xs rounded-lg flex items-center gap-2 transition-colors"
          >
            <Send className="h-3.5 w-3.5" />
            <span>Ask AI</span>
          </button>
        </form>
      </div>
    </div>
  );
}

