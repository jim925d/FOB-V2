import { createClient } from '@supabase/supabase-js';

const supabaseUrl = (import.meta.env.VITE_SUPABASE_URL ?? '').trim();
const supabaseAnonKey = (import.meta.env.VITE_SUPABASE_ANON_KEY ?? '').trim();
const looksConfigured =
  supabaseUrl.length > 0 &&
  supabaseAnonKey.length > 0 &&
  !supabaseUrl.includes('your-project') &&
  !supabaseAnonKey.startsWith('your-');

const lock = {
  acquireLock: async (name, callback) => {
    if (typeof navigator !== 'undefined' && navigator.locks) {
      try {
        return await navigator.locks.request(name, { ifAvailable: true }, async (lock) => {
          if (lock) return await callback(lock);
          return await callback(null);
        });
      } catch { return await callback(null); }
    }
    return await callback(null);
  },
};

// Use real client only when env looks configured; otherwise use no-op auth so the app always renders
export const supabase = looksConfigured
  ? createClient(supabaseUrl, supabaseAnonKey, {
      auth: { autoRefreshToken: true, persistSession: true, detectSessionInUrl: true, lock },
    })
  : {
      auth: {
        getSession: () => Promise.resolve({ data: { session: null }, error: null }),
        onAuthStateChange: () => ({ data: { subscription: { unsubscribe: () => {} } } }),
        signInWithPassword: async () => ({ data: null, error: new Error('Supabase not configured') }),
        signUp: async () => ({ data: null, error: new Error('Supabase not configured') }),
        signInWithOtp: async () => ({ data: null, error: new Error('Supabase not configured') }),
        signInWithOAuth: async () => ({ data: null, error: new Error('Supabase not configured') }),
        signOut: async () => {},
      },
    };
