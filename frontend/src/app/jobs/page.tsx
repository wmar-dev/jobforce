"use client";

import { useState } from "react";
import { useSearchParams } from "next/navigation";
import { useJobs } from "@/hooks/useJobs";
import { JobTable } from "@/components/jobs/JobTable";
import type { PipelineStatus, RoleType } from "@/lib/types";

const VALID_STATUSES = new Set<PipelineStatus>([
  "saved", "applied", "interviewing", "offer", "rejected", "withdrawn",
]);

const STATUS_TABS: Array<{ value: PipelineStatus | "all"; label: string }> = [
  { value: "all", label: "All" },
  { value: "saved", label: "Saved" },
  { value: "applied", label: "Applied" },
  { value: "interviewing", label: "Interviewing" },
  { value: "offer", label: "Offer" },
  { value: "rejected", label: "Rejected" },
  { value: "withdrawn", label: "Withdrawn" },
];

export default function JobsPage() {
  const searchParams = useSearchParams();
  const initialStatus = ((): PipelineStatus | "all" => {
    const s = searchParams.get("status");
    return s && VALID_STATUSES.has(s as PipelineStatus) ? (s as PipelineStatus) : "all";
  })();
  const [status, setStatus] = useState<PipelineStatus | "all">(initialStatus);
  const [location, setLocation] = useState("");
  const [roleType, setRoleType] = useState<RoleType | "">("");

  const { data, isLoading, error } = useJobs({
    status: status === "all" ? undefined : status,
    location: location || undefined,
    role_type: roleType || undefined,
  });

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
      <div className="flex gap-1 mb-4 border-b border-gray-800 pb-0">
        {STATUS_TABS.map((tab) => (
          <button
            key={tab.value}
            onClick={() => setStatus(tab.value)}
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
      <div className="flex gap-3 mb-4">
        <input
          type="text"
          placeholder="Filter by location..."
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          className="px-3 py-1.5 text-sm bg-gray-800 border border-gray-700 rounded text-gray-200 placeholder-gray-500 focus:outline-none focus:border-emerald-500 w-48"
        />
        <select
          value={roleType}
          onChange={(e) => setRoleType(e.target.value as RoleType | "")}
          className="px-3 py-1.5 text-sm bg-gray-800 border border-gray-700 rounded text-gray-200 focus:outline-none focus:border-emerald-500"
        >
          <option value="">All role types</option>
          <option value="full-time">Full-time</option>
          <option value="part-time">Part-time</option>
          <option value="contract">Contract</option>
          <option value="internship">Internship</option>
          <option value="other">Other</option>
        </select>
      </div>

      {/* Results */}
      {isLoading && (
        <div className="text-gray-500 text-sm py-8 text-center">Loading jobs...</div>
      )}
      {error && (
        <div className="text-red-400 text-sm py-4">
          Failed to load jobs. Is the backend running?
        </div>
      )}
      {data && (
        <>
          <div className="text-xs text-gray-500 mb-3">
            {data.total} listing{data.total !== 1 ? "s" : ""}
          </div>
          <JobTable jobs={data.items} />
        </>
      )}
    </div>
  );
}
