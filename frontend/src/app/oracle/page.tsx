"use client";

import { useJobs } from "@/hooks/useJobs";
import { StatusBadge } from "@/components/jobs/StatusBadge";
import Link from "next/link";

const CONFIDENCE_STYLES: Record<string, string> = {
  high: "bg-emerald-900 text-emerald-300",
  medium: "bg-yellow-900 text-yellow-300",
  low: "bg-gray-700 text-gray-400",
};

const ACTIVE_STATUSES = ["saved", "applied", "interviewing"];

export default function OraclePage() {
  const { data, isLoading, error } = useJobs();

  const rankedJobs = (data?.items ?? [])
    .filter((j) => ACTIVE_STATUSES.includes(j.status) && j.fit_scored && j.fit_score != null)
    .sort((a, b) => (b.fit_score ?? 0) - (a.fit_score ?? 0));

  const unrankedJobs = (data?.items ?? []).filter(
    (j) => ACTIVE_STATUSES.includes(j.status) && !j.fit_scored
  );

  return (
    <div>
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-1">
          <span className="text-2xl">🔮</span>
          <h1 className="text-2xl font-bold text-white">Oracle</h1>
          <span className="text-gray-500">Job Fit Ranking</span>
        </div>
        <p className="text-gray-400 text-sm ml-9">
          Scores saved jobs against your profile using AI analysis.
        </p>
      </div>

      {/* Claude Code instruction panel */}
      <div className="mb-6 p-4 bg-gray-900 border border-violet-800 rounded-lg">
        <p className="text-sm text-gray-300 font-medium mb-1">
          Run ranking via Claude Code
        </p>
        <code className="text-violet-300 text-sm">/oracle-rank</code>
        <p className="text-xs text-gray-500 mt-2">
          Optionally pass specific job IDs:{" "}
          <code className="text-violet-400">/oracle-rank 2 5 7</code>
        </p>
      </div>

      {isLoading && (
        <div className="text-gray-500 text-sm py-8 text-center">Loading jobs...</div>
      )}

      {error && (
        <div className="text-red-400 text-sm py-4 px-4 bg-red-950 rounded mb-4">
          Failed to load jobs. Is the backend running?
        </div>
      )}

      {/* Ranked jobs */}
      {rankedJobs.length > 0 && (
        <div className="mb-6">
          <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
            Ranked ({rankedJobs.length})
          </h2>
          <div className="space-y-3">
            {rankedJobs.map((job, idx) => (
              <div
                key={job.id}
                className="bg-gray-900 border border-gray-800 rounded-lg p-4"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-center gap-3 min-w-0">
                    <span className="text-gray-500 text-sm font-mono w-6 shrink-0">
                      #{idx + 1}
                    </span>
                    <div className="min-w-0">
                      <Link
                        href={`/jobs/${job.id}`}
                        className="text-violet-300 hover:text-violet-200 font-medium text-sm"
                      >
                        {job.title}
                      </Link>
                      <p className="text-gray-500 text-xs mt-0.5">{job.company.name}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                        CONFIDENCE_STYLES[job.fit_confidence ?? ""] ?? CONFIDENCE_STYLES.low
                      }`}
                    >
                      {job.fit_confidence}
                    </span>
                    <span className="text-violet-300 font-mono text-lg font-bold">
                      {Math.round((job.fit_score ?? 0) * 100)}%
                    </span>
                  </div>
                </div>
                {job.fit_rationale && (
                  <p className="text-gray-400 text-sm mt-2 ml-9">{job.fit_rationale}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Unranked jobs */}
      {unrankedJobs.length > 0 && (
        <div>
          <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
            Not yet ranked ({unrankedJobs.length})
          </h2>
          <div className="space-y-2">
            {unrankedJobs.map((job) => (
              <div
                key={job.id}
                className="flex items-center justify-between gap-4 px-4 py-3 bg-gray-900 border border-gray-800 rounded-lg"
              >
                <div className="min-w-0">
                  <Link
                    href={`/jobs/${job.id}`}
                    className="text-gray-300 hover:text-white text-sm font-medium"
                  >
                    {job.title}
                  </Link>
                  <p className="text-gray-600 text-xs mt-0.5">{job.company.name}</p>
                </div>
                <StatusBadge status={job.status} />
              </div>
            ))}
          </div>
        </div>
      )}

      {!isLoading && !error && rankedJobs.length === 0 && unrankedJobs.length === 0 && (
        <div className="text-center py-16 text-gray-500">
          <div className="text-4xl mb-3">🔮</div>
          <div className="text-lg font-medium">No active jobs to rank</div>
          <div className="text-sm mt-1">Capture some job listings via Scout first.</div>
        </div>
      )}
    </div>
  );
}
