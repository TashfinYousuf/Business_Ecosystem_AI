"use client";

/**
 * frontend/web/components/AppNavigationShell.tsx
 * Unified Navigation Sidebar, Top Operational Header, Profile Popover,
 * Bilingual Language Switcher (EN / BN), and Auth / OTP Modal.
 * Preserves all existing layout elements while integrating all 9 legacy Streamlit modules.
 */

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  BarChart3,
  BookOpen,
  Box,
  FileText,
  LayoutDashboard,
  Lightbulb,
  LogOut,
  Menu,
  MessageSquare,
  ScanLine,
  ShieldCheck,
  User,
  Wallet,
  X,
} from "lucide-react";
import { useLanguage, LanguageCode } from "../lib/LanguageContext";

export default function AppNavigationShell({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const { language, setLanguage, t, session, saveSession, clearSession } = useLanguage();

  const [profileOpen, setProfileOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [authTab, setAuthTab] = useState<"login" | "signup">("login");
  const [showOtpStep, setShowOtpStep] = useState(false);
  const [tempEmail, setTempEmail] = useState("");
  const [transitioning, setTransitioning] = useState(false);
  const [authError, setAuthError] = useState("");

  // Auth form states
  const [loginEmail, setLoginEmail] = useState("alex@ai.com");
  const [loginPass, setLoginPass] = useState("");
  const [regName, setRegName] = useState("");
  const [regEmail, setRegEmail] = useState("");
  const [regPhone, setRegPhone] = useState("");
  const [regPass, setRegPass] = useState("");
  const [otpInput, setOtpInput] = useState("");

  const navItems = [
    { href: "/", label: t.menu_command, icon: LayoutDashboard },
    { href: "/terminal", label: t.menu_terminal, icon: BarChart3 },
    { href: "/market-overview", label: t.menu_overview, icon: Activity },
    { href: "/trust-radar", label: t.menu_radar, icon: ShieldCheck },
    { href: "/analytics", label: t.menu_analysis, icon: Box },
    { href: "/risk-simulator", label: t.menu_risk, icon: Wallet },
    { href: "/idea-validator", label: t.menu_validator, icon: Lightbulb },
    { href: "/scanner", label: t.menu_scanner, icon: ScanLine },
    { href: "/orders", label: t.menu_ledger, icon: MessageSquare },
    { href: "/rag-chat", label: t.menu_rag, icon: FileText },
  ];

  const handleLoginSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError("");
    if (!loginEmail || !loginPass) {
      setAuthError("Please enter email and password.");
      return;
    }
    const derivedName = loginEmail.split("@")[0] || "Founder";
    saveSession({
      logged_in: true,
      username: derivedName.charAt(0).toUpperCase() + derivedName.slice(1),
      email: loginEmail,
    });
    setTransitioning(true);
    setTimeout(() => {
      setTransitioning(false);
    }, 1200);
  };

  const handleSignupSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError("");
    if (!regName || !regEmail || !regPass) {
      setAuthError("Please fill all required fields.");
      return;
    }
    setTempEmail(regEmail);
    setShowOtpStep(true);
  };

  const handleVerifyOtp = (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError("");
    if (otpInput === "1234") {
      saveSession({
        logged_in: true,
        username: regName || "New User",
        email: tempEmail,
      });
      setShowOtpStep(false);
      setTransitioning(true);
      setTimeout(() => {
        setTransitioning(false);
      }, 1200);
    } else {
      setAuthError("Invalid OTP. Type 1234 for testing.");
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-background text-[#eaecef]">
      {/* Top Operational Bar (Preserves all existing header badges + adds Profile & Language Popover) */}
      <header className="h-14 border-b border-surface-border bg-surface flex items-center justify-between px-4 lg:px-6 sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="lg:hidden p-1.5 rounded bg-[#0b0e11] border border-surface-border text-wolf-muted hover:text-[#eaecef]"
            aria-label="Toggle Navigation"
          >
            {mobileMenuOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
          </button>
          <Link href="/" className="flex items-center gap-3">
            <span className="h-3 w-3 rounded-full bg-wolf-gold animate-pulse"></span>
            <span className="font-mono text-base font-bold tracking-wider text-wolf-gold">
              TRADE WOLF OS
            </span>
          </Link>
          <span className="text-xs px-2 py-0.5 rounded bg-surface-border text-wolf-muted font-mono uppercase">
            v1.0-RC
          </span>
        </div>

        <div className="flex items-center gap-3 text-xs font-mono">
          <div className="hidden md:flex items-center gap-2 px-3 py-1 bg-[#0b0e11] border border-surface-border rounded">
            <span className="h-2 w-2 rounded-full bg-wolf-green"></span>
            <span className="text-wolf-muted">SYNC ENGINE:</span>
            <span className="text-wolf-green font-semibold">CLOUD SYNCED</span>
          </div>
          <div className="hidden sm:block px-3 py-1 bg-[#0b0e11] border border-surface-border rounded text-wolf-muted">
            TENANT: <span className="text-[#eaecef]">SATATA TRADERS (BD-01)</span>
          </div>

          {/* Quick Language Switcher Pill */}
          <div className="flex items-center bg-[#0b0e11] border border-surface-border rounded p-0.5">
            {(["EN", "BN"] as LanguageCode[]).map((lang) => (
              <button
                key={lang}
                type="button"
                onClick={() => setLanguage(lang)}
                className={`px-2 py-0.5 rounded text-[11px] font-mono font-bold transition-colors ${
                  language === lang
                    ? "bg-wolf-gold text-[#0b0e11]"
                    : "text-wolf-muted hover:text-[#eaecef]"
                }`}
              >
                {lang}
              </button>
            ))}
          </div>

          {/* Profile Popover Button (Ported from legacy-streamlit-mvp/app.py lines 350-367) */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setProfileOpen(!profileOpen)}
              className="flex items-center gap-2 px-3.5 py-1.5 rounded-full border border-teal-500/40 bg-gradient-to-r from-teal-500/15 to-emerald-500/5 hover:from-teal-500/25 text-[#eaecef] font-semibold transition-all"
            >
              <User className="h-3.5 w-3.5 text-wolf-gold" />
              <span>👤 {session.logged_in ? session.username || "Profile" : "Sign In"}</span>
            </button>

            {profileOpen && (
              <div className="absolute right-0 mt-2 w-64 bg-surface border border-surface-border rounded-xl shadow-2xl p-4 z-50 space-y-3">
                <div>
                  <div className="font-bold text-sm text-[#eaecef]">
                    {session.logged_in ? session.username : "Guest User"}
                  </div>
                  <div className="text-[11px] text-wolf-muted">Founder / Admin</div>
                </div>

                <div className="border-t border-surface-border pt-2">
                  <div className="text-[11px] font-semibold text-wolf-muted mb-1.5">
                    Language / ভাষা
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    {(["EN", "BN"] as LanguageCode[]).map((lang) => (
                      <button
                        key={lang}
                        type="button"
                        onClick={() => setLanguage(lang)}
                        className={`py-1.5 rounded border text-xs font-mono font-bold ${
                          language === lang
                            ? "bg-wolf-gold/15 border-wolf-gold text-wolf-gold"
                            : "bg-[#0b0e11] border-surface-border text-wolf-muted"
                        }`}
                      >
                        {lang === "EN" ? "🇬🇧 EN" : "🇧🇩 BN"}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="border-t border-surface-border pt-2">
                  {session.logged_in ? (
                    <button
                      type="button"
                      onClick={() => {
                        clearSession();
                        setProfileOpen(false);
                      }}
                      className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded bg-wolf-red hover:bg-wolf-red/90 text-white font-bold text-xs transition-colors"
                    >
                      <LogOut className="h-3.5 w-3.5" />
                      <span>🚪 Log Out</span>
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={() => setProfileOpen(false)}
                      className="w-full py-2 px-3 rounded bg-wolf-gold text-[#0b0e11] font-bold text-xs"
                    >
                      Open Login Screen
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Authentication Screen if user explicitly logged out (Mirrors app.py lines 276-344) */}
      {!session.logged_in ? (
        <div className="flex-1 flex items-center justify-center p-6">
          <div className="w-full max-w-md bg-surface border border-surface-border rounded-xl p-6 shadow-2xl space-y-5">
            <div className="text-center space-y-1">
              <h1 className="text-2xl font-extrabold font-mono text-[#eaecef]">
                📊 AI Business Assistant
              </h1>
              <p className="text-xs text-wolf-muted font-mono">
                Sign in to continue to your Founder Workspace
              </p>
            </div>

            <div className="grid grid-cols-2 gap-2 p-1 bg-[#0b0e11] rounded-lg border border-surface-border text-xs font-mono">
              <button
                type="button"
                onClick={() => {
                  setAuthTab("login");
                  setShowOtpStep(false);
                  setAuthError("");
                }}
                className={`py-2 rounded font-bold transition-colors ${
                  authTab === "login"
                    ? "bg-surface text-wolf-gold border border-surface-border"
                    : "text-wolf-muted hover:text-[#eaecef]"
                }`}
              >
                Log In
              </button>
              <button
                type="button"
                onClick={() => {
                  setAuthTab("signup");
                  setAuthError("");
                }}
                className={`py-2 rounded font-bold transition-colors ${
                  authTab === "signup"
                    ? "bg-surface text-wolf-gold border border-surface-border"
                    : "text-wolf-muted hover:text-[#eaecef]"
                }`}
              >
                Create Account
              </button>
            </div>

            {authError && (
              <div className="p-2.5 rounded bg-wolf-red/10 border border-wolf-red/30 text-wolf-red text-xs font-mono">
                {authError}
              </div>
            )}

            {authTab === "login" ? (
              <form onSubmit={handleLoginSubmit} className="space-y-3 text-xs font-mono">
                <div>
                  <label className="block text-wolf-muted mb-1">Email Address</label>
                  <input
                    type="email"
                    value={loginEmail}
                    onChange={(e) => setLoginEmail(e.target.value)}
                    placeholder="e.g., alex@ai.com"
                    className="w-full px-3 py-2 rounded bg-[#0b0e11] border border-surface-border text-[#eaecef] focus:border-wolf-gold outline-none"
                  />
                </div>
                <div>
                  <label className="block text-wolf-muted mb-1">Password</label>
                  <input
                    type="password"
                    value={loginPass}
                    onChange={(e) => setLoginPass(e.target.value)}
                    placeholder="••••••••"
                    className="w-full px-3 py-2 rounded bg-[#0b0e11] border border-surface-border text-[#eaecef] focus:border-wolf-gold outline-none"
                  />
                </div>
                <button
                  type="submit"
                  className="w-full py-2.5 bg-wolf-gold hover:bg-[#dfaa05] text-[#0b0e11] font-bold rounded transition-colors"
                >
                  Access Dashboard
                </button>
              </form>
            ) : !showOtpStep ? (
              <form onSubmit={handleSignupSubmit} className="space-y-3 text-xs font-mono">
                <div>
                  <label className="block text-wolf-muted mb-1">Full Name</label>
                  <input
                    type="text"
                    value={regName}
                    onChange={(e) => setRegName(e.target.value)}
                    placeholder="Alex Doe"
                    className="w-full px-3 py-2 rounded bg-[#0b0e11] border border-surface-border text-[#eaecef] outline-none"
                  />
                </div>
                <div>
                  <label className="block text-wolf-muted mb-1">Email</label>
                  <input
                    type="email"
                    value={regEmail}
                    onChange={(e) => setRegEmail(e.target.value)}
                    placeholder="alex@ai.com"
                    className="w-full px-3 py-2 rounded bg-[#0b0e11] border border-surface-border text-[#eaecef] outline-none"
                  />
                </div>
                <div>
                  <label className="block text-wolf-muted mb-1">Phone Number</label>
                  <input
                    type="text"
                    value={regPhone}
                    onChange={(e) => setRegPhone(e.target.value)}
                    placeholder="+8801..."
                    className="w-full px-3 py-2 rounded bg-[#0b0e11] border border-surface-border text-[#eaecef] outline-none"
                  />
                </div>
                <div>
                  <label className="block text-wolf-muted mb-1">Create Password</label>
                  <input
                    type="password"
                    value={regPass}
                    onChange={(e) => setRegPass(e.target.value)}
                    className="w-full px-3 py-2 rounded bg-[#0b0e11] border border-surface-border text-[#eaecef] outline-none"
                  />
                </div>
                <button
                  type="submit"
                  className="w-full py-2.5 bg-wolf-green hover:bg-[#0bb372] text-[#0b0e11] font-bold rounded transition-colors"
                >
                  Create AI Account
                </button>
              </form>
            ) : (
              <form onSubmit={handleVerifyOtp} className="space-y-3 text-xs font-mono">
                <div className="p-3 rounded bg-wolf-gold/10 border border-wolf-gold/30 text-wolf-gold">
                  An OTP has been sent to <strong>{tempEmail}</strong>
                </div>
                <div>
                  <label className="block text-wolf-muted mb-1">
                    Enter 4-digit OTP (Type 1234 for testing)
                  </label>
                  <input
                    type="text"
                    maxLength={4}
                    value={otpInput}
                    onChange={(e) => setOtpInput(e.target.value)}
                    placeholder="1234"
                    className="w-full px-3 py-2 rounded bg-[#0b0e11] border border-surface-border text-[#eaecef] tracking-widest text-center text-base font-bold outline-none"
                  />
                </div>
                <button
                  type="submit"
                  className="w-full py-2.5 bg-wolf-green hover:bg-[#0bb372] text-[#0b0e11] font-bold rounded transition-colors"
                >
                  Verify & Login
                </button>
              </form>
            )}
          </div>
        </div>
      ) : transitioning ? (
        <div className="flex-1 flex flex-col items-center justify-center p-6 text-center space-y-2">
          <h2 className="text-2xl font-bold font-mono text-wolf-green">
            Welcome back, {session.username}!
          </h2>
          <p className="text-sm text-wolf-muted font-mono">
            Preparing your personalized dashboard...
          </p>
        </div>
      ) : (
        <div className="flex-1 flex">
          {/* Sidebar Navigation (Ported from legacy-streamlit-mvp/app.py option_menu) */}
          <aside
            className={`${
              mobileMenuOpen ? "fixed inset-y-14 left-0 z-40 w-64" : "hidden lg:flex lg:w-64"
            } flex-col border-r border-surface-border bg-surface shrink-0 select-none`}
          >
            <div className="p-4 border-b border-surface-border text-center">
              <div className="inline-flex items-center justify-center px-3 py-1 rounded-full bg-teal-500/10 border border-teal-500/30 text-[#14B8A6] text-[11px] font-mono font-bold tracking-widest">
                🐺 FOUNDER WORKSPACE
              </div>
            </div>

            <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive =
                  item.href === "/"
                    ? pathname === "/"
                    : pathname?.startsWith(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-xs font-mono transition-all ${
                      isActive
                        ? "bg-wolf-green/15 text-white border-l-4 border-wolf-green font-bold shadow-sm"
                        : "text-wolf-muted hover:text-[#eaecef] hover:bg-surface-hover hover:translate-x-1"
                    }`}
                  >
                    <Icon
                      className={`h-4 w-4 shrink-0 ${
                        isActive ? "text-wolf-green" : "text-wolf-gold/80"
                      }`}
                    />
                    <span className="truncate">{item.label}</span>
                  </Link>
                );
              })}
            </nav>

            <div className="p-3 border-t border-surface-border text-[11px] font-mono text-wolf-muted">
              <div className="flex items-center justify-between">
                <span>AI GATEWAY:</span>
                <span className="text-wolf-green font-semibold">GEMINI + GROQ</span>
              </div>
              <div className="flex items-center justify-between mt-1">
                <span>AEGIS FIREWALL:</span>
                <span className="text-wolf-gold font-semibold">ACTIVE</span>
              </div>
            </div>
          </aside>

          {/* Main Content Area */}
          <main className="flex-1 p-4 md:p-6 max-w-7xl w-full mx-auto overflow-x-hidden">
            {children}
          </main>
        </div>
      )}
    </div>
  );
}

