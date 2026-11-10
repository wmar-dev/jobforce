// API shapes are generated from backend/openapi.yaml (`npm run gen:api`) into
// ./api-schema.d.ts. This module only gives them stable frontend names, so a
// backend change surfaces as a type error here instead of a runtime surprise.
// Do not hand-write API shapes; regenerate instead.
import type { components } from "./api-schema";

type Schemas = components["schemas"];

// Jobs
export type JobListing = Schemas["JobListingOut"];
export type JobListingDetail = Schemas["JobListingDetail"];
export type JobListPage = Schemas["JobListPage"];
export type JobNote = Schemas["JobNoteOut"];
export type StatusTransition = Schemas["StatusTransitionOut"];

export type PipelineStatus = JobListing["status"];
export type RoleType = NonNullable<JobListing["role_type"]>;
export type FitConfidence = NonNullable<JobListing["fit_confidence"]>;

// Oracle
export type OracleRankResult = Schemas["RankResult"];

// Forge
export type Resume = Schemas["ResumeOut"];
export type TailoredResumeResponse = Schemas["TailoredResumeOut"];
export type ResumeDiffItem = Schemas["ResumeDiffItem"];
export type ResumeStructuredData = Schemas["ResumeStructuredData"];
export type PersonalInfo = Schemas["PersonalInfo"];
export type WorkHistoryItem = Schemas["WorkHistoryItem"];
export type EducationItem = Schemas["EducationItem"];
export type ProjectItem = Schemas["ProjectItem"];
export type CertificationItem = Schemas["CertificationItem"];
export type ExportResponse = Schemas["ExportOut"];

// Coach
export type InterviewSession = Schemas["PrepSessionOut"];
export type QuestionItem = Schemas["QuestionOut"];

// Companies & dashboard
export type Company = Schemas["CompanyListItem"];
export type CompanyDetail = Schemas["CompanyDetail"];
export type MeetingNote = Schemas["NoteOut"];
export type DashboardSummary = Schemas["DashboardOut"];

// Error bodies: branch on `code`, never on `detail` text.
export type BusinessError = Schemas["BusinessError"];
export type ErrorCode = BusinessError["code"];
