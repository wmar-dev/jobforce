import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Hero agent theme tokens
        scout: {
          DEFAULT: "#10b981",  // emerald-500 — discovery green
          light: "#d1fae5",
          dark: "#065f46",
        },
        oracle: {
          DEFAULT: "#8b5cf6",  // violet-500 — wisdom purple
          light: "#ede9fe",
          dark: "#4c1d95",
        },
        forge: {
          DEFAULT: "#f59e0b",  // amber-500 — crafting gold
          light: "#fef3c7",
          dark: "#92400e",
        },
        coach: {
          DEFAULT: "#3b82f6",  // blue-500 — coaching blue
          light: "#dbeafe",
          dark: "#1e3a8a",
        },
        hq: {
          DEFAULT: "#ef4444",  // red-500 — command red
          light: "#fee2e2",
          dark: "#991b1b",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
  plugins: [],
};

export default config;
