import { useState } from 'react';
import toast from 'react-hot-toast';
import { useAuth } from '@/contexts/AuthContext';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

function passwordStrength(pwd) {
  if (!pwd) return 0;
  let score = 0;
  if (pwd.length >= 8) score += 25;
  if (pwd.length >= 12) score += 15;
  if (/[A-Z]/.test(pwd)) score += 20;
  if (/[0-9]/.test(pwd)) score += 20;
  if (/[^A-Za-z0-9]/.test(pwd)) score += 20;
  return Math.min(100, score);
}

function strengthColorClass(score) {
  if (score <= 25) return '[&>div]:bg-destructive';
  if (score <= 50) return '[&>div]:bg-amber-500';
  if (score <= 75) return '[&>div]:bg-yellow-500';
  return '[&>div]:bg-green-500';
}

export default function AuthModal({
  open,
  onOpenChange,
  defaultTab = 'signin',
  contextMessage = 'Sign in to save your progress',
  onSuccess,
}) {
  const {
    signInWithPassword,
    signUp,
    signInWithMagicLink,
    signInWithGoogle,
  } = useAuth();

  const [tab, setTab] = useState(defaultTab);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [magicLinkEmail, setMagicLinkEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [magicLinkSent, setMagicLinkSent] = useState(false);

  const strength = passwordStrength(password);
  const strengthClass = strengthColorClass(strength);

  const resetForm = () => {
    setEmail('');
    setPassword('');
    setConfirmPassword('');
    setMagicLinkEmail('');
    setError('');
    setMagicLinkSent(false);
  };

  const handleOpenChange = (next) => {
    if (!next) resetForm();
    onOpenChange(next);
  };

  const handleSignIn = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await signInWithPassword(email, password);
      toast.success('Signed in successfully');
      handleOpenChange(false);
      onSuccess?.();
    } catch (err) {
      setError(err.message ?? 'Sign in failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSignUp = async (e) => {
    e.preventDefault();
    setError('');
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    setLoading(true);
    try {
      await signUp(email, password);
      toast.success('Account created. Check your email to confirm.');
      handleOpenChange(false);
      onSuccess?.();
    } catch (err) {
      setError(err.message ?? 'Sign up failed');
    } finally {
      setLoading(false);
    }
  };

  const handleMagicLink = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await signInWithMagicLink(magicLinkEmail || email);
      setMagicLinkSent(true);
      toast.success('Magic link sent to your email');
    } catch (err) {
      setError(err.message ?? 'Failed to send magic link');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogle = async () => {
    setError('');
    setLoading(true);
    try {
      await signInWithGoogle();
      handleOpenChange(false);
      onSuccess?.();
    } catch (err) {
      setError(err.message ?? 'Google sign in failed');
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent
        className="max-w-md border bg-card"
        style={{
          background: 'var(--color-bg-elevated)',
          borderColor: 'var(--color-border)',
        }}
      >
        <DialogHeader>
          <DialogTitle className="font-serif">Welcome to The FOB</DialogTitle>
          <DialogDescription>{contextMessage}</DialogDescription>
        </DialogHeader>

        <Tabs value={tab} onValueChange={setTab} className="w-full">
          <TabsList
            className="w-full bg-[var(--color-bg-tertiary)]"
            style={{ background: 'var(--color-bg-tertiary)' }}
          >
            <TabsTrigger
              value="signin"
              className={cn(
                'flex-1 data-[state=active]:bg-fob-info data-[state=active]:text-white'
              )}
            >
              Sign In
            </TabsTrigger>
            <TabsTrigger
              value="signup"
              className={cn(
                'flex-1 data-[state=active]:bg-fob-info data-[state=active]:text-white'
              )}
            >
              Sign Up
            </TabsTrigger>
          </TabsList>

          <TabsContent value="signin" className="space-y-4 pt-4">
            <form onSubmit={handleSignIn} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="signin-email">Email</Label>
                <Input
                  id="signin-email"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                  disabled={loading}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="signin-password">Password</Label>
                <Input
                  id="signin-password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                  disabled={loading}
                />
              </div>
              {error && (
                <p className="text-sm text-destructive">{error}</p>
              )}
              <Button
                type="submit"
                variant="info"
                className="w-full"
                disabled={loading}
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  'Sign In'
                )}
              </Button>
            </form>
            <Separator />
            <div className="relative flex items-center justify-center text-xs text-muted-foreground">
              <span className="bg-card px-2" style={{ background: 'var(--color-bg-elevated)' }}>or</span>
            </div>
            <Button
              type="button"
              variant="outline"
              className="w-full"
              onClick={handleGoogle}
              disabled={loading}
            >
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Continue with Google'}
            </Button>
            <Button
              type="button"
              variant="link"
              className="w-full"
              onClick={() => setMagicLinkSent(false)}
              disabled={loading}
            >
              Send magic link instead
            </Button>
            {magicLinkSent ? (
              <p className="text-sm text-muted-foreground">Check your email for the link.</p>
            ) : (
              <form onSubmit={handleMagicLink} className="flex gap-2">
                <Input
                  type="email"
                  placeholder="Email for magic link"
                  value={magicLinkEmail || email}
                  onChange={(e) => setMagicLinkEmail(e.target.value)}
                  disabled={loading}
                  className="flex-1"
                />
                <Button type="submit" variant="outline" size="sm" disabled={loading}>
                  Send
                </Button>
              </form>
            )}
          </TabsContent>

          <TabsContent value="signup" className="space-y-4 pt-4">
            <form onSubmit={handleSignUp} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="signup-email">Email</Label>
                <Input
                  id="signup-email"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoComplete="email"
                  disabled={loading}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="signup-password">Password</Label>
                <Input
                  id="signup-password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="new-password"
                  disabled={loading}
                />
                <Progress value={strength} className={cn('h-2', strengthClass)} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="signup-confirm">Confirm password</Label>
                <Input
                  id="signup-confirm"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  autoComplete="new-password"
                  disabled={loading}
                />
              </div>
              {error && (
                <p className="text-sm text-destructive">{error}</p>
              )}
              <Button
                type="submit"
                variant="info"
                className="w-full"
                disabled={loading}
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  'Create Account'
                )}
              </Button>
            </form>
            <Separator />
            <div className="relative flex items-center justify-center text-xs text-muted-foreground">
              <span className="bg-card px-2" style={{ background: 'var(--color-bg-elevated)' }}>or</span>
            </div>
            <Button
              type="button"
              variant="outline"
              className="w-full"
              onClick={handleGoogle}
              disabled={loading}
            >
              Continue with Google
            </Button>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
