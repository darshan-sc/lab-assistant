// Project types
export interface Project {
  id: number;
  user_id: number;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
  role: string | null;
  member_count: number | null;
}

export interface ProjectCreate {
  name: string;
  description?: string;
}

export interface ProjectUpdate {
  name?: string;
  description?: string;
}

export interface ProjectMember {
  id: number;
  user_id: number;
  email: string;
  role: 'owner' | 'member';
  added_at: string;
}

export interface ProjectInvite {
  id: number;
  code: string;
  created_at: string;
  expires_at: string | null;
  is_active: boolean;
}

// Paper types
export interface Paper {
  id: number;
  user_id: number;
  project_id: number | null;
  title: string | null;
  abstract: string | null;
  pdf_path: string | null;
  processing_status: 'pending' | 'processing' | 'completed' | 'failed';
  processing_error: string | null;
  is_indexed_for_rag?: boolean;
}

export interface PaperUpdate {
  title?: string;
  abstract?: string;
}

// Experiment types
export interface Experiment {
  id: number;
  user_id: number;
  project_id: number | null;
  paper_id: number | null;
  title: string;
  goal: string | null;
  protocol: string | null;
  results: string | null;
  status: 'active' | 'paused' | 'completed';
  created_at: string;
  updated_at: string;
}

export interface ExperimentCreate {
  title: string;
  goal?: string;
  protocol?: string;
  paper_id?: number;
}

export interface ExperimentUpdate {
  title?: string;
  goal?: string;
  protocol?: string;
  results?: string;
  status?: string;
  paper_id?: number;
}

// Experiment Run types
export interface ExperimentRun {
  id: number;
  user_id: number;
  project_id: number | null;
  experiment_id: number;
  run_name: string | null;
  status: 'planned' | 'running' | 'done' | 'failed';
  config: Record<string, unknown> | null;
  metrics: Record<string, unknown> | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface RunCreate {
  run_name?: string;
  config?: Record<string, unknown>;
}

export interface RunUpdate {
  run_name?: string;
  status?: string;
  config?: Record<string, unknown>;
  metrics?: Record<string, unknown>;
  started_at?: string;
  finished_at?: string;
}

// Note types
export interface Note {
  id: number;
  user_id: number;
  project_id: number | null;
  paper_id: number | null;
  experiment_id: number | null;
  experiment_run_id: number | null;
  content: string;
  created_at: string;
}

export interface NoteCreate {
  content: string;
  project_id?: number;
  paper_id?: number;
  experiment_id?: number;
  experiment_run_id?: number;
}

export interface NoteUpdate {
  content?: string;
}

// Q&A types
export interface QAResponse {
  answer: string;
  sources?: string[];
}
