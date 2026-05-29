"use client";

import { useState } from "react";
import type { JobListing } from "@/lib/types";
import { StatusBadge } from "./StatusBadge";
import Link from "next/link";

type SortKey = "title" | "company" | "location" | "status" | "fit_score" | "captured";
type SortDir = "asc" | "desc";

function sortJobs(jobs: JobListing[], key: SortKey, dir: SortDir): JobListing[] {
  return [...jobs].sort((a, b) => {
    let av: string | number | null, bv: string | number | null;
    switch (key) {
      case "title":    av = a.title;          bv = b.title;          break;
      case "company":  av = a.company.name;   bv = b.company.name;   break;
      case "location": av = a.location ?? ""; bv = b.location ?? ""; break;
      case "status":   av = a.status;         bv = b.status;         break;
      case "fit_score":
        // nulls last regardless of direction
        if (a.fit_score == null && b.fit_score == null) return 0;
        if (a.fit_score == null) return 1;
        if (b.fit_score == null) return -1;
        av = a.fit_score; bv = b.fit_score; break;
      case "captured":
        av = a.crawled_at ?? a.created_at;
        bv = b.crawled_at ?? b.created_at;
        break;
    }
    if (av! < bv!) return dir === "asc" ? -1 : 1;
    if (av! > bv!) return dir === "asc" ? 1 : -1;
    return 0;
  });
}

function SortIcon({ active, dir }: { active: boolean; dir: SortDir }) {
  if (!active) return <span className="ml-1 text-gray-700">↕</span>;
  return <span className="ml-1 text-emerald-400">{dir === "asc" ? "↑" : "↓"}</span>;
}

interface JobTableProps {
  jobs: JobListing[];
}

export function JobTable({ jobs }: JobTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>("fit_score");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  function handleSort(key: SortKey) {
    if (key === sortKey) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir(key === "fit_score" || key === "captured" ? "desc" : "asc");
    }
  }

  const sorted = sortJobs(jobs, sortKey, sortDir);

  if (jobs.length === 0) {
    return (
      <div className="text-center py-16 text-gray-500">
        <div className="text-4xl mb-3">🔭</div>
        <div className="text-lg font-medium">No jobs captured yet</div>
        <div className="text-sm mt-1">
          Use the Chrome extension or Playwright MCP skill to capture job listings.
        </div>
      </div>
    );
  }

  function Th({ col, label, last }: { col: SortKey; label: string; last?: boolean }) {
    return (
      <th
        className={`pb-3 ${last ? "" : "pr-4"} font-medium cursor-pointer select-none hover:text-white transition-colors`}
        onClick={() => handleSort(col)}
      >
        {label}<SortIcon active={sortKey === col} dir={sortDir} />
      </th>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-800 text-gray-400 text-left">
            <Th col="title"     label="Title" />
            <Th col="company"   label="Company" />
            <Th col="location"  label="Location" />
            <Th col="status"    label="Status" />
            <Th col="fit_score" label="Fit Score" />
            <Th col="captured"  label="Captured" last />
          </tr>
        </thead>
        <tbody>
          {sorted.map((job) => (
            <tr
              key={job.id}
              className="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors"
            >
              <td className="py-3 pr-4">
                <Link
                  href={`/jobs/${job.id}`}
                  className="text-emerald-400 hover:text-emerald-300 font-medium"
                >
                  {job.title}
                </Link>
              </td>
              <td className="py-3 pr-4 text-gray-300">{job.company.name}</td>
              <td className="py-3 pr-4 text-gray-400">{job.location ?? "—"}</td>
              <td className="py-3 pr-4">
                <StatusBadge status={job.status} />
              </td>
              <td className="py-3 pr-4">
                {job.fit_scored && job.fit_score != null ? (
                  <span className="text-violet-300 font-mono">
                    {Math.round(job.fit_score * 100)}%
                    {job.fit_confidence && (
                      <span className="ml-1 text-xs text-gray-500">
                        ({job.fit_confidence})
                      </span>
                    )}
                  </span>
                ) : (
                  <span className="text-gray-600 text-xs">Not scored</span>
                )}
              </td>
              <td className="py-3 text-gray-500 text-xs">
                {job.crawled_at
                  ? new Date(job.crawled_at).toLocaleDateString()
                  : new Date(job.created_at).toLocaleDateString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
