import useSWR from "swr";
import { getJobNote } from "@/lib/api";
import type { JobNote } from "@/lib/types";

export function useJobNote(jobId: number) {
  return useSWR<JobNote | null>(
    `/api/jobs/${jobId}/note`,
    () => getJobNote(jobId).catch((err: { status?: number }) => {
      if (err?.status === 404) return null;
      throw err;
    }),
  );
}
