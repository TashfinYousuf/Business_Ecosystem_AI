/**
 * frontend/web/next.config.ts
 * Cleaned and validated configuration for Next.js 15.
 */

import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Note: Only verified experimental keys are placed within experimental block
  experimental: {
    // If React compiler is desired in Next 15, it lives inside experimental
  },
};

export default nextConfig;