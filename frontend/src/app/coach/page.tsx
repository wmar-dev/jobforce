"use client";

import { Suspense, useState, useEffect, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import { getJobs, getLatestCoachSession } from "@/lib/api";
import { QuestionCard } from "@/components/coach/QuestionCard";
import type { JobListing, InterviewSession, QuestionItem } from "@/lib/types";

const CATEGORIES: Array<{ key: QuestionItem["category"]; label: string; icon: string }> = [
  { key: "behavioral", label: "Behavioral", icon: "💬" },
  { key: "coding", label: "Coding", icon: "💻" },
  { key: "system_design", label: "System Design", icon: "🏗️" },
  { key: "role_specific", label: "Role-Specific", icon: "🎯" },
];

function CoachPageInner() {
  const searchParams = useSearchParams();
  const [jobs, setJobs] = useState<JobListing[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<number | null>(() => {
    const jobParam = searchParams.get("job");
    return jobParam ? Number(jobParam) : null;
  });
  const [session, setSession] = useState<InterviewSession | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeCategory, setActiveCategory] = useState<QuestionItem["category"] | "all">("all");

  useEffect(() => {
    Promise.all([
      getJobs({ status: "interviewing", limit: 50 }),
      getJobs({ status: "applied", limit: 50 }),
      getJobs({ status: "shortlisted", limit: 50 }),
    ]).then(([a, b, c]) => setJobs([...a.items, ...b.items, ...c.items]));
  }, []);

  const handleLoadSession = useCallback(async (jobId?: number) => {
    const id = jobId ?? selectedJobId;
    if (!id) return;
    setIsLoading(true);
    setError(null);
    setSession(null);
    try {
      const result = await getLatestCoachSession(id);
      setSession(result);
      setActiveCategory("all");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "";
      setError(
        msg.toLowerCase().includes("no prep session")
          ? `No prep session found — run /coach-prep ${id} in Claude Code first, then reload.`
          : msg || "Failed to load session"
      );
    } finally {
      setIsLoading(false);
    }
  }, [selectedJobId]);

  useEffect(() => {
    if (selectedJobId != null) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- initial load on mount, not a state sync
      handleLoadSession(selectedJobId);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const filteredQuestions = session?.questions.filter(
    (q) => activeCategory === "all" || q.category === activeCategory
  ) ?? [];

  return (
    <div>
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-1">
          <span className="text-2xl">🎯</span>
          <h1 className="text-2xl font-bold text-white">Coach</h1>
          <span className="text-gray-500">Interview Prep</span>
        </div>
        <p className="text-gray-400 text-sm ml-9">
          Interview prep powered by Claude Code. Run /coach-prep &lt;job_id&gt; to generate a session, then load it here.
        </p>
      </div>

      {/* Job Selector */}
      <div className="flex items-center gap-3 mb-6">
        <select
          value={selectedJobId ?? ""}
          onChange={(e) => {
            const id = e.target.value ? Number(e.target.value) : null;
            setSelectedJobId(id);
            if (id) handleLoadSession(id);
          }}
          className="flex-1 max-w-xs px-3 py-2 text-sm bg-gray-800 border border-gray-700 rounded text-gray-200 focus:outline-hidden focus:border-blue-500"
        >
          <option value="">Select a job...</option>
          {jobs.map((job) => (
            <option key={job.id} value={job.id}>
              {job.title} @ {job.company.name}
            </option>
          ))}
        </select>
        {isLoading && (
          <span className="text-sm text-gray-500">Loading...</span>
        )}
        {selectedJobId && (
          <a
            href={`/jobs/${selectedJobId}`}
            className="text-sm text-blue-400 hover:text-blue-300 transition-colors"
          >
            View job →
          </a>
        )}
      </div>

      {error && (
        <div className="text-red-400 text-sm py-3 px-4 bg-red-950 rounded mb-4">{error}</div>
      )}

      {session && (
        <>
          <div className="flex gap-1 mb-4">
            <button
              onClick={() => setActiveCategory("all")}
              className={`px-3 py-1.5 text-xs rounded transition-colors ${
                activeCategory === "all"
                  ? "bg-gray-700 text-white"
                  : "text-gray-500 hover:text-gray-300"
              }`}
            >
              All ({session.questions.length})
            </button>
            {CATEGORIES.map((cat) => {
              const count = session.questions.filter((q) => q.category === cat.key).length;
              if (count === 0) return null;
              return (
                <button
                  key={cat.key}
                  onClick={() => setActiveCategory(cat.key)}
                  className={`px-3 py-1.5 text-xs rounded transition-colors ${
                    activeCategory === cat.key
                      ? "bg-gray-700 text-white"
                      : "text-gray-500 hover:text-gray-300"
                  }`}
                >
                  {cat.icon} {cat.label} ({count})
                </button>
              );
            })}
          </div>

          <div className="space-y-3">
            {filteredQuestions.map((q) => (
              <QuestionCard key={q.id} question={q} />
            ))}
            {filteredQuestions.length === 0 && (
              <div className="text-gray-600 text-sm py-4 text-center">
                No questions in this category.
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

export default function CoachPage() {
  return (
    <Suspense>
      <CoachPageInner />
    </Suspense>
  );
}
