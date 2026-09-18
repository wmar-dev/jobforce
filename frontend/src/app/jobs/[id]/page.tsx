"use client";

import { use, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import { useJob } from "@/hooks/useJob";
import { useJobNote } from "@/hooks/useJobNote";
import { upsertJobNote, deleteJobNote } from "@/lib/api";
import { StatusBadge } from "@/components/jobs/StatusBadge";
import { StatusTransitionModal } from "@/components/jobs/StatusTransitionModal";
import type { PipelineStatus } from "@/lib/types";

function JobDescription({ text }: { text: string }) {
  const isMarkdown = /[#*\-`\[\]]/.test(text);
  if (isMarkdown) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-5">
        <ReactMarkdown
          components={{
            h1: ({ children }) => <h3 className="text-base font-semibold text-emerald-400 mt-4 mb-2 first:mt-0">{children}</h3>,
            h2: ({ children }) => <h3 className="text-sm font-semibold text-emerald-400 mt-4 mb-2 first:mt-0">{children}</h3>,
            h3: ({ children }) => <h4 className="text-sm font-semibold text-gray-300 mt-3 mb-1">{children}</h4>,
            p: ({ children }) => <p className="text-sm text-gray-300 leading-relaxed mb-3">{children}</p>,
            ul: ({ children }) => <ul className="list-disc list-outside ml-4 mb-3 space-y-1">{children}</ul>,
            ol: ({ children }) => <ol className="list-decimal list-outside ml-4 mb-3 space-y-1">{children}</ol>,
            li: ({ children }) => <li className="text-sm text-gray-300 leading-relaxed">{children}</li>,
            strong: ({ children }) => <strong className="text-gray-100 font-semibold">{children}</strong>,
          }}
        >
          {text}
        </ReactMarkdown>
      </div>
    );
  }
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-5">
      <p className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">{text}</p>
    </div>
  );
}

