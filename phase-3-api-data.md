# Phase 3 — API Client + Data Layer

## What you're building

Single unified API client for all backend (Render) calls, Supabase data functions for all user-persisted data, and generic hooks. This phase is the same regardless of UI library — it's pure data logic.

**Prerequisites:** Phase 0 + 1 + 2 complete.

---

## Step 1: Backend API Client — `src/lib/api.js`

Single module for ALL Render backend calls. No fetch() anywhere else.

```javascript
const API_BASE = import.meta.env.VITE_API_BASE;

async function fetchApi(path, options = {}) {
  const { method = 'GET', body, timeout = 15000 } = options;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method,
      headers: body ? { 'Content-Type': 'application/json' } : {},
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `API error: ${res.status}`);
    }
    return await res.json();
  } finally { clearTimeout(timer); }
}

// Career Pathfinder
export const getRoles = () => fetchApi('/api/v1/career/roles');
export const getCertifications = () => fetchApi('/api/v1/career/certifications');
export const getTargets = () => fetchApi('/api/v1/career/targets');
export const generateRoadmap = (inputs) => fetchApi('/api/v1/roadmap/generate', { method: 'POST', body: inputs, timeout: 30000 });

// SkillBridge
export const getPrograms = (params = {}) => fetchApi(`/api/v1/programs?${new URLSearchParams(params)}`);
export const getProgram = (id) => fetchApi(`/api/v1/programs/${id}`);
export const getProgramsMap = (params = {}) => fetchApi(`/api/v1/programs/map?${new URLSearchParams(params)}`);
export const getProgramStats = () => fetchApi('/api/v1/programs/stats');

// Communities, ERGs, News, Networking
export const getCommunities = (params = {}) => fetchApi(`/api/v1/communities?${new URLSearchParams(params)}`);
export const getERGs = (params = {}) => fetchApi(`/api/v1/ergs?${new URLSearchParams(params)}`);
export const getNews = (params = {}) => fetchApi(`/api/v1/news?${new URLSearchParams(params)}`);
export const analyzeNetwork = (data) => fetchApi('/api/v1/networking/analyze', { method: 'POST', body: data, timeout: 30000 });
export const generateNetworkingRoadmap = (data) => fetchApi('/api/v1/networking/roadmap', { method: 'POST', body: data, timeout: 30000 });
```

## Step 2: Supabase Data Functions — `src/lib/database.js`

All CRUD for user-persisted data. Every function takes userId first.

```javascript
import { supabase } from '@/lib/supabase';

async function query(table, userId, opts = {}) {
  let q = supabase.from(table).select(opts.select || '*').eq('user_id', userId);
  if (opts.order) q = q.order(opts.order, { ascending: false });
  const { data, error } = await q;
  if (error) throw error;
  return data;
}
async function insert(table, userId, record) {
  const { data, error } = await supabase.from(table).insert({ user_id: userId, ...record }).select().single();
  if (error) throw error;
  return data;
}
async function remove(table, id, userId) {
  const { error } = await supabase.from(table).delete().eq('id', id).eq('user_id', userId);
  if (error) throw error;
}

// Profiles
export const getProfile = async (userId) => {
  const { data, error } = await supabase.from('profiles').select('*').eq('id', userId).single();
  if (error && error.code !== 'PGRST116') throw error;
  return data;
};
export const upsertProfile = async (userId, updates) => {
  const { data, error } = await supabase.from('profiles').upsert({ id: userId, ...updates, updated_at: new Date().toISOString() }).select().single();
  if (error) throw error;
  return data;
};

// All saved items — same pattern
export const getSavedRoadmaps = (uid) => query('saved_roadmaps', uid, { order: 'created_at' });
export const saveRoadmap = (uid, rec) => insert('saved_roadmaps', uid, rec);
export const deleteSavedRoadmap = (id, uid) => remove('saved_roadmaps', id, uid);

export const getSavedPrograms = (uid) => query('saved_programs', uid, { order: 'created_at' });
export const saveProgram = (uid, rec) => insert('saved_programs', uid, rec);
export const deleteSavedProgram = (id, uid) => remove('saved_programs', id, uid);

export const getSavedERGs = (uid) => query('saved_ergs', uid, { order: 'created_at' });
export const saveERG = (uid, rec) => insert('saved_ergs', uid, rec);
export const deleteSavedERG = (id, uid) => remove('saved_ergs', id, uid);

export const getSavedCommunities = (uid) => query('saved_communities', uid, { order: 'created_at' });
export const saveCommunity = (uid, rec) => insert('saved_communities', uid, rec);
export const deleteSavedCommunity = (id, uid) => remove('saved_communities', id, uid);

export const getSavedArticles = (uid) => query('saved_articles', uid, { order: 'created_at' });
export const saveArticle = (uid, rec) => insert('saved_articles', uid, rec);
export const deleteSavedArticle = (id, uid) => remove('saved_articles', id, uid);

export const getBenefitsProgress = (uid) => query('benefits_progress', uid);
export const upsertBenefitProgress = async (uid, type, updates) => {
  const { data, error } = await supabase.from('benefits_progress')
    .upsert({ user_id: uid, benefit_type: type, ...updates, updated_at: new Date().toISOString() }, { onConflict: 'user_id,benefit_type' })
    .select().single();
  if (error) throw error;
  return data;
};

export const getEvents = (uid) => query('user_events', uid, { order: 'event_date' });
export const createEvent = (uid, rec) => insert('user_events', uid, rec);
export const deleteEvent = (id, uid) => remove('user_events', id, uid);

export const getReminders = (uid) => query('recurring_reminders', uid, { order: 'next_date' });
export const createReminder = (uid, rec) => insert('recurring_reminders', uid, rec);
export const deleteReminder = (id, uid) => remove('recurring_reminders', id, uid);

export const getQuickLinks = (uid) => query('dashboard_quick_links', uid, { order: 'created_at' });
export const createQuickLink = (uid, rec) => insert('dashboard_quick_links', uid, rec);
export const deleteQuickLink = (id, uid) => remove('dashboard_quick_links', id, uid);

export const getNetworkingRoadmaps = (uid) => query('networking_roadmaps', uid, { order: 'created_at' });
export const saveNetworkingRoadmap = (uid, rec) => insert('networking_roadmaps', uid, rec);
export const deleteNetworkingRoadmap = (id, uid) => remove('networking_roadmaps', id, uid);
```

## Step 3: Hooks — `src/hooks/`

**`useApi.js`:**
```javascript
import { useState, useEffect, useCallback } from 'react';

export function useApi(apiFn, ...args) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const fetch = useCallback(async () => {
    setLoading(true); setError(null);
    try { setData(await apiFn(...args)); }
    catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }, [apiFn, ...args]);
  useEffect(() => { fetch(); }, [fetch]);
  return { data, loading, error, refetch: fetch };
}

export function useLazyApi(apiFn) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const execute = useCallback(async (...args) => {
    setLoading(true); setError(null);
    try { const r = await apiFn(...args); setData(r); return r; }
    catch (e) { setError(e.message); throw e; }
    finally { setLoading(false); }
  }, [apiFn]);
  return { data, loading, error, execute };
}
```

---

## Verify

- Test a `useApi(getRoles)` call in a placeholder page — confirm it hits backend (or errors gracefully)
- Test `useLazyApi(generateRoadmap)` with a button — manual trigger works
- Test `getProfile(user.id)` when authenticated — Supabase responds
- No fetch() calls exist outside `api.js` and `database.js`

**Phase 3 complete.** Commit: `feat: phase 3 — unified API client + supabase data layer`
