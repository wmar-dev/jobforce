"use client";

import useSWR from "swr";
import { getDashboard } from "@/lib/api";
import type { DashboardSummary } from "@/lib/types";

export function useDashboard() {
  return useSWR<DashboardSummary>("/api/dashboard", getDashboard, {
    refreshInterval: 30_000,
  });
}
