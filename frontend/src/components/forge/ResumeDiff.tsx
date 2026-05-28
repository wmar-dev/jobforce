"use client";

import type { ResumeDiffItem } from "@/lib/types";

interface ResumeDiffProps {
  diff: ResumeDiffItem[];
}

function tryParseJson(str: string): string {
  try {
    const parsed = JSON.parse(str);
    if (typeof parsed === "string") return parsed;
    return JSON.stringify(parsed, null, 2);
  } catch {
    return str;
  }
}

export function ResumeDiff({ diff }: ResumeDiffProps) {
  if (diff.length === 0) {
    return (
      <div className="text-gray-500 text-sm py-4 text-center">
        No changes were made to the resume.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {diff.map((item) => (
        <div key={item.field} className="border border-gray-800 rounded-lg overflow-hidden">
          <div className="bg-gray-800 px-3 py-2 text-xs font-mono text-gray-400 border-b border-gray-700">
            {item.field}
          </div>
          <div className="grid grid-cols-2 divide-x divide-gray-800">
            <div className="p-3">
              <div className="text-xs text-gray-600 uppercase tracking-wider mb-2">Original</div>
              <pre className="text-xs text-red-300 whitespace-pre-wrap break-all">
                {tryParseJson(item.original)}
              </pre>
            </div>
            <div className="p-3">
              <div className="text-xs text-gray-600 uppercase tracking-wider mb-2">Tailored</div>
              <pre className="text-xs text-emerald-300 whitespace-pre-wrap break-all">
                {tryParseJson(item.tailored)}
              </pre>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
