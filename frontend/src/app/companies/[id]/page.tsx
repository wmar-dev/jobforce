"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import useSWR from "swr";
import Link from "next/link";
import { getCompany, createMeetingNote, bulkArchive, patchCompany } from "@/lib/api";
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
  const [isBulkArchiving, setIsBulkArchiving] = useState(false);
  const [bulkArchiveMsg, setBulkArchiveMsg] = useState<string | null>(null);
  const [editingLink, setEditingLink] = useState(false);
  const [careersUrlInput, setCareersUrlInput] = useState("");
  const [isSavingLink, setIsSavingLink] = useState(false);

  const handleSaveLink = async () => {
    if (!company || !careersUrlInput.trim()) return;
    setIsSavingLink(true);
    try {
      await patchCompany(company.id, careersUrlInput.trim());
      setEditingLink(false);
      await mutate();
    } catch {
      console.error("Failed to save link", new Error("Backend error"));
    } finally {
      setIsSavingLink(false);
    }
  };

  const handleBulkArchive = async () => {
    setIsBulkArchiving(true);
    setBulkArchiveMsg(null);
    try {
      const result = await bulkArchive(companyId, { savedOnly: true });
      setBulkArchiveMsg(
        `Archived ${result.archived_count} saved job${result.archived_count !== 1 ? "s" : ""}.`
      );
      await mutate();
    } catch {
      setBulkArchiveMsg("Bulk archive failed. Is the backend running?");
    } finally {
      setIsBulkArchiving(false);
    }
  };

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
          <p className="text-sm ml-0">
            <a
              href={
                /^https?:\/\//.test(company.domain)
                  ? company.domain
                  : `https://${company.domain}`
              }
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-500 hover:text-emerald-400 transition-colors"
            >
              {company.domain}
            </a>
          </p>
        )}
        <div className="mt-3">
          {editingLink ? (
            <div className="flex gap-2">
              <input
                type="url"
                value={careersUrlInput}
                onChange={(e) => setCareersUrlInput(e.target.value)}
                placeholder="https://careers.example.com"
                className="flex-1 px-3 py-2 text-sm bg-gray-800 border border-gray-700 rounded text-gray-200 placeholder-gray-600 focus:outline-hidden focus:border-emerald-500"
              />
              <button
                onClick={handleSaveLink}
                disabled={isSavingLink || !careersUrlInput.trim()}
                className="px-3 py-2 text-sm bg-emerald-800 hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded transition-colors"
              >
                {isSavingLink ? "Saving..." : "Save"}
              </button>
              <button
                onClick={() => {
                  setEditingLink(false);
                  setCareersUrlInput("");
                }}
                className="px-3 py-2 text-sm bg-gray-800 border border-gray-700 rounded text-gray-400 hover:text-white hover:border-gray-600 transition-colors"
              >
                Cancel
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              {company.careers_url ? (
                <>
                  <a
                    href={company.careers_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-emerald-400 hover:text-emerald-300 text-sm break-all"
                  >
                    {company.careers_url}
                  </a>
                  <button
                    onClick={() => {
                      setCareersUrlInput(company.careers_url ?? "");
                      setEditingLink(true);
                    }}
                    className="text-xs text-gray-500 hover:text-gray-300 px-2 py-1 rounded border border-gray-700 hover:border-gray-600 transition-colors"
                  >
                    Edit
                  </button>
                </>
              ) : (
                <button
                  onClick={() => setEditingLink(true)}
                  className="text-xs text-gray-500 hover:text-gray-300 px-2 py-1 rounded border border-gray-700 hover:border-gray-600 transition-colors"
                >
                  Add Link
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Job Listings */}
        <div className="lg:col-span-2">
          <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
            <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
              Listings ({company.listings.length})
            </h2>
            <div className="flex items-center gap-2">
              <button
                onClick={handleBulkArchive}
                disabled={isBulkArchiving}
                className="px-3 py-1.5 text-xs bg-gray-800 border border-gray-700 rounded text-gray-400 hover:text-white hover:border-gray-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                title="Archive every saved job for this company, regardless of fit score"
              >
                {isBulkArchiving ? "Archiving..." : "Bulk Archive Saved"}
              </button>
              {bulkArchiveMsg && (
                <span className="text-xs text-gray-500">{bulkArchiveMsg}</span>
              )}
            </div>
          </div>
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
                    {job.fit_scored && job.fit_score != null ? (
                      <span className="text-violet-300 font-mono text-xs">
                        {Math.round(job.fit_score * 100)}%
                      </span>
                    ) : (
                      <span className="text-gray-600 text-xs">Not scored</span>
                    )}
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
              className="w-full px-3 py-2 text-sm bg-gray-800 border border-gray-700 rounded text-gray-200 placeholder-gray-600 focus:outline-hidden focus:border-emerald-500 resize-none"
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
