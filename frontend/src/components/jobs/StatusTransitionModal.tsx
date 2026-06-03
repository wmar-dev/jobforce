"use client";

import { useState } from "react";
import { patchJobStatus } from "@/lib/api";
import type { PipelineStatus } from "@/lib/types";

const VALID_TRANSITIONS: Record<PipelineStatus, PipelineStatus[]> = {
  saved: ["applied", "rejected", "withdrawn", "archived", "shortlisted"],
  shortlisted: ["applied", "rejected", "withdrawn", "archived", "saved"],
  archived: ["saved"],
  applied: ["interviewing", "rejected", "withdrawn"],
  interviewing: ["offer", "rejected", "withdrawn"],
  offer: [],
  rejected: [],
  withdrawn: [],
};

const DESTRUCTIVE: PipelineStatus[] = ["rejected", "withdrawn"];

interface StatusTransitionModalProps {
  jobId: number;
  currentStatus: PipelineStatus;
  onTransitioned?: (newStatus: PipelineStatus) => void;
  onClose: () => void;
}

export function StatusTransitionModal({
  jobId,
  currentStatus,
  onTransitioned,
  onClose,
}: StatusTransitionModalProps) {
  const [selected, setSelected] = useState<PipelineStatus | null>(null);
  const [isPending, setIsPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmDestructive, setConfirmDestructive] = useState(false);

  const validNext = VALID_TRANSITIONS[currentStatus] ?? [];

  const isTerminal = validNext.length === 0;

  const handleConfirm = async () => {
    if (!selected) return;
    if (DESTRUCTIVE.includes(selected) && !confirmDestructive) {
      setConfirmDestructive(true);
      return;
    }
    setIsPending(true);
    setError(null);
    try {
      await patchJobStatus(jobId, selected);
      onTransitioned?.(selected);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Transition failed");
    } finally {
      setIsPending(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 w-full max-w-sm shadow-2xl">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-white font-semibold">Change Status</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-300 text-lg">
            ✕
          </button>
        </div>

        <div className="text-xs text-gray-500 mb-3">
          Current:{" "}
          <span className="text-gray-300 font-medium">{currentStatus}</span>
        </div>

        {isTerminal ? (
          <p className="text-gray-400 text-sm py-4 text-center">
            This job is in a terminal state and cannot be moved.
          </p>
        ) : (
          <div className="space-y-2 mb-4">
            {validNext.map((status) => (
              <button
                key={status}
                onClick={() => {
                  setSelected(status);
                  setConfirmDestructive(false);
                }}
                className={`w-full text-left px-3 py-2 rounded text-sm transition-colors border ${
                  selected === status
                    ? "border-emerald-500 bg-emerald-950 text-emerald-300"
                    : "border-gray-700 hover:border-gray-600 text-gray-300"
                }`}
              >
                {status}
                {DESTRUCTIVE.includes(status) && (
                  <span className="ml-2 text-xs text-red-400">(destructive)</span>
                )}
              </button>
            ))}
          </div>
        )}

        {confirmDestructive && selected && (
          <p className="text-amber-400 text-xs mb-3">
            Moving to <strong>{selected}</strong> is irreversible. Confirm?
          </p>
        )}

        {error && <p className="text-red-400 text-xs mb-3">{error}</p>}

        {!isTerminal && (
          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="flex-1 px-3 py-2 text-sm text-gray-400 border border-gray-700 rounded hover:border-gray-600 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleConfirm}
              disabled={!selected || isPending}
              className="flex-1 px-3 py-2 text-sm bg-emerald-700 hover:bg-emerald-600 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded transition-colors"
            >
              {isPending ? "Moving..." : confirmDestructive ? "Confirm" : "Move"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
