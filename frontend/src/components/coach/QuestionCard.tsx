"use client";

import { useState } from "react";
import type { QuestionItem } from "@/lib/types";

const CATEGORY_CONFIG: Record<
  QuestionItem["category"],
  { label: string; icon: string; color: string }
> = {
  behavioral: { label: "Behavioral", icon: "💬", color: "text-blue-300" },
  coding: { label: "Coding", icon: "💻", color: "text-emerald-300" },
  system_design: { label: "System Design", icon: "🏗️", color: "text-violet-300" },
  role_specific: { label: "Role-Specific", icon: "🎯", color: "text-amber-300" },
};

interface QuestionCardProps {
  question: QuestionItem;
}

export function QuestionCard({ question }: QuestionCardProps) {
  const [showGuidance, setShowGuidance] = useState(false);
  const cfg = CATEGORY_CONFIG[question.category] ?? {
    label: question.category,
    icon: "❓",
    color: "text-gray-300",
  };

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
      <div className="flex items-start gap-3">
        <span className="text-lg shrink-0 mt-0.5">{cfg.icon}</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <span className={`text-xs font-medium ${cfg.color}`}>{cfg.label}</span>
            {question.leetcode_url && (
              <a
                href={question.leetcode_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs bg-yellow-900 text-yellow-300 px-1.5 py-0.5 rounded hover:bg-yellow-800 transition-colors"
              >
                LeetCode →
              </a>
            )}
            {question.source_url && (
              <a
                href={question.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-gray-500 hover:text-gray-300 transition-colors truncate max-w-[160px]"
              >
                source ↗
              </a>
            )}
          </div>
          <p className="text-gray-200 text-sm">{question.text}</p>
          {question.guidance && (
            <div className="mt-2">
              <button
                onClick={() => setShowGuidance(!showGuidance)}
                className="text-xs text-gray-500 hover:text-gray-400 transition-colors"
              >
                {showGuidance ? "▲ Hide guidance" : "▼ Show guidance"}
              </button>
              {showGuidance && (
                <p className="text-xs text-gray-400 mt-1 italic">{question.guidance}</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
