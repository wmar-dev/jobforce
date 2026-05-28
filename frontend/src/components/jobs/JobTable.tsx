"use client";

import type { JobListing } from "@/lib/types";
import { StatusBadge } from "./StatusBadge";
import Link from "next/link";

interface JobTableProps {
  jobs: JobListing[];
}

export function JobTable({ jobs }: JobTableProps) {
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

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-800 text-gray-400 text-left">
            <th className="pb-3 pr-4 font-medium">Title</th>
            <th className="pb-3 pr-4 font-medium">Company</th>
            <th className="pb-3 pr-4 font-medium">Location</th>
            <th className="pb-3 pr-4 font-medium">Status</th>
            <th className="pb-3 pr-4 font-medium">Fit Score</th>
            <th className="pb-3 font-medium">Captured</th>
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
