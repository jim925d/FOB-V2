/**
 * SkillBridge API Client
 *
 * Drop this file into your React project at src/api/skillbridge.js
 * Set VITE_API_URL in your .env to point to your API server.
 *
 * Usage:
 *   import { fetchPrograms, fetchMapData, fetchStats } from './api/skillbridge';
 *   const programs = await fetchPrograms({ q: 'software', state: 'WA' });
 */

const API_BASE = typeof import.meta !== 'undefined'
  ? (import.meta.env?.VITE_API_URL || 'http://localhost:8000')
  : 'http://localhost:8000';

function buildParams(obj) {
  const params = new URLSearchParams();
  Object.entries(obj).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') params.set(k, v);
  });
  return params.toString();
}

async function apiGet(path, params = {}) {
  const qs = buildParams(params);
  const url = `${API_BASE}${path}${qs ? '?' + qs : ''}`;
  const resp = await fetch(url);
  if (!resp.ok) {
    const text = await resp.text().catch(() => '');
    throw new Error(`API ${resp.status}: ${text}`);
  }
  return resp.json();
}

// ─── Programs ───

export function fetchPrograms(filters = {}) {
  return apiGet('/api/v1/programs', filters);
}

export function fetchProgram(id) {
  return apiGet(`/api/v1/programs/${id}`);
}

// ─── Map ───

export function fetchMapData(filters = {}) {
  return apiGet('/api/v1/programs/map', filters);
}

// ─── Stats / Lookups ───

export function fetchStats() {
  return apiGet('/api/v1/programs/stats');
}

export function fetchIndustries() {
  return apiGet('/api/v1/industries');
}

export function fetchStates() {
  return apiGet('/api/v1/states');
}

// ─── Health ───

export function fetchHealth() {
  return apiGet('/api/v1/health');
}
