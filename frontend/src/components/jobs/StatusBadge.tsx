import type { PipelineStatus } from "@/lib/types";

const STATUS_CONFIG: Record<PipelineStatus, { label: string; classes: string }> = {
  saved: { label: "Saved", classes: "bg-gray-700 text-gray-200" },
  archived: { label: "Archived", classes: "bg-gray-800 text-gray-500" },
  shortlisted: { label: "Shortlisted", classes: "bg-amber-900 text-amber-200" },
  applied: { label: "Applied", classes: "bg-blue-900 text-blue-200" },
  interviewing: { label: "Interviewing", classes: "bg-yellow-900 text-yellow-200" },
  offer: { label: "Offer", classes: "bg-green-900 text-green-200" },
  rejected: { label: "Rejected", classes: "bg-red-900 text-red-300" },
  withdrawn: { label: "Withdrawn", classes: "bg-purple-900 text-purple-300" },
};

export function StatusBadge({ status }: { status: PipelineStatus }) {
  const cfg = STATUS_CONFIG[status] ?? { label: status, classes: "bg-gray-700 text-gray-200" };
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${cfg.classes}`}
    >
      {cfg.label}
    </span>
  );
}
