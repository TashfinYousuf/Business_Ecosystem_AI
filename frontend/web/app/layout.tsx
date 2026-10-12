/**
 * frontend/web/app/layout.tsx
 * Root Application Shell with System Status Indicator & High-Density Dark Matte Navigation.
 */

import type { Metadata } from "next";
import "./globals.css";
import React from "react";
import { LanguageProvider } from "../lib/LanguageContext";
import AppNavigationShell from "../components/AppNavigationShell";

export const metadata: Metadata = {
  title: "Trade Wolf OS | SME Commerce Terminal",
  description: "AI-Native Commerce Operating System for Emerging Markets",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="bn" className="dark">
      <body className="bg-background text-[#eaecef] min-h-screen flex flex-col font-sans selection:bg-wolf-gold/20 selection:text-wolf-gold">
        <LanguageProvider>
          <AppNavigationShell>{children}</AppNavigationShell>
        </LanguageProvider>
      </body>
    </html>
  );
}