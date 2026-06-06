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

type DiffLine =
  | { type: "context"; text: string; lineA: number; lineB: number }
  | { type: "removed"; text: string; lineA: number }
  | { type: "added"; text: string; lineB: number };

function computeLineDiff(a: string, b: string): DiffLine[] {
  const linesA = a.split("\n");
  const linesB = b.split("\n");

  // Myers diff via LCS dp
  const m = linesA.length;
  const n = linesB.length;

  // dp[i][j] = LCS length of linesA[0..i-1] and linesB[0..j-1]
  const dp: number[][] = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0));
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      dp[i][j] =
        linesA[i - 1] === linesB[j - 1]
          ? dp[i - 1][j - 1] + 1
          : Math.max(dp[i - 1][j], dp[i][j - 1]);
    }
  }

  // Backtrack
  const raw: Array<{ kind: "context" | "removed" | "added"; text: string }> = [];
  let i = m, j = n;
  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && linesA[i - 1] === linesB[j - 1]) {
      raw.unshift({ kind: "context", text: linesA[i - 1] });
      i--; j--;
    } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
      raw.unshift({ kind: "added", text: linesB[j - 1] });
      j--;
    } else {
      raw.unshift({ kind: "removed", text: linesA[i - 1] });
      i--;
    }
  }

  // Assign line numbers
  const lines: DiffLine[] = [];
  let lineA = 1, lineB = 1;
  for (const entry of raw) {
    if (entry.kind === "context") {
      lines.push({ type: "context", text: entry.text, lineA, lineB });
      lineA++; lineB++;
    } else if (entry.kind === "removed") {
      lines.push({ type: "removed", text: entry.text, lineA });
      lineA++;
    } else {
      lines.push({ type: "added", text: entry.text, lineB });
      lineB++;
    }
  }
  return lines;
}

// Keep at most CONTEXT lines of context around changed lines
const CONTEXT = 3;

function sliceHunks(lines: DiffLine[]): DiffLine[][] {
  const changed = new Set<number>();
  lines.forEach((l, idx) => {
    if (l.type !== "context") changed.add(idx);
  });

  if (changed.size === 0) return [];

  // Build keep-set: changed ± CONTEXT
  const keep = new Set<number>();
  for (const idx of changed) {
    for (let d = -CONTEXT; d <= CONTEXT; d++) {
      const n = idx + d;
      if (n >= 0 && n < lines.length) keep.add(n);
    }
  }

  // Group contiguous keep indices into hunks
  const hunks: DiffLine[][] = [];
  let hunk: DiffLine[] = [];
  let prev = -2;
  const sorted = [...keep].sort((a, b) => a - b);
  for (const idx of sorted) {
    if (idx !== prev + 1 && hunk.length > 0) {
      hunks.push(hunk);
      hunk = [];
    }
    hunk.push(lines[idx]);
    prev = idx;
  }
  if (hunk.length > 0) hunks.push(hunk);
  return hunks;
}

function HunkHeader({ hunk }: { hunk: DiffLine[] }) {
  const firstA = hunk.find((l) => l.type !== "added");
  const firstB = hunk.find((l) => l.type !== "removed");
  const lastA = [...hunk].reverse().find((l) => l.type !== "added");
  const lastB = [...hunk].reverse().find((l) => l.type !== "removed");

  const startA = firstA && "lineA" in firstA ? firstA.lineA : "?";
  const startB = firstB && "lineB" in firstB ? firstB.lineB : "?";
  const countA =
    lastA && "lineA" in lastA && firstA && "lineA" in firstA
      ? (lastA.lineA as number) - (firstA.lineA as number) + 1
      : 0;
  const countB =
    lastB && "lineB" in lastB && firstB && "lineB" in firstB
      ? (lastB.lineB as number) - (firstB.lineB as number) + 1
      : 0;

  return (
    <div className="bg-blue-950/40 border-y border-blue-900/50 px-4 py-0.5 text-xs font-mono text-blue-400 select-none">
      @@ -{startA},{countA} +{startB},{countB} @@
    </div>
  );
}

