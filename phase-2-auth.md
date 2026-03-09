# Phase 2 — Auth + Supabase (shadcn/ui)

## What you're building

Supabase auth with shadcn Dialog for modals, shadcn Input/Label for forms, shadcn Tabs for sign-in/sign-up toggle.

**Prerequisites:** Phase 0 + 1 complete.

---

## Step 1: Install Supabase

```bash
npm install @supabase/supabase-js
```

## Step 2: Supabase Client — `src/lib/supabase.js`

```javascript
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

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

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: { autoRefreshToken: true, persistSession: true, detectSessionInUrl: true, lock },
});
```

## Step 3: Auth Context — `src/contexts/AuthContext.jsx`

```javascript
import { createContext, useContext, useState, useEffect } from 'react';
import { supabase } from '@/lib/supabase';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session); setUser(session?.user ?? null); setLoading(false);
    });
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session); setUser(session?.user ?? null); setLoading(false);
    });
    return () => subscription.unsubscribe();
  }, []);

  const signInWithPassword = async (email, password) => {
    const { data, error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) throw error; return data;
  };
  const signUp = async (email, password) => {
    const { data, error } = await supabase.auth.signUp({ email, password });
    if (error) throw error; return data;
  };
  const signInWithMagicLink = async (email) => {
    const { data, error } = await supabase.auth.signInWithOtp({ email });
    if (error) throw error; return data;
  };
  const signInWithGoogle = async () => {
    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: 'google', options: { redirectTo: window.location.origin },
    });
    if (error) throw error; return data;
  };
  const signOut = async () => { await supabase.auth.signOut(); };

  return (
    <AuthContext.Provider value={{ user, session, loading, signInWithPassword, signUp, signInWithMagicLink, signInWithGoogle, signOut, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};
```

Wrap app in `main.jsx`:
```jsx
<AuthProvider><BrowserRouter><App /><Toaster ... /></BrowserRouter></AuthProvider>
```

## Step 4: Auth Modal — `src/components/auth/AuthModal.jsx`

Uses shadcn `Dialog`, `Tabs`, `Input`, `Label`, `Button`, `Progress`.

```jsx
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
```

**Props:** `open`, `onOpenChange`, `defaultTab` ("signin"/"signup"), `contextMessage`

**Structure:**
```
DialogContent (max-w-md, bg card, border)
  DialogHeader
    DialogTitle: "Welcome to The FOB" (font-serif)
    DialogDescription: contextMessage or "Sign in to save your progress"
  
  Tabs defaultValue={defaultTab}
    TabsList (full width, bg --color-bg-tertiary)
      TabsTrigger "Sign In" — active: bg-fob-info text-white
      TabsTrigger "Sign Up" — active: bg-fob-info text-white
    
    TabsContent "signin":
      Label + Input (email)
      Label + Input (password, type="password")
      Button variant="info" full width: "Sign In"
      Separator with "or" text
      Button variant="outline" full width: "Continue with Google"
      Button variant="link": "Send magic link instead"
    
    TabsContent "signup":
      Label + Input (email)
      Label + Input (password)
      Label + Input (confirm password)
      Progress bar (password strength: red/orange/yellow/green)
      Button variant="info" full width: "Create Account"
      Separator + Google button
```

**Behavior:**
- Loading state: Button shows spinner
- Error: text-destructive below field
- Success: toast + dialog closes
- Password strength: calculate from length + has uppercase + has number + has special char

## Step 5: ProtectedAction — `src/components/auth/ProtectedAction.jsx`

```jsx
import { useAuth } from "@/contexts/AuthContext";
import AuthModal from "./AuthModal";
import { useState } from "react";

export function ProtectedAction({ children, message, onAuthenticated }) {
  const { isAuthenticated } = useAuth();
  const [showAuth, setShowAuth] = useState(false);
  const [pendingAction, setPendingAction] = useState(false);

  const handleClick = () => {
    if (isAuthenticated) {
      onAuthenticated();
    } else {
      setPendingAction(true);
      setShowAuth(true);
    }
  };

  const handleAuth = () => {
    setShowAuth(false);
    if (pendingAction) {
      onAuthenticated();
      setPendingAction(false);
    }
  };

  return (
    <>
      {children({ onClick: handleClick })}
      <AuthModal
        open={showAuth}
        onOpenChange={setShowAuth}
        contextMessage={message}
        defaultTab="signin"
      />
    </>
  );
}
```

**Usage:**
```jsx
<ProtectedAction message="Sign in to save this career map" onAuthenticated={() => saveRoadmap(data)}>
  {({ onClick }) => <Button variant="info" onClick={onClick}>Save to Dashboard</Button>}
</ProtectedAction>
```

## Step 6: Update AppNav

Wire in real auth state using `useAuth()`. Show Avatar + DropdownMenu when signed in, Sign In button when not.

---

## Verify

- "Sign In" button in nav opens Dialog
- Tabs switch between Sign In / Sign Up
- shadcn Input fields render with dark theme
- Password strength Progress bar works
- Google button + magic link are present
- Sign up creates account, toast shows, dialog closes
- Sign in authenticates, nav shows avatar
- Sign out works
- ProtectedAction: signed out → opens auth modal with context message
- ProtectedAction: signed in → executes action directly
- Session persists on page refresh

**Phase 2 complete.** Commit: `feat: phase 2 — supabase auth with shadcn dialog + forms`
