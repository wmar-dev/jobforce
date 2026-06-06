"use client";

import { useState } from "react";
import { exportResume } from "@/lib/api";

interface ExportButtonProps {
  resumeId: number;
}

type ExportState = "idle" | "loading" | "done" | "error";

interface ExportPaths {
  tex_path: string;
  pdf_path: string | null;
}

export function ExportButton({ resumeId }: ExportButtonProps) {
  const [state, setState] = useState<ExportState>("idle");
  const [paths, setPaths] = useState<ExportPaths | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleExport = async () => {
    setState("loading");
    setErrorMessage(null);
    setPaths(null);
    try {
      const result = await exportResume(resumeId);
      setPaths(result);
      setState("done");
    } catch (err) {
      setState("error");
      setErrorMessage(err instanceof Error ? err.message : "Export failed");
    }
  };

  return (
    <div>
      <button
        onClick={handleExport}
        disabled={state === "loading"}
        className="px-4 py-2 bg-amber-700 hover:bg-amber-600 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium rounded transition-colors"
      >
        {state === "loading" ? "Exporting..." : "⬇ Export Resume"}
      </button>
      {state === "done" && paths && (
        <div className="mt-2 text-xs space-y-1">
          <p className="text-green-400">
            .tex: <span className="text-gray-300 font-mono">{paths.tex_path}</span>
          </p>
          {paths.pdf_path ? (
            <p className="text-green-400">
              PDF: <span className="text-gray-300 font-mono">{paths.pdf_path}</span>
            </p>
          ) : (
            <p className="text-amber-400">
              PDF not generated — install texlive to compile PDFs
            </p>
          )}
        </div>
      )}
      {state === "error" && (
        <p className="text-red-400 text-xs mt-2">{errorMessage}</p>
      )}
    </div>
  );
}
