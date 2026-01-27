import { supabase } from './supabase';

const API_BASE = import.meta.env.VITE_API_BASE || '/api';

interface FetchOptions extends RequestInit {
  headers?: Record<string, string>;
}

export async function authenticatedFetch(endpoint: string, options: FetchOptions = {}) {
  const { data: { session } } = await supabase.auth.getSession();
  
  const headers: Record<string, string> = {
    ...options.headers,
    'Content-Type': 'application/json',
  };

  if (session?.access_token) {
    headers['Authorization'] = `Bearer ${session.access_token}`;
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
        errorMessage = `API Error: ${errorData.detail}`;
      }
    } catch {
      // ignore json parse error
    }
    throw new Error(errorMessage);
  }

  return response.json();
}