const FIT_CONFIDENCE_CLASSES: Record<string, string> = {
  high: "text-emerald-400",
  medium: "text-yellow-400",
  low: "text-red-400",
};

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export default function JobDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const jobId = parseInt(id, 10);
  const router = useRouter();
  const { data: job, mutate, error, isLoading } = useJob(jobId);
  const { data: note, mutate: mutateNote } = useJobNote(jobId);
  const [showModal, setShowModal] = useState(false);
  const [noteBody, setNoteBody] = useState("");
  const [noteSaving, setNoteSaving] = useState(false);
  const [prevNote, setPrevNote] = useState(note);

  if (note !== prevNote) {
    setPrevNote(note);
    setNoteBody(note?.body ?? "");
  }

  async function handleSaveNote() {
    if (noteSaving) return;
    setNoteSaving(true);
    try {
      await upsertJobNote(jobId, noteBody);
      await mutateNote();
    } finally {
      setNoteSaving(false);
    }
  }

  async function handleClearNote() {
    if (noteSaving) return;
    setNoteSaving(true);
    try {
      await deleteJobNote(jobId);
      setNoteBody("");
      await mutateNote();
    } finally {
      setNoteSaving(false);
    }
  }

  if (isLoading) {
    return (
      <div className="text-gray-500 text-sm py-16 text-center">
        Loading job...
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="py-16 text-center">
        <p className="text-red-400 text-sm mb-4">
          Failed to load job. Is the backend running?
        </p>
        <Link href="/jobs" className="text-emerald-400 text-sm hover:underline">
          ← Back to jobs
        </Link>
      </div>
    );
  }

  const handleTransitioned = (newStatus: PipelineStatus) => {
    mutate({ ...job, status: newStatus });
  };

  return (
    <div className="max-w-3xl mx-auto">
      {/* Back nav */}
      <div className="mb-6">
        <button
          onClick={() => router.back()}
          className="text-gray-500 hover:text-gray-300 text-sm transition-colors"
        >
          ← Back
        </button>
      </div>

      {/* Header */}
      <div className="mb-6">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-2xl font-bold text-white mb-1">{job.title}</h1>
            <Link
              href={`/companies/${job.company.id}`}
              className="text-gray-400 hover:text-emerald-400 text-base transition-colors"
            >
              {job.company.name}
            </Link>
          </div>
          <div className="flex items-center gap-3 flex-shrink-0">
            <StatusBadge status={job.status} />
            <button
              onClick={() => setShowModal(true)}
              className="px-3 py-1.5 text-xs bg-gray-800 hover:bg-gray-700 border border-gray-700 hover:border-gray-600 text-gray-300 rounded transition-colors"
            >
              Move status
            </button>
          </div>
        </div>
      </div>

      {/* Meta row */}
      <div className="flex flex-wrap gap-x-6 gap-y-2 mb-6 text-sm text-gray-400">
        {job.location && (
          <span>
            <span className="text-gray-600 mr-1">📍</span>
            {job.location}
          </span>
        )}
        {job.role_type && (
          <span>
            <span className="text-gray-600 mr-1">💼</span>
            {job.role_type}
          </span>
        )}
        <span>
          <span className="text-gray-600 mr-1">📅</span>
          Added {formatDate(job.created_at)}
        </span>
        <a
          href={job.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-emerald-400 hover:text-emerald-300 transition-colors"
        >
          View original ↗
        </a>
        <Link
          href={`/forge?jobId=${job.id}`}
          className="text-amber-400 hover:text-amber-300 transition-colors"
        >
          ⚒️ Tailor in Forge
        </Link>
        <Link
          href={`/coach?job=${job.id}`}
          className="text-blue-400 hover:text-blue-300 transition-colors"
        >
          🎯 Interview Prep
        </Link>
      </div>

      {/* Fit score */}
      {job.fit_scored && job.fit_score != null && (
        <div className="mb-6 p-4 bg-gray-900 border border-gray-800 rounded-lg">
          <div className="flex items-center gap-3 mb-2">
            <span className="text-sm font-medium text-gray-300">Fit Score</span>
            <span
              className={`text-lg font-bold ${
                FIT_CONFIDENCE_CLASSES[job.fit_confidence ?? ""] ?? "text-gray-300"
              }`}
            >
              {Math.round(job.fit_score * 100)}
              <span className="text-xs font-normal text-gray-500 ml-1">/ 100</span>
            </span>
            {job.fit_confidence && (
              <span className="text-xs text-gray-500 capitalize">
                ({job.fit_confidence})
              </span>
            )}
          </div>
          {job.fit_rationale && (
            <p className="text-sm text-gray-400">{job.fit_rationale}</p>
          )}
        </div>
      )}

      {/* Description */}
      {job.description && (
        <div className="mb-6">
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">
            Description
          </h2>
          <JobDescription text={job.description} />
        </div>
      )}

      {/* Status history */}
      {job.status_history.length > 0 && (
        <div className="mb-6">
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">
            Status History
          </h2>
          <ol className="relative border-l border-gray-800 ml-2">
            {job.status_history.map((transition) => (
              <li key={transition.id} className="mb-4 ml-4">
                <div className="absolute w-2 h-2 bg-emerald-600 rounded-full -left-1 mt-1" />
                <div className="flex items-center gap-2 flex-wrap">
                  {transition.from_status && (
                    <>
                      <StatusBadge status={transition.from_status} />
                      <span className="text-gray-600 text-xs">→</span>
                    </>
                  )}
                  <StatusBadge status={transition.to_status} />
                  <span className="text-xs text-gray-500 ml-auto">
                    {formatDate(transition.transitioned_at)}
                  </span>
                </div>
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* Notes */}
      <div className="mb-6">
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">
          Notes
        </h2>
        <textarea
          value={noteBody}
          onChange={(e) => setNoteBody(e.target.value)}
          placeholder="Add notes from recruiter meetings or company research..."
          className="w-full h-36 bg-gray-900 border border-gray-800 rounded-lg p-3 text-sm text-gray-300 placeholder-gray-600 resize-y focus:outline-none focus:border-gray-600 transition-colors"
        />
        <div className="flex items-center justify-between mt-2">
          <div className="text-xs text-gray-600">
            {note?.updated_at && (
              <span>Last edited {new Date(note.updated_at).toLocaleString()}</span>
            )}
          </div>
          <div className="flex gap-2">
            {note && (
              <button
                onClick={handleClearNote}
                disabled={noteSaving}
                className="px-3 py-1.5 text-xs bg-gray-800 hover:bg-gray-700 border border-gray-700 text-gray-400 rounded transition-colors disabled:opacity-50"
              >
                Clear
              </button>
            )}
            <button
              onClick={handleSaveNote}
              disabled={noteSaving || noteBody === (note?.body ?? "")}
              className="px-3 py-1.5 text-xs bg-emerald-700 hover:bg-emerald-600 text-white rounded transition-colors disabled:opacity-50"
            >
              {noteSaving ? "Saving…" : "Save"}
            </button>
          </div>
        </div>
      </div>

      {/* Status transition modal */}
      {showModal && (
        <StatusTransitionModal
          jobId={job.id}
          currentStatus={job.status}
          onTransitioned={handleTransitioned}
          onClose={() => setShowModal(false)}
        />
      )}
    </div>
  );
}
