import { browser } from '$app/environment';
import { writable } from 'svelte/store';

const STORAGE_KEY = 'anpr_access_token';

const initialToken = browser ? localStorage.getItem(STORAGE_KEY) ?? '' : '';

export const authToken = writable<string>(initialToken);

export function setAuthToken(token: string): void {
  authToken.set(token);
  if (browser) {
    localStorage.setItem(STORAGE_KEY, token);
  }
}

export function clearAuthToken(): void {
  authToken.set('');
  if (browser) {
    localStorage.removeItem(STORAGE_KEY);
  }
}
