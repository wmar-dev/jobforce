"use client";

import { useState, useEffect } from "react";
import { getJobs, getLatestCoachSession } from "@/lib/api";
import { QuestionCard } from "@/components/coach/QuestionCard";
import { MockInterviewPanel } from "@/components/coach/MockInterviewPanel";
import type { JobListing, InterviewSession, QuestionItem } from "@/lib/types";

const CATEGORIES: Array<{ key: QuestionItem["category"]; label: string; icon: string }> = [
  { key: "behavioral", label: "Behavioral", icon: "💬" },
  { key: "coding", label: "Coding", icon: "💻" },
  { key: "system_design", label: "System Design", icon: "🏗️" },
  { key: "role_specific", label: "Role-Specific", icon: "🎯" },
];

export default function CoachPage() {
  const [jobs, setJobs] = useState<JobListing[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null);
  const [session, setSession] = useState<InterviewSession | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeCategory, setActiveCategory] = useState<QuestionItem["category"] | "all">("all");
  const [isMockMode, setIsMockMode] = useState(false);

  useEffect(() => {
    Promise.all([
      getJobs({ status: "interviewing", limit: 50 }),
      getJobs({ status: "applied", limit: 50 }),
      getJobs({ status: "shortlisted", limit: 50 }),
    ]).then(([a, b, c]) => setJobs([...a.items, ...b.items, ...c.items]));
  }, []);

  const handleGeneratePrep = async () => {
    if (!selectedJobId) return;
    setIsLoading(true);
    setError(null);
    setSession(null);
    try {
      const result = await getLatestCoachSession(selectedJobId);
      setSession(result);
      setActiveCategory("all");
      setIsMockMode(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No prep session found — run /coach-prep <job_id> in Claude Code first");
    } finally {
      setIsLoading(false);
    }
  };

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
          onChange={(e) => setSelectedJobId(e.target.value ? Number(e.target.value) : null)}
          className="flex-1 max-w-xs px-3 py-2 text-sm bg-gray-800 border border-gray-700 rounded text-gray-200 focus:outline-none focus:border-blue-500"
        >
          <option value="">Select a job...</option>
          {jobs.map((job) => (
            <option key={job.id} value={job.id}>
              {job.title} @ {job.company.name}
            </option>
          ))}
        </select>
        <button
          onClick={handleGeneratePrep}
          disabled={isLoading || !selectedJobId}
          className="px-4 py-2 text-sm bg-blue-700 hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded transition-colors"
        >
          {isLoading ? "Loading..." : "🎯 Load Prep Pack"}
        </button>
      </div>

      {error && (
        <div className="text-red-400 text-sm py-3 px-4 bg-red-950 rounded mb-4">{error}</div>
      )}

      {session && (
        <>
          <div className="flex items-center justify-between mb-4">
            <div className="flex gap-1">
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
            <button
              onClick={() => setIsMockMode(!isMockMode)}
              className={`text-xs px-3 py-1.5 rounded border transition-colors ${
                isMockMode
                  ? "border-blue-600 bg-blue-950 text-blue-300"
                  : "border-gray-700 text-gray-500 hover:text-gray-300"
              }`}
            >
              {isMockMode ? "📋 Study Mode" : "🎭 Mock Interview"}
            </button>
          </div>

          {isMockMode ? (
            <MockInterviewPanel
              sessionId={session.session_id}
              questions={session.questions}
            />
          ) : (
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
          )}
        </>
      )}
    </div>
  );
}
