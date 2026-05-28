"use client";

import { useState } from "react";
import { exportResumePdf } from "@/lib/api";

interface PDFDownloadButtonProps {
  resumeId: number;
  filename?: string;
}

export function PDFDownloadButton({ resumeId, filename = "resume.pdf" }: PDFDownloadButtonProps) {
  const [state, setState] = useState<"idle" | "loading" | "error" | "unavailable">("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleExport = async () => {
    setState("loading");
    setErrorMessage(null);
    try {
      const blob = await exportResumePdf(resumeId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      setState("idle");
    } catch (err) {
      if (err instanceof Error) {
        const statusErr = err as Error & { status?: number };
        if (statusErr.status === 503) {
          setState("unavailable");
          setErrorMessage("LaTeX not installed — install texlive to generate PDFs");
        } else {
          setState("error");
          setErrorMessage(err.message);
        }
      } else {
        setState("error");
        setErrorMessage("Export failed");
      }
    }
  };

  return (
    <div>
      <button
        onClick={handleExport}
        disabled={state === "loading" || state === "unavailable"}
        className="px-4 py-2 bg-amber-700 hover:bg-amber-600 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium rounded transition-colors"
      >
        {state === "loading" ? "Generating PDF..." : "⬇ Download PDF"}
      </button>
      {state === "unavailable" && (
        <p className="text-amber-400 text-xs mt-2">
          {errorMessage || "LaTeX not available"}
        </p>
      )}
      {state === "error" && (
        <p className="text-red-400 text-xs mt-2">{errorMessage}</p>
      )}
    </div>
  );
}
