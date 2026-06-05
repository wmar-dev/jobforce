"use client";

import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import useSWR from "swr";
import { useJobs } from "@/hooks/useJobs";
import { JobTable } from "@/components/jobs/JobTable";
import { getCompanies, bulkArchive } from "@/lib/api";
import type { PipelineStatus, RoleType, Company } from "@/lib/types";
import type { JobSortKey, SortDir } from "@/lib/api";

const VALID_STATUSES = new Set<PipelineStatus>([
  "saved", "applied", "interviewing", "offer", "rejected", "withdrawn",
  "archived", "shortlisted",
]);

const STATUS_TABS: Array<{ value: PipelineStatus | "all"; label: string }> = [
  { value: "all", label: "Active" },
  { value: "shortlisted", label: "Shortlisted" },
  { value: "saved", label: "Saved" },
  { value: "applied", label: "Applied" },
  { value: "interviewing", label: "Interviewing" },
  { value: "offer", label: "Offer" },
  { value: "rejected", label: "Rejected" },
  { value: "withdrawn", label: "Withdrawn" },
  { value: "archived", label: "Archived" },
];

const PAGE_SIZE = 50;

function JobsPageInner() {
  const searchParams = useSearchParams();
  const initialStatus = ((): PipelineStatus | "all" => {
    const s = searchParams.get("status");
    return s && VALID_STATUSES.has(s as PipelineStatus) ? (s as PipelineStatus) : "all";
  })();
  const [status, setStatus] = useState<PipelineStatus | "all">(initialStatus);
  const [companyId, setCompanyId] = useState<number | "">("");
  const [location, setLocation] = useState("");
  const [roleType, setRoleType] = useState<RoleType | "">("");
  const [sortBy, setSortBy] = useState<JobSortKey>("fit_score");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [page, setPage] = useState(0);
  const [bulkArchiveMsg, setBulkArchiveMsg] = useState<string | null>(null);
  const [isBulkArchiving, setIsBulkArchiving] = useState(false);

  function resetPage() { setPage(0); }

  const { data: companies } = useSWR<Company[]>("companies", getCompanies);

  const { data, isLoading, error, mutate: mutateJobs } = useJobs({
    status: status === "all" ? undefined : status,
    company_id: companyId || undefined,
    location: location || undefined,
    role_type: roleType || undefined,
    sort_by: sortBy,
    sort_dir: sortDir,
    limit: PAGE_SIZE,
    offset: page * PAGE_SIZE,
  });

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 0;

  function handleSort(key: JobSortKey) {
    if (key === sortBy) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortBy(key);
      setSortDir(key === "fit_score" || key === "created_at" ? "desc" : "asc");
    }
    resetPage();
  }

  async function handleBulkArchive() {
    setIsBulkArchiving(true);
    setBulkArchiveMsg(null);
    try {
      const result = await bulkArchive(companyId || undefined);
      setBulkArchiveMsg(`Archived ${result.archived_count} low-score job${result.archived_count !== 1 ? "s" : ""}.`);
      await mutateJobs();
    } catch {
      setBulkArchiveMsg("Bulk archive failed. Is the backend running?");
    } finally {
      setIsBulkArchiving(false);
    }
  }

  return (
    <div>
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-1">
          <span className="text-2xl">🔭</span>
          <h1 className="text-2xl font-bold text-white">Scout</h1>
          <span className="text-gray-500">Job Discovery</span>
        </div>
        <p className="text-gray-400 text-sm ml-9">
          Job listings captured via Chrome extension or Playwright MCP skill.
        </p>
      </div>

      {/* Status filter tabs */}
      <div className="flex gap-1 mb-4 border-b border-gray-800 pb-0 flex-wrap">
        {STATUS_TABS.map((tab) => (
          <button
            key={tab.value}
            onClick={() => { setStatus(tab.value); resetPage(); setBulkArchiveMsg(null); }}
            className={`px-3 py-2 text-sm rounded-t transition-colors ${
              status === tab.value
                ? "bg-gray-800 text-emerald-400 border-b-2 border-emerald-400"
                : "text-gray-400 hover:text-white"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Secondary filters */}
      <div className="flex gap-3 mb-4 flex-wrap">
        <select
          value={companyId}
          onChange={(e) => { setCompanyId(e.target.value ? Number(e.target.value) : ""); resetPage(); }}
          className="px-3 py-1.5 text-sm bg-gray-800 border border-gray-700 rounded text-gray-200 focus:outline-none focus:border-emerald-500 w-44"
        >
          <option value="">All companies</option>
          {companies?.map((c) => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
        <input
          type="text"
          placeholder="Filter by location..."
          value={location}
          onChange={(e) => { setLocation(e.target.value); resetPage(); }}
          className="px-3 py-1.5 text-sm bg-gray-800 border border-gray-700 rounded text-gray-200 placeholder-gray-500 focus:outline-none focus:border-emerald-500 w-48"
        />
        <select
          value={roleType}
          onChange={(e) => { setRoleType(e.target.value as RoleType | ""); resetPage(); }}
          className="px-3 py-1.5 text-sm bg-gray-800 border border-gray-700 rounded text-gray-200 focus:outline-none focus:border-emerald-500"
        >
          <option value="">All role types</option>
          <option value="full-time">Full-time</option>
          <option value="part-time">Part-time</option>
          <option value="contract">Contract</option>
          <option value="internship">Internship</option>
          <option value="other">Other</option>
        </select>
        <button
          onClick={handleBulkArchive}
          disabled={isBulkArchiving}
          className="px-3 py-1.5 text-sm bg-gray-800 border border-gray-700 rounded text-gray-400 hover:text-white hover:border-gray-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          title={companyId ? "Archive low-score saved jobs for selected company" : "Archive all saved jobs with fit score below 50"}
        >
          {isBulkArchiving ? "Archiving..." : "Bulk Archive Low Scores"}
        </button>
        {bulkArchiveMsg && (
          <span className="text-xs text-gray-400 self-center">{bulkArchiveMsg}</span>
        )}
      </div>

      {/* Results */}
      {isLoading && !data && (
        <div className="text-gray-500 text-sm py-8 text-center">Loading jobs...</div>
      )}
      {error && (
        <div className="text-red-400 text-sm py-4">
          Failed to load jobs. Is the backend running?
        </div>
      )}
      {data && (
        <>
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs text-gray-500">
              {data.total} listing{data.total !== 1 ? "s" : ""}
              {totalPages > 1 && ` · page ${page + 1} of ${totalPages}`}
            </span>
          </div>
          <JobTable
            jobs={data.items}
            sortBy={sortBy}
            sortDir={sortDir}
            onSort={handleSort}
          />
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-6">
              <button
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
                className="px-3 py-1.5 text-sm bg-gray-800 border border-gray-700 rounded text-gray-300 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              >
                ← Prev
              </button>
              <span className="text-xs text-gray-500 tabular-nums">
                {page + 1} / {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
                className="px-3 py-1.5 text-sm bg-gray-800 border border-gray-700 rounded text-gray-300 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              >
                Next →
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default function JobsPage() {
  return (
    <Suspense>
      <JobsPageInner />
    </Suspense>
  );
}
