"use client";

import type { JobListing } from "@/lib/types";
import { StatusBadge } from "./StatusBadge";
import Link from "next/link";
import { StickyNote } from "lucide-react";
import type { JobSortKey, SortDir } from "@/lib/api";
import { patchJobStatus } from "@/lib/api";
import { useSWRConfig } from "swr";

function SortIcon({ active, dir }: { active: boolean; dir: SortDir }) {
  if (!active) return <span className="ml-1 text-gray-700">↕</span>;
  return <span className="ml-1 text-emerald-400">{dir === "asc" ? "↑" : "↓"}</span>;
}

interface JobTableProps {
  jobs: JobListing[];
  sortBy: JobSortKey;
  sortDir: SortDir;
  onSort: (key: JobSortKey) => void;
}

export function JobTable({ jobs, sortBy, sortDir, onSort }: JobTableProps) {
  const { mutate } = useSWRConfig();

  async function handleAction(jobId: number, action: "archived" | "shortlisted" | "saved") {
    // Optimistically remove/update the row so the list doesn't jump to the top on revalidation
    mutate(
      ([key]: [string]) => key === "/api/jobs",
      (cached: { items: JobListing[]; total: number } | undefined) => {
        if (!cached) return cached;
        const items = cached.items.filter((j) => j.id !== jobId);
        return { ...cached, items, total: cached.total - 1 };
      },
      { revalidate: false }
    );
    await patchJobStatus(jobId, action);
    mutate(([key]: [string]) => key === "/api/jobs", undefined, { revalidate: true });
  }

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

  function Th({ col, label, sortable, last }: { col: JobSortKey | null; label: string; sortable?: boolean; last?: boolean }) {
    return (
      <th
        className={`pb-3 ${last ? "" : "pr-4"} font-medium ${sortable && col ? "cursor-pointer select-none hover:text-white transition-colors" : ""}`}
        onClick={() => sortable && col && onSort(col)}
      >
        {label}{sortable && col && <SortIcon active={sortBy === col} dir={sortDir} />}
      </th>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-800 text-gray-400 text-left">
            <Th col="title"      label="Title"     sortable />
            <Th col="company"    label="Company"   sortable />
            <Th col={null}       label="Location" />
            <Th col="status"     label="Status"    sortable />
            <Th col="fit_score"  label="Fit Score" sortable />
            <Th col="created_at" label="Captured"  sortable />
            <Th col={null}       label=""          last />
          </tr>
        </thead>
        <tbody>
          {jobs.map((job) => (
            <tr
              key={job.id}
              className="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors"
            >
              <td className="py-3 pr-4">
                <Link
                  href={`/jobs/${job.id}`}
                  className="text-emerald-400 hover:text-emerald-300 font-medium inline-flex items-center gap-1.5"
                >
                  {job.title}
                  {job.has_note && (
                    <StickyNote size={12} className="text-yellow-500 flex-shrink-0" />
                  )}
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
              <td className="py-3 pr-4 text-gray-500 text-xs">
                {job.crawled_at
                  ? new Date(job.crawled_at).toLocaleDateString()
                  : new Date(job.created_at).toLocaleDateString()}
              </td>
              <td className="py-3 text-right">
                <span className="inline-flex gap-1">
                  {job.status !== "shortlisted" && job.status !== "applied" && job.status !== "interviewing" && job.status !== "offer" && job.status !== "rejected" && job.status !== "withdrawn" && (
                    <button
                      onClick={() => handleAction(job.id, "shortlisted")}
                      className="px-1.5 py-0.5 text-xs rounded bg-amber-900/50 text-amber-300 hover:bg-amber-800/60 transition-colors"
                      title="Shortlist this job"
                    >
                      ★
                    </button>
                  )}
                  {job.status === "shortlisted" && (
                    <button
                      onClick={() => handleAction(job.id, "saved")}
                      className="px-1.5 py-0.5 text-xs rounded bg-amber-800 text-amber-200 hover:bg-amber-700 transition-colors"
                      title="Remove from shortlist"
                    >
                      ★
                    </button>
                  )}
                  {job.status !== "archived" && job.status !== "applied" && job.status !== "interviewing" && job.status !== "offer" && job.status !== "rejected" && job.status !== "withdrawn" && (
                    <button
                      onClick={() => handleAction(job.id, "archived")}
                      className="px-1.5 py-0.5 text-xs rounded bg-gray-700 text-gray-400 hover:bg-gray-600 hover:text-gray-200 transition-colors"
                      title="Archive this job"
                    >
                      ✕
                    </button>
                  )}
                  {job.status === "archived" && (
                    <button
                      onClick={() => handleAction(job.id, "saved")}
                      className="px-1.5 py-0.5 text-xs rounded bg-gray-700 text-gray-400 hover:bg-gray-600 hover:text-gray-200 transition-colors"
                      title="Restore from archive"
                    >
                      ↩
                    </button>
                  )}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
