import { supabase } from './supabase';
import type {
  Project,
  ProjectCreate,
  ProjectUpdate,
  Paper,
  PaperUpdate,
  Experiment,
  ExperimentCreate,
  ExperimentUpdate,
  ExperimentRun,
  RunCreate,
  RunUpdate,
  Note,
  NoteCreate,
  NoteUpdate,
  QAResponse,
} from '../types';

const API_BASE = import.meta.env.VITE_API_BASE || '/api';

async function getAuthHeaders(): Promise<Record<string, string>> {
  const { data: { session } } = await supabase.auth.getSession();
  const headers: Record<string, string> = {};
  if (session?.access_token) {
    headers['Authorization'] = `Bearer ${session.access_token}`;
  }
  return headers;
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const authHeaders = await getAuthHeaders();

  const headers: Record<string, string> = {
    ...authHeaders,
    ...(options.headers as Record<string, string> || {}),
  };

  // Only set Content-Type for JSON requests (not file uploads)
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorMessage = `API Error: ${response.statusText}`;
    try {
      const errorData = await response.json();
      if (errorData.detail) {
        errorMessage = errorData.detail;
      }
    } catch {
      // ignore json parse error
    }
    throw new Error(errorMessage);
  }

  // Handle empty responses
  const text = await response.text();
  if (!text) return {} as T;
  return JSON.parse(text);
}

// Project endpoints
export const projectsApi = {
  list: () => request<Project[]>('/projects'),

  get: (id: number) => request<Project>(`/projects/${id}`),

  create: (data: ProjectCreate) =>
    request<Project>('/projects', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (id: number, data: ProjectUpdate) =>
    request<Project>(`/projects/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  delete: (id: number) =>
    request<void>(`/projects/${id}`, {
      method: 'DELETE',
    }),

  askQuestion: (id: number, question: string) =>
    request<QAResponse>(`/projects/${id}/qa?question=${encodeURIComponent(question)}`, {
      method: 'POST',
    }),
};

// Paper endpoints
export const papersApi = {
  list: (projectId?: number) => {
    const params = projectId ? `?project_id=${projectId}` : '';
    return request<Paper[]>(`/papers${params}`);
  },

  get: (id: number) => request<Paper>(`/papers/${id}`),

  upload: async (file: File, projectId?: number) => {
    const formData = new FormData();
    formData.append('file', file);
    const params = projectId ? `?project_id=${projectId}` : '';
    return request<Paper>(`/papers/upload${params}`, {
      method: 'POST',
      body: formData,
    });
  },

  update: (id: number, data: PaperUpdate) =>
    request<Paper>(`/papers/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  delete: (id: number) =>
    request<void>(`/papers/${id}`, {
      method: 'DELETE',
    }),

  index: (id: number) =>
    request<{ message: string }>(`/papers/${id}/index`, {
      method: 'POST',
    }),

  askQuestion: (id: number, question: string) =>
    request<QAResponse>(`/papers/${id}/qa?question=${encodeURIComponent(question)}`, {
      method: 'POST',
    }),
};

// Experiment endpoints
export const experimentsApi = {
  list: (projectId: number) =>
    request<Experiment[]>(`/projects/${projectId}/experiments`),

  get: (id: number) => request<Experiment>(`/experiments/${id}`),

  create: (projectId: number, data: ExperimentCreate) =>
    request<Experiment>(`/projects/${projectId}/experiments`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (id: number, data: ExperimentUpdate) =>
    request<Experiment>(`/experiments/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  delete: (id: number) =>
    request<void>(`/experiments/${id}`, {
      method: 'DELETE',
    }),
};

// Experiment Run endpoints
export const runsApi = {
  list: (experimentId: number) =>
    request<ExperimentRun[]>(`/experiments/${experimentId}/runs`),

  get: (id: number) => request<ExperimentRun>(`/runs/${id}`),

  create: (experimentId: number, data: RunCreate) =>
    request<ExperimentRun>(`/experiments/${experimentId}/runs`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (id: number, data: RunUpdate) =>
    request<ExperimentRun>(`/runs/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  delete: (id: number) =>
    request<void>(`/runs/${id}`, {
      method: 'DELETE',
    }),
};

// Note endpoints
export const notesApi = {
  list: (filters: {
    project_id?: number;
    paper_id?: number;
    experiment_id?: number;
    experiment_run_id?: number;
  }) => {
    const params = new URLSearchParams();
    if (filters.project_id) params.append('project_id', filters.project_id.toString());
    if (filters.paper_id) params.append('paper_id', filters.paper_id.toString());
    if (filters.experiment_id) params.append('experiment_id', filters.experiment_id.toString());
    if (filters.experiment_run_id) params.append('experiment_run_id', filters.experiment_run_id.toString());
    const queryString = params.toString();
    return request<Note[]>(`/notes${queryString ? `?${queryString}` : ''}`);
  },

  create: (data: NoteCreate) =>
    request<Note>('/notes', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (id: number, data: NoteUpdate) =>
    request<Note>(`/notes/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  delete: (id: number) =>
    request<void>(`/notes/${id}`, {
      method: 'DELETE',
    }),
};
