import useSWR from "swr";
import { getJobs, type JobFilters } from "@/lib/api";
import type { JobListPage } from "@/lib/types";

export function useJobs(filters: JobFilters = {}) {
  const key = ["/api/jobs", filters] as const;
  return useSWR<JobListPage>(key, () => getJobs(filters), {
    refreshInterval: 30_000,
  });
}
