import { supabase } from '@/lib/supabase';

async function query(table, userId, opts = {}) {
  let q = supabase.from(table).select(opts.select || '*').eq('user_id', userId);
  if (opts.order) q = q.order(opts.order, { ascending: false });
  const { data, error } = await q;
  if (error) throw error;
  return data;
}
async function insert(table, userId, record) {
  const { data, error } = await supabase
    .from(table)
    .insert({ user_id: userId, ...record })
    .select()
    .single();
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
  const { data, error } = await supabase
    .from('profiles')
    .upsert({ id: userId, ...updates, updated_at: new Date().toISOString() })
    .select()
    .single();
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
  const { data, error } = await supabase
    .from('benefits_progress')
    .upsert(
      { user_id: uid, benefit_type: type, ...updates, updated_at: new Date().toISOString() },
      { onConflict: 'user_id,benefit_type' }
    )
    .select()
    .single();
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

export const getNetworkingRoadmaps = (uid) =>
  query('networking_roadmaps', uid, { order: 'created_at' });
export const saveNetworkingRoadmap = (uid, rec) => insert('networking_roadmaps', uid, rec);
export const deleteNetworkingRoadmap = (id, uid) => remove('networking_roadmaps', id, uid);
