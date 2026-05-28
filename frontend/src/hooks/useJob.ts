import useSWR from "swr";
import { getJob } from "@/lib/api";
import type { JobListingDetail } from "@/lib/types";

export function useJob(id: number) {
  return useSWR<JobListingDetail>(`/api/jobs/${id}`, () => getJob(id));
}
