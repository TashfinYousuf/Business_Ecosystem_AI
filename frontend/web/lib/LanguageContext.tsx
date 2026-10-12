"use client";

/**
 * frontend/web/lib/LanguageContext.tsx
 * Provides the exact Enterprise Bilingual UI/UX Dictionary (EN / BN) and
 * Session Persistence / Auth State from legacy-streamlit-mvp/app.py.
 */

import React, { createContext, useContext, useEffect, useState } from "react";

export type LanguageCode = "EN" | "BN";

export const TEXT: Record<LanguageCode, Record<string, string>> = {
  EN: {
    menu_command: "Command Center ⚡",
    menu_terminal: "Live Market 🔴",
    menu_overview: "Market Overview",
    menu_radar: "Trusted Suppliers 🛡️",
    menu_analysis: "Top Selling Items",
    menu_risk: "Safe Investment Guide",
    menu_validator: "Start New Business",
    menu_scanner: "Smart Memo Scanner",
    menu_ledger: "Order Inbox 📥",
    menu_rag: "Document Chat AI",

    term_title: "⚡ Live Market Terminal",
    term_cap: "Track live wholesale prices and find the cheapest deals in the market.",
    vol_title: "Market Heat",
    sentiment_title: "Buyer Mood",
    margin_title: "Avg. Profit",
    tab_gainers: "🔥 High Demand (Buy Now)",
    tab_losers: "🩸 Slow Moving (Avoid)",
    tab_arbitrage: "💸 Cheapest Deals",
    btn_scrape: "🔄 Scan Live Market",
    msg_success: "✅ Live Data Fetched!",

    over_title: "🌍 Market Overview",
    over_cap: "Track your live stock and global import factors.",

    scan_title: "📸 Auto Memo Entry",
    scan_cap: "Upload memos or voice notes. AI will update your stock automatically.",

    sales_title: "Customer Orders & Dues 🧾",
    sales_cap: "Record sales easily. AI tracks your cash, dues, and stock.",
    sales_record: "📥 Order Inbox",
    sales_info: 'Record voice or type: "Sold 5 AirPods to Tuhin Bhai at 600 tk."',
    btn_process_sale: "🧠 Process Order",
    sales_ledger: "Customer Dues 📒",
  },
  BN: {
    menu_command: "কমান্ড সেন্টার ⚡",
    menu_terminal: "লাইভ মার্কেট 🔴",
    menu_overview: "মার্কেট ও স্টক",
    menu_radar: "নির্ভরযোগ্য সাপ্লায়ার 🛡️",
    menu_analysis: "বেস্ট সেলিং প্রোডাক্ট",
    menu_risk: "নিরাপদ ইনভেস্টমেন্ট",
    menu_validator: "নতুন ব্যবসার আইডিয়া",
    menu_scanner: "অটো মেমো এন্ট্রি",
    menu_ledger: "অর্ডার ইনবক্স 📥",
    menu_rag: "ডকুমেন্ট এআই (PDF)",

    term_title: "⚡ লাইভ মার্কেট টার্মিনাল",
    term_cap: "পাইকারি বাজারের লাইভ দাম এবং সবচেয়ে সস্তা ডিলগুলো খুঁজুন।",
    vol_title: "মার্কেটের অবস্থা",
    sentiment_title: "ক্রেতাদের মুড",
    margin_title: "গড় লাভ",
    tab_gainers: "🔥 প্রচুর চাহিদা (কিনুন)",
    tab_losers: "🩸 বিক্রি কম (এড়িয়ে চলুন)",
    tab_arbitrage: "💸 সস্তা ডিল (অফার)",
    btn_scrape: "🔄 লাইভ মার্কেট স্ক্যান করুন",
    msg_success: "✅ ডাটা আপডেট হয়েছে!",

    over_title: "🌍 মার্কেট ও স্টক ওভারভিউ",
    over_cap: "আপনার বর্তমান স্টক এবং গ্লোবাল ইমপোর্ট রেট ট্র্যাক করুন।",

    scan_title: "📸 অটো মেমো ও স্টক এন্ট্রি",
    scan_cap: "মেমো বা ভয়েস দিন, এআই অটোমেটিক আপনার স্টকে মাল তুলে দিবে।",

    sales_title: "অর্ডার এবং কাস্টমার খাতা 🧾",
    sales_cap: "সহজে বেচাকেনা রেকর্ড করুন। এআই আপনার ক্যাশ এবং বাকি হিসাব রাখবে।",
    sales_record: "📥 অর্ডার ইনবক্স",
    sales_info: 'ভয়েস দিন বা লিখুন: "তুহিন ভাইকে ৬০০ টাকা করে ৫টা এয়ারপডস দিলাম।"',
    btn_process_sale: "🧠 অর্ডার প্রসেস করুন",
    sales_ledger: "কাস্টমারের বাকি 📒",
  },
};

interface SessionState {
  logged_in: boolean;
  username: string;
  email: string;
  token?: string;
}

interface LanguageContextValue {
  language: LanguageCode;
  setLanguage: (lang: LanguageCode) => void;
  t: Record<string, string>;
  session: SessionState;
  saveSession: (session: SessionState) => void;
  clearSession: () => void;
}

const LanguageContext = createContext<LanguageContextValue | undefined>(undefined);

const STORAGE_KEY = "tradewolf_session_cache";
const LANG_KEY = "tradewolf_language";

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguageState] = useState<LanguageCode>("EN");
  const [session, setSessionState] = useState<SessionState>({
    logged_in: true,
    username: "Founder",
    email: "admin@tradewolf.com",
  });

  useEffect(() => {
    try {
      const savedLang = localStorage.getItem(LANG_KEY) as LanguageCode | null;
      if (savedLang === "EN" || savedLang === "BN") {
        setLanguageState(savedLang);
      }
      const savedSession = localStorage.getItem(STORAGE_KEY);
      if (savedSession) {
        const parsed = JSON.parse(savedSession);
        if (typeof parsed.logged_in === "boolean") {
          setSessionState(parsed);
        }
      }
    } catch {
      // Ignore storage access errors
    }
  }, []);

  const setLanguage = (lang: LanguageCode) => {
    setLanguageState(lang);
    try {
      localStorage.setItem(LANG_KEY, lang);
    } catch {
      // Ignore
    }
  };

  const saveSession = (newSession: SessionState) => {
    setSessionState(newSession);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(newSession));
    } catch {
      // Ignore
    }
  };

  const clearSession = () => {
    const loggedOut = { logged_in: false, username: "", email: "" };
    setSessionState(loggedOut);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(loggedOut));
    } catch {
      // Ignore
    }
  };

  return (
    <LanguageContext.Provider
      value={{
        language,
        setLanguage,
        t: TEXT[language],
        session,
        saveSession,
        clearSession,
      }}
    >
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const ctx = useContext(LanguageContext);
  if (!ctx) {
    return {
      language: "EN" as LanguageCode,
      setLanguage: () => {},
      t: TEXT.EN,
      session: { logged_in: true, username: "Founder", email: "admin@tradewolf.com" },
      saveSession: () => {},
      clearSession: () => {},
    };
  }
  return ctx;
}

