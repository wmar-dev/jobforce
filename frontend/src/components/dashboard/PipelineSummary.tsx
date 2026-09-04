"use client";

import Link from "next/link";
import type { PipelineStatus } from "@/lib/types";

const STATUS_CONFIG: Record<
  Exclude<PipelineStatus, "archived">,
  { label: string; bg: string; text: string; border: string }
> = {
  saved: { label: "Saved", bg: "bg-gray-900", text: "text-gray-200", border: "border-gray-700" },
  shortlisted: { label: "Shortlisted", bg: "bg-amber-950", text: "text-amber-300", border: "border-amber-800" },
  applied: { label: "Applied", bg: "bg-blue-950", text: "text-blue-300", border: "border-blue-800" },
  interviewing: {
    label: "Interviewing",
    bg: "bg-yellow-950",
    text: "text-yellow-300",
    border: "border-yellow-800",
  },
  offer: { label: "Offer", bg: "bg-green-950", text: "text-green-300", border: "border-green-800" },
  rejected: {
    label: "Rejected",
    bg: "bg-red-950",
    text: "text-red-300",
    border: "border-red-900",
  },
  withdrawn: {
    label: "Withdrawn",
    bg: "bg-purple-950",
    text: "text-purple-300",
    border: "border-purple-900",
  },
};

interface PipelineSummaryProps {
  counts: Record<Exclude<PipelineStatus, "archived">, number>;
}

export function PipelineSummary({ counts }: PipelineSummaryProps) {
  const statuses: Array<Exclude<PipelineStatus, "archived">> = [
    "saved",
    "shortlisted",
    "applied",
    "interviewing",
    "offer",
    "rejected",
    "withdrawn",
  ];

  return (
    <div className="grid grid-cols-3 sm:grid-cols-7 gap-3">
      {statuses.map((status) => {
        const cfg = STATUS_CONFIG[status];
        const count = counts[status] ?? 0;
        return (
          <Link
            key={status}
            href={`/jobs?status=${status}`}
            className={`${cfg.bg} border ${cfg.border} rounded-lg p-3 text-center hover:brightness-125 transition-all`}
          >
            <div className={`text-2xl font-bold font-mono ${cfg.text}`}>{count}</div>
            <div className="text-xs text-gray-500 mt-1">{cfg.label}</div>
          </Link>
        );
      })}
    </div>
  );
}
