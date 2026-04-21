/**
 * API client for communicating with the Remailder backend through Kong Gateway.
 * All requests go through /api/ prefix which Kong routes to the correct service.
 */

const API_BASE = '/api';

interface ApiOptions {
  method?: string;
  body?: unknown;
  token?: string | null;
  headers?: Record<string, string>;
}

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

async function request<T>(endpoint: string, options: ApiOptions = {}): Promise<T> {
  const { method = 'GET', body, token, headers: extraHeaders } = options;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...extraHeaders,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const config: RequestInit = {
    method,
    headers,
  };

  if (body) {
    config.body = JSON.stringify(body);
  }

  const response = await fetch(`${API_BASE}${endpoint}`, config);

  if (!response.ok) {
    let errorMessage = 'Eroare necunoscută';
    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorData.message || errorMessage;
    } catch {
      errorMessage = response.statusText;
    }
    throw new ApiError(errorMessage, response.status);
  }

  return response.json();
}

// --- Auth API ---

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user_id: number;
  email: string;
}

export async function apiRegister(email: string, password: string): Promise<TokenResponse> {
  return request<TokenResponse>('/auth/register', {
    method: 'POST',
    body: { email, password },
  });
}

export async function apiLogin(email: string, password: string): Promise<TokenResponse> {
  return request<TokenResponse>('/auth/login', {
    method: 'POST',
    body: { email, password },
  });
}

export async function apiGetProfile(token: string) {
  return request<{ user_id: number; email: string }>('/auth/me', { token });
}

// --- Email API ---

export interface EmailTemplate {
  style_name: string;
  placeholders: string[];
  html: string;
}

export async function apiGetTemplates(token: string): Promise<Record<string, EmailTemplate>> {
  return request('/main/templates', { token });
}

export interface ScheduleEmailPayload {
  to: string;
  subject: string;
  body: string;
  scheduled_at: string;
  is_html?: boolean;
}

export async function apiScheduleEmail(payload: ScheduleEmailPayload, token: string, userId: number) {
  return request('/main/schedule', {
    method: 'POST',
    body: payload,
    token,
    headers: { 'X-User-Id': String(userId) },
  });
}

export interface EmailLog {
  id: number;
  id_user: number;
  recipient: string;
  subject: string;
  status: string;
  created_at: string;
  scheduled_at: string | null;
}

export async function apiGetHistory(token: string, userId: number): Promise<EmailLog[]> {
  return request('/main/history', {
    token,
    headers: { 'X-User-Id': String(userId) },
  });
}

export { ApiError };
