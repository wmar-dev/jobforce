"use client";

import type { DashboardSummary } from "@/lib/types";

interface ActivityFeedProps {
  transitions: DashboardSummary["recent_transitions"];
  notes: DashboardSummary["recent_notes"];
}

const STATUS_COLORS: Record<string, string> = {
  saved: "text-gray-300",
  applied: "text-blue-300",
  interviewing: "text-yellow-300",
  offer: "text-green-300",
  rejected: "text-red-300",
  withdrawn: "text-purple-300",
};

function formatRelative(dateStr: string): string {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diff = now - then;
  const minutes = Math.floor(diff / 60_000);
  const hours = Math.floor(diff / 3_600_000);
  const days = Math.floor(diff / 86_400_000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  return `${days}d ago`;
}

type FeedItem =
  | { kind: "transition"; at: string; item: DashboardSummary["recent_transitions"][0] }
  | { kind: "note"; at: string; item: DashboardSummary["recent_notes"][0] };

export function ActivityFeed({ transitions, notes }: ActivityFeedProps) {
  const items: FeedItem[] = [
    ...transitions.map((t) => ({ kind: "transition" as const, at: t.transitioned_at, item: t })),
    ...notes.map((n) => ({ kind: "note" as const, at: n.created_at, item: n })),
  ].sort((a, b) => new Date(b.at).getTime() - new Date(a.at).getTime());

  if (items.length === 0) {
    return (
      <div className="text-gray-600 text-sm py-6 text-center">No recent activity</div>
    );
  }

  return (
    <div className="space-y-2">
      {items.map((entry, idx) => (
        <div key={idx} className="flex items-start gap-3 py-2 border-b border-gray-800/50 last:border-0">
          <span className="text-lg shrink-0 mt-0.5">
            {entry.kind === "transition" ? "🔄" : "📝"}
          </span>
          <div className="min-w-0 flex-1">
            {entry.kind === "transition" ? (
              <span className="text-sm text-gray-300">
                <a
                  href={`/jobs/${entry.item.job_id}`}
                  className="text-emerald-400 hover:text-emerald-300"
                >
                  {entry.item.job_title || `Job #${entry.item.job_id}`}
                </a>{" "}
                →{" "}
                <span className={STATUS_COLORS[entry.item.to_status] ?? "text-gray-300"}>
                  {entry.item.to_status}
                </span>
              </span>
            ) : (
              <span className="text-sm text-gray-400 truncate block">
                Note on{" "}
                <a
                  href={`/companies/${entry.item.company_id}`}
                  className="text-emerald-400 hover:text-emerald-300"
                >
                  company #{entry.item.company_id}
                </a>
                : {entry.item.content}
              </span>
            )}
          </div>
          <span className="text-xs text-gray-600 shrink-0">{formatRelative(entry.at)}</span>
        </div>
      ))}
    </div>
  );
}
