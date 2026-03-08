import { Link, useLocation } from 'react-router-dom';
import { cn } from '@/lib/utils';

const navLinks = [
  { to: '/', label: 'Home' },
  { to: '/careers/pathfinder', label: 'Pathfinder' },
  { to: '/careers/pathfinder/map', label: 'Career Map' },
  { to: '/skillbridge', label: 'SkillBridge' },
  { to: '/benefits', label: 'Benefits' },
  { to: '/communities', label: 'Communities' },
  { to: '/employment/ergs', label: 'ERGs' },
  { to: '/employment/networking', label: 'Networking' },
  { to: '/news', label: 'News' },
  { to: '/dashboard', label: 'Dashboard' },
];

export default function AppNav() {
  const location = useLocation();

  return (
    <nav
      className="sticky top-0 z-50 border-b px-4 py-3 flex flex-wrap items-center gap-2"
      style={{
        background: 'var(--color-bg-secondary)',
        borderColor: 'var(--color-border)',
      }}
    >
      <Link
        to="/"
        className="font-serif text-lg mr-4"
        style={{ color: 'var(--color-text-primary)' }}
      >
        The FOB
      </Link>
      {navLinks.map(({ to, label }) => (
        <Link
          key={to}
          to={to}
          className={cn(
            'text-sm px-3 py-1.5 rounded-md transition-colors',
            location.pathname === to
              ? 'font-medium'
              : 'hover:opacity-90'
          )}
          style={{
            color: location.pathname === to ? 'var(--color-accent)' : 'var(--color-text-muted)',
            background: location.pathname === to ? 'var(--color-accent-dim)' : 'transparent',
          }}
        >
          {label}
        </Link>
      ))}
    </nav>
  );
}
