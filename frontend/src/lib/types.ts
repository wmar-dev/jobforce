export type PipelineStatus =
  | "saved"
  | "applied"
  | "interviewing"
  | "offer"
  | "rejected"
  | "withdrawn";

export type FitConfidence = "high" | "medium" | "low";

export type RoleType = "full-time" | "part-time" | "contract" | "internship" | "other";

export interface Company {
  id: number;
  name: string;
  domain?: string | null;
}

export interface StatusTransition {
  id: number;
  from_status: PipelineStatus | null;
  to_status: PipelineStatus;
  transitioned_at: string;
}

export interface JobListing {
  id: number;
  title: string;
  company: Company;
  location?: string | null;
  role_type?: RoleType | null;
  source_url: string;
  status: PipelineStatus;
  fit_scored: boolean;
  fit_score?: number | null;
  fit_confidence?: FitConfidence | null;
  fit_rationale?: string | null;
  crawled_at?: string | null;
  created_at: string;
}

export interface JobListingDetail extends JobListing {
  description?: string | null;
  status_history: StatusTransition[];
}

export interface JobListPage {
  total: number;
  items: JobListing[];
}

export interface OracleRankResult {
  job_id: number;
  score: number;
  confidence: FitConfidence;
  rationale: string;
  warning?: string | null;
  scored_at?: string;
}

export interface OracleRankResponse {
  ranked: OracleRankResult[];
}

export interface PersonalInfo {
  name: string;
  email: string;
  phone?: string | null;
  location?: string | null;
  linkedin?: string | null;
  github?: string | null;
  website?: string | null;
}

export interface WorkHistoryItem {
  title: string;
  company: string;
  start_date: string;
  end_date?: string | null;
  location?: string | null;
  bullets: string[];
}

export interface EducationItem {
  degree: string;
  institution: string;
  start_date?: string | null;
  end_date?: string | null;
  gpa?: string | null;
  notes?: string | null;
}

export interface CertificationItem {
  name: string;
  issuer?: string | null;
  year?: number | null;
}

export interface ProjectItem {
  name: string;
  description?: string | null;
  url?: string | null;
  bullets: string[];
}

export interface ResumeStructuredData {
  personal_info: PersonalInfo;
  summary?: string | null;
  work_history: WorkHistoryItem[];
  education: EducationItem[];
  skills: string[];
  certifications?: CertificationItem[];
  projects?: ProjectItem[];
}

export interface ResumeDiffItem {
  field: string;
  original: string;
  tailored: string;
}

export interface Resume {
  id: number;
  label: string;
  is_base: boolean;
  job_listing_id?: number | null;
  structured_data: ResumeStructuredData;
  created_at: string;
  updated_at: string;
}

export interface TailoredResumeResponse extends Resume {
  diff: ResumeDiffItem[];
}

export interface QuestionItem {
  id: string;
  category: "behavioral" | "coding" | "system_design" | "role_specific";
  text: string;
  source_url?: string | null;
  leetcode_url?: string | null;
  guidance?: string | null;
  user_answer?: string | null;
  coach_feedback?: string | null;
}

export interface InterviewSession {
  session_id: number;
  job_id: number;
  questions: QuestionItem[];
}

export interface AnswerFeedback {
  question_id: string;
  feedback: string;
  score: number;
}

export interface SessionSummary {
  session_id: number;
  overall_score: number;
  summary: string;
  areas_to_improve: string[];
}

export interface MeetingNote {
  id: number;
  company_id: number;
  job_listing_id?: number | null;
  body: string;
  created_at: string;
}

export interface DashboardSummary {
  pipeline: Record<PipelineStatus, number>;
  recent_transitions: Array<{
    job_id: number;
    title: string;
    to_status: PipelineStatus;
    at: string;
  }>;
  recent_notes: Array<{
    id: number;
    company: string;
    body: string;
    created_at: string;
  }>;
}

export interface UserProfile {
  full_name?: string | null;
  headline?: string | null;
  skills: string[];
  experience?: object[] | null;
  preferences?: object | null;
}
