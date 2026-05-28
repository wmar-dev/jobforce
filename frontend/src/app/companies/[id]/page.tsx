"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import useSWR from "swr";
import Link from "next/link";
import { getCompany, createMeetingNote } from "@/lib/api";
import { StatusBadge } from "@/components/jobs/StatusBadge";
import { StatusTransitionModal } from "@/components/jobs/StatusTransitionModal";
import type { CompanyDetail, PipelineStatus } from "@/lib/types";

export default function CompanyDetailPage() {
  const params = useParams();
  const companyId = Number(params.id);

  const { data: company, isLoading, error, mutate } = useSWR<CompanyDetail>(
    `/api/companies/${companyId}`,
    () => getCompany(companyId)
  );

  const [noteContent, setNoteContent] = useState("");
  const [isSubmittingNote, setIsSubmittingNote] = useState(false);
  const [transitionJobId, setTransitionJobId] = useState<number | null>(null);
  const [transitionCurrentStatus, setTransitionCurrentStatus] =
    useState<PipelineStatus | null>(null);

  const handleAddNote = async () => {
    if (!noteContent.trim()) return;
    setIsSubmittingNote(true);
    try {
      await createMeetingNote(companyId, noteContent.trim());
      setNoteContent("");
      await mutate();
    } catch (err) {
      console.error("Failed to add note", err);
    } finally {
      setIsSubmittingNote(false);
    }
  };

  if (isLoading) {
    return <div className="text-gray-500 text-sm py-8">Loading company...</div>;
  }
  if (error) {
    return (
      <div className="text-red-400 text-sm py-4">
        Failed to load company. Is the backend running?
      </div>
    );
  }
  if (!company) return null;

  return (
    <div>
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-1">
          <Link href="/" className="text-gray-600 hover:text-gray-400 text-sm">
            HQ
          </Link>
          <span className="text-gray-700">/</span>
          <h1 className="text-2xl font-bold text-white">{company.name}</h1>
        </div>
        {company.domain && (
          <p className="text-gray-500 text-sm ml-0">{company.domain}</p>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Job Listings */}
        <div className="lg:col-span-2">
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
            Listings ({company.listings.length})
          </h2>
          {company.listings.length === 0 ? (
            <div className="text-gray-600 text-sm">No listings for this company.</div>
          ) : (
            <div className="space-y-2">
              {company.listings.map((job) => (
                <div
                  key={job.id}
                  className="flex items-center justify-between bg-gray-900 border border-gray-800 rounded-lg px-4 py-3"
                >
                  <div>
                    <Link
                      href={`/jobs/${job.id}`}
                      className="text-emerald-400 hover:text-emerald-300 text-sm font-medium"
                    >
                      {job.title}
                    </Link>
                    {job.location && (
                      <div className="text-xs text-gray-500">{job.location}</div>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <StatusBadge status={job.status as PipelineStatus} />
                    <button
                      onClick={() => {
                        setTransitionJobId(job.id);
                        setTransitionCurrentStatus(job.status as PipelineStatus);
                      }}
                      className="text-xs text-gray-500 hover:text-gray-300 px-2 py-1 rounded border border-gray-700 hover:border-gray-600 transition-colors"
                    >
                      Move
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Meeting Notes */}
        <div>
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
            Notes
          </h2>
          <div className="mb-4">
            <textarea
              value={noteContent}
              onChange={(e) => setNoteContent(e.target.value)}
              placeholder="Add a meeting note..."
              rows={3}
              className="w-full px-3 py-2 text-sm bg-gray-800 border border-gray-700 rounded text-gray-200 placeholder-gray-600 focus:outline-none focus:border-emerald-500 resize-none"
            />
            <button
              onClick={handleAddNote}
              disabled={isSubmittingNote || !noteContent.trim()}
              className="mt-2 w-full px-3 py-2 text-sm bg-emerald-800 hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded transition-colors"
            >
              {isSubmittingNote ? "Saving..." : "Add Note"}
            </button>
          </div>

          {company.notes.length === 0 ? (
            <div className="text-gray-600 text-sm">No notes yet.</div>
          ) : (
            <div className="space-y-3">
              {company.notes.map((note) => (
                <div
                  key={note.id}
                  className="bg-gray-900 border border-gray-800 rounded-lg p-3"
                >
                  <p className="text-gray-300 text-sm">{note.content}</p>
                  <div className="text-xs text-gray-600 mt-2">
                    {new Date(note.created_at).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {transitionJobId !== null && transitionCurrentStatus !== null && (
        <StatusTransitionModal
          jobId={transitionJobId}
          currentStatus={transitionCurrentStatus}
          onTransitioned={() => mutate()}
          onClose={() => {
            setTransitionJobId(null);
            setTransitionCurrentStatus(null);
          }}
        />
      )}
    </div>
  );
}
