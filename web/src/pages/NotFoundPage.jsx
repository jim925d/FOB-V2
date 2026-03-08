import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

export default function NotFoundPage() {
  return (
    <div className="min-h-screen flex items-center justify-center p-8">
      <Card className="max-w-md w-full" style={{ background: 'var(--color-bg-secondary)', borderColor: 'var(--color-border)' }}>
        <CardContent className="pt-8 text-center">
          <h1 className="text-3xl font-serif mb-2" style={{ color: 'var(--color-text-primary)' }}>404 — Page not found</h1>
          <p className="text-sm mb-6" style={{ color: 'var(--color-text-muted)' }}>The page you’re looking for doesn’t exist.</p>
          <Button asChild>
            <Link to="/">Back to Home</Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
