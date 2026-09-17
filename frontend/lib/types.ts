export interface SkillRequirement {
  skill: string;
  level: "required" | "preferred";
}

export interface Candidate {
  id: string;
  email: string;
  name: string;
  resume_summary: string | null;
  skills: string[] | null;
  years_experience: number;
  desired_salary_min: number | null;
  desired_salary_max: number | null;
  location: string | null;
  remote_ok: boolean;
  created_at: string;
}

export interface CandidateProfileUpdate {
  name?: string;
  resume_summary?: string;
  skills?: string[];
  years_experience?: number;
  desired_salary_min?: number | null;
  desired_salary_max?: number | null;
  location?: string | null;
  remote_ok?: boolean;
}

export interface JobCard {
  id: string;
  title: string;
  company_id: string;
  company_name: string | null;
  company_industry: string | null;
  description: string | null;
  required_skills: SkillRequirement[] | null;
  salary_min: number | null;
  salary_max: number | null;
  location: string | null;
  remote_ok: boolean;
  seniority: string | null;
}

export interface JobListing {
  id: string;
  company_id: string;
  title: string;
  description: string | null;
  required_skills: SkillRequirement[] | null;
  min_years_experience: number;
  salary_min: number | null;
  salary_max: number | null;
  location: string | null;
  remote_ok: boolean;
  seniority: string | null;
  is_active: boolean;
  created_at: string;
}

export interface JobListingCreate {
  title: string;
  description?: string;
  required_skills?: SkillRequirement[];
  min_years_experience?: number;
  salary_min?: number | null;
  salary_max?: number | null;
  location?: string | null;
  remote_ok?: boolean;
  seniority?: string | null;
}

export interface Application {
  id: string;
  match_id: string;
  candidate_id: string;
  job_listing_id: string;
  status: "submitted" | "viewed" | "rejected" | "interview";
  created_at: string;
  candidate?: Candidate;
  score?: number;
}

export interface Match {
  id: string;
  candidate_id: string;
  job_listing_id: string;
  score: number;
  status: "applied" | "withdrawn" | "pending";
  matched_at: string | null;
  created_at: string;
  job?: JobCard;
  job_listing?: any;
}

export interface MatchBreakdown {
  id: string;
  score: number;
  score_breakdown: {
    embedding_similarity: number;
    skill_overlap: number;
    experience_fit: number;
    salary_overlap: number;
    total: number;
    used_embedding_fallback?: boolean;
  } | null;
  status: string;
}

export interface FeedResponse {
  items: JobCard[];
  next_cursor: string | null;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface DashboardResponse {
  total_matches: number;
  total_swiped: number;
  total_applied: number;
  avg_score: number | null;
  funnel: Record<string, number>;
}

export interface ParsedResume {
  rawText: string;
  name?: string;
  email?: string;
  summary: string;
  skills: string[];
  yearsExperience: number;
  location?: string;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    field: string | null;
  };
}