function DiffHunk({ hunk }: { hunk: DiffLine[] }) {
  return (
    <div>
      <HunkHeader hunk={hunk} />
      {hunk.map((line, idx) => {
        const lineA = "lineA" in line ? line.lineA : null;
        const lineB = "lineB" in line ? line.lineB : null;
        const prefix = line.type === "removed" ? "-" : line.type === "added" ? "+" : " ";
        const bg =
          line.type === "removed"
            ? "bg-red-950/50"
            : line.type === "added"
              ? "bg-green-950/50"
              : "";
        const textColor =
          line.type === "removed"
            ? "text-red-300"
            : line.type === "added"
              ? "text-green-300"
              : "text-gray-400";
        const gutterColor =
          line.type === "removed"
            ? "text-red-700"
            : line.type === "added"
              ? "text-green-700"
              : "text-gray-700";

        return (
          <div key={idx} className={`flex font-mono text-xs ${bg}`}>
            {/* Gutter: old line number */}
            <span
              className={`w-10 shrink-0 text-right pr-2 select-none ${gutterColor} border-r border-gray-800`}
            >
              {lineA ?? ""}
            </span>
            {/* Gutter: new line number */}
            <span
              className={`w-10 shrink-0 text-right pr-2 select-none ${gutterColor} border-r border-gray-800`}
            >
              {lineB ?? ""}
            </span>
            {/* +/- prefix */}
            <span className={`w-5 shrink-0 text-center select-none ${textColor}`}>{prefix}</span>
            {/* Content */}
            <span className={`flex-1 pl-1 whitespace-pre-wrap break-all ${textColor}`}>
              {line.text}
            </span>
          </div>
        );
      })}
    </div>
  );
}

function FieldDiff({ item }: { item: ResumeDiffItem }) {
  const original = tryParseJson(item.original);
  const tailored = tryParseJson(item.tailored);
  const lines = computeLineDiff(original, tailored);
  const hunks = sliceHunks(lines);

  // File header line counts
  const removedCount = lines.filter((l) => l.type === "removed").length;
  const addedCount = lines.filter((l) => l.type === "added").length;

  return (
    <div className="border border-gray-800 rounded-lg overflow-hidden text-xs">
      {/* File header */}
      <div className="flex items-center gap-3 bg-gray-800/80 px-3 py-2 border-b border-gray-700">
        <span className="font-mono text-gray-200 flex-1">{item.field}</span>
        {removedCount > 0 && (
          <span className="text-red-400 font-mono">−{removedCount}</span>
        )}
        {addedCount > 0 && (
          <span className="text-green-400 font-mono">+{addedCount}</span>
        )}
      </div>

      {hunks.length === 0 ? (
        <div className="px-4 py-2 text-gray-600 font-mono">No textual changes</div>
      ) : (
        hunks.map((hunk, idx) => <DiffHunk key={idx} hunk={hunk} />)
      )}
    </div>
  );
}

export function ResumeDiff({ diff }: ResumeDiffProps) {
  if (diff.length === 0) {
    return (
      <div className="text-gray-500 text-sm py-4 text-center">
        No changes were made to the resume.
      </div>
    );
  }

  const totalRemoved = diff.reduce((acc, item) => {
    const original = tryParseJson(item.original);
    const tailored = tryParseJson(item.tailored);
    return acc + computeLineDiff(original, tailored).filter((l) => l.type === "removed").length;
  }, 0);

  const totalAdded = diff.reduce((acc, item) => {
    const original = tryParseJson(item.original);
    const tailored = tryParseJson(item.tailored);
    return acc + computeLineDiff(original, tailored).filter((l) => l.type === "added").length;
  }, 0);

  return (
    <div className="space-y-3">
      {/* Summary bar */}
      <div className="flex items-center gap-4 text-xs font-mono px-1">
        <span className="text-gray-500">{diff.length} file{diff.length !== 1 ? "s" : ""} changed</span>
        {totalAdded > 0 && <span className="text-green-400">+{totalAdded} insertions</span>}
        {totalRemoved > 0 && <span className="text-red-400">−{totalRemoved} deletions</span>}
      </div>

      {diff.map((item) => (
        <FieldDiff key={item.field} item={item} />
      ))}
    </div>
  );
}
