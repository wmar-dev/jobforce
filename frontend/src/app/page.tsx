"use client";

import Link from "next/link";
import { useDashboard } from "@/hooks/useDashboard";
import { PipelineSummary } from "@/components/dashboard/PipelineSummary";
import { ActivityFeed } from "@/components/dashboard/ActivityFeed";
import type { PipelineStatus } from "@/lib/types";

const HEROES = [
  {
    href: "/jobs",
    icon: "🔭",
    codename: "Scout",
    power: "Job Discovery",
    color: "text-emerald-400",
  },
  {
    href: "/oracle",
    icon: "🔮",
    codename: "Oracle",
    power: "Fit Ranking",
    color: "text-violet-400",
  },
  {
    href: "/forge",
    icon: "⚒️",
    codename: "Forge",
    power: "Resume Tailoring",
    color: "text-amber-400",
  },
  {
    href: "/coach",
    icon: "🎯",
    codename: "Coach",
    power: "Interview Prep",
    color: "text-blue-400",
  },
];

const EMPTY_COUNTS: Record<Exclude<PipelineStatus, "archived">, number> = {
  saved: 0,
  shortlisted: 0,
  applied: 0,
  interviewing: 0,
  offer: 0,
  rejected: 0,
  withdrawn: 0,
};

export default function HQPage() {
  const { data, isLoading, error } = useDashboard();

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-1">
          <span className="text-2xl">🏛️</span>
          <h1 className="text-2xl font-bold text-white">HQ</h1>
          <span className="text-gray-500">Command Center</span>
        </div>
        <p className="text-gray-400 text-sm ml-9">
          Your job search mission status and team overview.
        </p>
      </div>

      {/* Hero Quick-Access */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
        {HEROES.map((hero) => (
          <Link
            key={hero.href}
            href={hero.href}
            className="bg-gray-900 border border-gray-800 rounded-lg p-4 hover:border-gray-700 transition-colors group"
          >
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xl">{hero.icon}</span>
              <span className={`font-bold text-sm ${hero.color} group-hover:brightness-125`}>
                {hero.codename}
              </span>
            </div>
            <div className="text-xs text-gray-500">{hero.power}</div>
          </Link>
        ))}
      </div>

      {/* Pipeline Summary */}
      <section className="mb-8">
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
          Pipeline
        </h2>
        {isLoading && (
          <div className="text-gray-600 text-sm">Loading pipeline...</div>
        )}
        {error && (
          <div className="text-red-400 text-sm">
            Failed to load dashboard. Is the backend running?
          </div>
        )}
        {data && <PipelineSummary counts={data.counts} />}
        {!data && !isLoading && !error && (
          <PipelineSummary counts={EMPTY_COUNTS} />
        )}
      </section>

      {/* Activity Feed */}
      <section>
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
          Recent Activity
        </h2>
        {data ? (
          <ActivityFeed
            transitions={data.recent_transitions}
            notes={data.recent_notes}
          />
        ) : (
          !isLoading && <div className="text-gray-600 text-sm py-4">No activity yet.</div>
        )}
      </section>
    </div>
  );
}
