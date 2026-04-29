import { get } from 'svelte/store';

import { authToken, clearAuthToken } from '$lib/stores/auth';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

type RequestOptions = RequestInit & {
  skipAuth?: boolean;
};

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const token = get(authToken);
  const headers = new Headers(options.headers ?? {});

  if (!options.skipAuth && token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers
  });

  if (response.status === 401) {
    clearAuthToken();
    throw new Error('Unauthorized');
  }

  if (!response.ok) {
    const maybeJson = await response.json().catch(() => null);
    const detail = maybeJson?.detail ?? response.statusText;
    throw new Error(detail || 'Request failed');
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export const api = {
  get: <T>(path: string, options?: RequestOptions) =>
    request<T>(path, { method: 'GET', ...options }),
  post: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, {
      method: 'POST',
      body: body !== undefined ? JSON.stringify(body) : undefined,
      headers: {
        'Content-Type': 'application/json',
        ...(options?.headers ?? {})
      },
      ...options
    }),
  put: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, {
      method: 'PUT',
      body: body !== undefined ? JSON.stringify(body) : undefined,
      headers: {
        'Content-Type': 'application/json',
        ...(options?.headers ?? {})
      },
      ...options
    }),
  delete: <T>(path: string, options?: RequestOptions) =>
    request<T>(path, { method: 'DELETE', ...options })
};
