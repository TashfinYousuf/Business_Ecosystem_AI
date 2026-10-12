/**
 * frontend/web/tailwind.config.ts
 * High-density matte dark theme for Trade Wolf OS.
 */

import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
    "./*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0b0e11",
        surface: {
          DEFAULT: "#181a20",
          hover: "#22262e",
          border: "#2b313a",
        },
        wolf: {
          gold: "#f0b90b",
          green: "#0ecb81",
          red: "#f6465d",
          muted: "#848e9c",
        },
      },
      fontFamily: {
        mono: ["JetBrains Mono", "SF Mono", "monospace"],
        sans: ["Inter", "-apple-system", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;