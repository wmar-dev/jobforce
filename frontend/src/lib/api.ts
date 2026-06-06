import type {
  JobListing,
  JobListingDetail,
  JobListPage,
  JobNote,
  OracleRankResponse,
  OracleRankResult,
  Resume,
  TailoredResumeResponse,
  InterviewSession,
  DashboardSummary,
  CompanyDetail,
  MeetingNote,
  UserProfile,
  PipelineStatus,
  RoleType,
  ExportResponse,
} from "./types";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? (typeof window !== "undefined" ? "" : "http://localhost:8000");

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: res.statusText }));
    throw Object.assign(new Error(detail.detail ?? res.statusText), {
      status: res.status,
      code: detail.code,
    });
  }
  return res.json() as Promise<T>;
}

// Jobs
export type JobSortKey = "fit_score" | "created_at" | "title" | "status" | "company";
export type SortDir = "asc" | "desc";

export interface JobFilters {
  status?: PipelineStatus;
  company_id?: number;
  min_score?: number;
  location?: string;
  role_type?: RoleType;
  sort_by?: JobSortKey;
  sort_dir?: SortDir;
  limit?: number;
  offset?: number;
}

export function getJobs(filters: JobFilters = {}): Promise<JobListPage> {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([k, v]) => {
    if (v !== undefined && v !== null) params.set(k, String(v));
  });
  const qs = params.toString();
  return apiFetch<JobListPage>(`/api/jobs${qs ? `?${qs}` : ""}`);
}

export function getJob(id: number): Promise<JobListingDetail> {
  return apiFetch<JobListingDetail>(`/api/jobs/${id}`);
}

export function patchJobStatus(
  id: number,
  status: PipelineStatus
): Promise<{ id: number; status: PipelineStatus; transitioned_at: string }> {
  return apiFetch(`/api/jobs/${id}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

export function bulkArchive(companyId?: number): Promise<{ archived_count: number }> {
  const qs = companyId !== undefined ? `?company_id=${companyId}` : "";
  return apiFetch(`/api/jobs/bulk-archive${qs}`, { method: "POST" });
}

// Job notes
export function getJobNote(jobId: number): Promise<JobNote> {
  return apiFetch<JobNote>(`/api/jobs/${jobId}/note`);
}

export function upsertJobNote(jobId: number, body: string): Promise<JobNote> {
  return apiFetch<JobNote>(`/api/jobs/${jobId}/note`, {
    method: "PUT",
    body: JSON.stringify({ body }),
  });
}

export function deleteJobNote(jobId: number): Promise<void> {
  return apiFetch<void>(`/api/jobs/${jobId}/note`, { method: "DELETE" });
}

// Ingest
export interface IngestPayload {
  source_url: string;
  html: string;
  title: string;
  company_name: string;
  location?: string;
  role_type?: string;
  description?: string;
}

export function ingestJob(
  payload: IngestPayload
): Promise<{ id: number; status: string; company_id: number; duplicate: boolean }> {
  return apiFetch("/api/ingest", { method: "POST", body: JSON.stringify(payload) });
}

// Oracle — ranking is performed by Claude Code via /oracle-rank skill

export function getJobRank(jobId: number): Promise<OracleRankResult> {
  return apiFetch<OracleRankResult>(`/api/oracle/rank/${jobId}`);
}

// Profile
export function getProfile(): Promise<UserProfile> {
  return apiFetch<UserProfile>("/api/profile");
}

export function putProfile(profile: UserProfile): Promise<UserProfile> {
  return apiFetch("/api/profile", { method: "PUT", body: JSON.stringify(profile) });
}

// Forge
export function getBaseResume(): Promise<Resume> {
  return apiFetch<Resume>("/api/resume/base");
}

export function putBaseResume(resume: Resume): Promise<Resume> {
  return apiFetch("/api/resume/base", { method: "PUT", body: JSON.stringify(resume) });
}

export function tailorResume(
  jobId: number,
  baseResumeId: number
): Promise<TailoredResumeResponse> {
  return apiFetch("/api/resume/tailor", {
    method: "POST",
    body: JSON.stringify({ job_id: jobId, base_resume_id: baseResumeId }),
  });
}

export async function exportResume(resumeId: number): Promise<ExportResponse> {
  const res = await fetch(`${BASE_URL}/api/resume/${resumeId}/export`, { method: "POST" });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: res.statusText }));
    throw Object.assign(new Error(detail.detail ?? res.statusText), { status: res.status });
  }
  return res.json() as Promise<ExportResponse>;
}

// Coach
export function getLatestCoachSession(jobId: number): Promise<InterviewSession> {
  return apiFetch(`/api/coach/jobs/${jobId}/latest-session`);
}

// Dashboard
export function getDashboard(): Promise<DashboardSummary> {
  return apiFetch<DashboardSummary>("/api/dashboard");
}

// Companies
export function getCompanies(): Promise<Company[]> {
  return apiFetch<Company[]>("/api/companies");
}

export function getCompany(companyId: number): Promise<CompanyDetail> {
  return apiFetch<CompanyDetail>(`/api/companies/${companyId}`);
}

export function getCompanyNotes(companyId: number): Promise<MeetingNote[]> {
  return apiFetch<MeetingNote[]>(`/api/companies/${companyId}/notes`);
}

export function createMeetingNote(
  companyId: number,
  content: string
): Promise<MeetingNote> {
  return apiFetch(`/api/companies/${companyId}/notes`, {
    method: "POST",
    body: JSON.stringify({ content }),
  });
}
