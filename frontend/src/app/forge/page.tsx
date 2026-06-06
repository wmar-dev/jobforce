"use client";

import { useState, useEffect } from "react";
import { getJobs, getBaseResume, putBaseResume, getTailoredResume } from "@/lib/api";
import { ResumeDiff } from "@/components/forge/ResumeDiff";
import { ExportButton } from "@/components/forge/ExportButton";
import type { JobListing, Resume, TailoredResumeResponse } from "@/lib/types";

export default function ForgePage() {
  const [jobs, setJobs] = useState<JobListing[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null);
  const [baseResume, setBaseResume] = useState<Resume | null>(null);
  const [tailored, setTailored] = useState<TailoredResumeResponse | null>(null);
  const [isLoadingTailored, setIsLoadingTailored] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isEditingBase, setIsEditingBase] = useState(false);
  const [rawJson, setRawJson] = useState("");

  useEffect(() => {
    Promise.all([
      getJobs({ status: "shortlisted", limit: 50, sort_by: "fit_score", sort_dir: "desc" }),
      getJobs({ status: "saved", limit: 50, sort_by: "fit_score", sort_dir: "desc" }),
    ]).then(([shortlisted, saved]) => setJobs([...shortlisted.items, ...saved.items]));
    getBaseResume()
      .then((r) => {
        setBaseResume(r);
        setRawJson(JSON.stringify(r.structured_data, null, 2));
      })
      .catch(() => {
        setRawJson(JSON.stringify(EMPTY_RESUME, null, 2));
      });
  }, []);

  const handleSaveBase = async () => {
    try {
      const parsed = JSON.parse(rawJson);
      const saved = await putBaseResume(parsed);
      setBaseResume(saved);
      setIsEditingBase(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Invalid JSON or save failed");
    }
  };

  const handleJobSelect = async (jobId: number | null) => {
    setSelectedJobId(jobId);
    setTailored(null);
    setError(null);
    if (!jobId) return;
    setIsLoadingTailored(true);
    try {
      const result = await getTailoredResume(jobId);
      setTailored(result);
    } finally {
      setIsLoadingTailored(false);
    }
  };

  return (
    <div>
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-1">
          <span className="text-2xl">⚒️</span>
          <h1 className="text-2xl font-bold text-white">Forge</h1>
          <span className="text-gray-500">Resume Tailoring</span>
        </div>
        <p className="text-gray-400 text-sm ml-9">
          Tailor your resume to a specific job listing using AI.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Base Resume Editor */}
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-gray-300">Base Resume</h2>
            <button
              onClick={() => setIsEditingBase(!isEditingBase)}
              className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
            >
              {isEditingBase ? "Cancel" : "Edit"}
            </button>
          </div>

          {isEditingBase ? (
            <>
              <textarea
                value={rawJson}
                onChange={(e) => setRawJson(e.target.value)}
                rows={16}
                className="w-full px-3 py-2 text-xs font-mono bg-gray-800 border border-gray-700 rounded text-gray-200 focus:outline-none focus:border-amber-500 resize-none"
              />
              <button
                onClick={handleSaveBase}
                className="mt-2 px-3 py-2 text-sm bg-amber-700 hover:bg-amber-600 text-white rounded transition-colors"
              >
                Save Base Resume
              </button>
            </>
          ) : (
            <div className="text-sm text-gray-400">
              {baseResume ? (
                <>
                  <div>
                    <span className="text-gray-500">Name:</span>{" "}
                    <span className="text-gray-200">
                      {baseResume.structured_data?.personal_info?.name ?? "—"}
                    </span>
                  </div>
                  <div className="mt-1">
                    <span className="text-gray-500">Skills:</span>{" "}
                    <span className="text-gray-300">
                      {Array.isArray(baseResume.structured_data?.skills)
                        ? baseResume.structured_data.skills.join(", ")
                        : "—"}
                    </span>
                  </div>
                  <div className="mt-1">
                    <span className="text-gray-500">Experience entries:</span>{" "}
                    <span className="text-gray-300">
                      {baseResume.structured_data?.work_history?.length ?? 0}
                    </span>
                  </div>
                </>
              ) : (
                <span className="text-gray-600">
                  No base resume. Click Edit to add yours.
                </span>
              )}
            </div>
          )}
        </div>

        {/* Target Job Selector */}
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <h2 className="text-sm font-semibold text-gray-300 mb-3">Target Job</h2>
          {jobs.length === 0 ? (
            <p className="text-gray-600 text-sm">
              No saved jobs yet. Use Scout to capture job listings.
            </p>
          ) : (
            <select
              value={selectedJobId ?? ""}
              onChange={(e) => handleJobSelect(e.target.value ? Number(e.target.value) : null)}
              className="w-full px-3 py-2 text-sm bg-gray-800 border border-gray-700 rounded text-gray-200 focus:outline-none focus:border-amber-500"
            >
              <option value="">Select a job...</option>
              {(() => {
                const shortlisted = jobs.filter((j) => j.status === "shortlisted");
                const saved = jobs.filter((j) => j.status === "saved");
                return (
                  <>
                    {shortlisted.length > 0 && (
                      <optgroup label="⭐ Shortlisted">
                        {shortlisted.map((job) => (
                          <option key={job.id} value={job.id}>
                            {job.fit_score != null ? `[${job.fit_score}] ` : ""}{job.title} @ {job.company.name}
                          </option>
                        ))}
                      </optgroup>
                    )}
                    {saved.length > 0 && (
                      <optgroup label="Saved">
                        {saved.map((job) => (
                          <option key={job.id} value={job.id}>
                            {job.fit_score != null ? `[${job.fit_score}] ` : ""}{job.title} @ {job.company.name}
                          </option>
                        ))}
                      </optgroup>
                    )}
                  </>
                );
              })()}
            </select>
          )}

          {selectedJobId && (
            <div className="mt-4 px-3 py-2 bg-gray-800 border border-gray-700 rounded text-xs text-gray-400">
              {isLoadingTailored ? (
                <span>Loading tailored resume...</span>
              ) : tailored ? (
                <span className="text-green-400">✓ Tailored resume loaded</span>
              ) : (
                <>
                  <span className="text-amber-400">No tailored resume yet.</span>
                  {" "}Run in Claude Code:{" "}
                  <code className="text-gray-200 font-mono">/forge-tailor {selectedJobId}</code>
                </>
              )}
            </div>
          )}
        </div>
      </div>

      {error && (
        <div className="text-red-400 text-sm py-3 px-4 bg-red-950 rounded mb-4">{error}</div>
      )}

      {tailored && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-gray-300">
              Changes ({tailored.diff.length} field{tailored.diff.length !== 1 ? "s" : ""} modified)
            </h2>
            <ExportButton resumeId={tailored.id} />
          </div>
          <ResumeDiff diff={tailored.diff} />
        </div>
      )}
    </div>
  );
}

const EMPTY_RESUME = {
  personal_info: { name: "", email: "" },
  work_history: [],
  education: [],
  skills: [],
};
