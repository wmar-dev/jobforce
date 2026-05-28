"use client";

import { useState } from "react";
import { rankJobs } from "@/lib/api";
import type { OracleRankResult } from "@/lib/types";

const CONFIDENCE_STYLES: Record<string, string> = {
  high: "bg-emerald-900 text-emerald-300",
  medium: "bg-yellow-900 text-yellow-300",
  low: "bg-gray-700 text-gray-400",
};

export default function OraclePage() {
  const [results, setResults] = useState<OracleRankResult[] | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runRanking = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await rankJobs();
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to rank jobs");
    } finally {
      setIsLoading(false);
    }
  };

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

      <div className="mb-6 flex items-center gap-4">
        <button
          onClick={runRanking}
          disabled={isLoading}
          className="px-4 py-2 bg-violet-700 hover:bg-violet-600 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium rounded transition-colors"
        >
          {isLoading ? "Ranking..." : "Run Oracle Ranking"}
        </button>
        {results && (
          <span className="text-xs text-gray-500">
            {results.length} job{results.length !== 1 ? "s" : ""} ranked
          </span>
        )}
      </div>

      {error && (
        <div className="text-red-400 text-sm py-4 px-4 bg-red-950 rounded mb-4">
          {error}
        </div>
      )}

      {results !== null && results.length === 0 && (
        <div className="text-center py-16 text-gray-500">
          <div className="text-4xl mb-3">🔮</div>
          <div className="text-lg font-medium">No active jobs to rank</div>
          <div className="text-sm mt-1">Capture some job listings via Scout first.</div>
        </div>
      )}

      {results && results.length > 0 && (
        <div className="space-y-3">
          {results.map((result, idx) => (
            <div
              key={result.job_id}
              className="bg-gray-900 border border-gray-800 rounded-lg p-4"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-center gap-3 min-w-0">
                  <span className="text-gray-500 text-sm font-mono w-6 shrink-0">
                    #{idx + 1}
                  </span>
                  <div className="min-w-0">
                    <a
                      href={`/jobs/${result.job_id}`}
                      className="text-violet-300 hover:text-violet-200 font-medium text-sm"
                    >
                      Job #{result.job_id}
                    </a>
                    {result.warning && (
                      <div className="text-amber-400 text-xs mt-1">
                        ⚠ {result.warning}
                      </div>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                      CONFIDENCE_STYLES[result.confidence] ?? CONFIDENCE_STYLES.low
                    }`}
                  >
                    {result.confidence}
                  </span>
                  <span className="text-violet-300 font-mono text-lg font-bold">
                    {Math.round(result.score * 100)}%
                  </span>
                </div>
              </div>
              {result.rationale && (
                <p className="text-gray-400 text-sm mt-2 ml-9">{result.rationale}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
