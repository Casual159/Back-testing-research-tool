'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ChevronRight, Home } from 'lucide-react';
import { cn } from '@/lib/utils';

interface BreadcrumbItem {
  label: string;
  href: string;
}

const routeLabels: Record<string, string> = {
  projects: 'Projects',
  strategies: 'Strategies',
  data: 'Data',
  backtest: 'Backtest',
  results: 'Results',
  settings: 'Settings',
  new: 'New',
  create: 'Create',
};

export function Breadcrumbs() {
  const pathname = usePathname();

  // Don't show on home or onboarding
  if (pathname === '/' || pathname === '/onboarding') {
    return null;
  }

  const segments = pathname.split('/').filter(Boolean);
  const breadcrumbs: BreadcrumbItem[] = [];

  let currentPath = '';
  for (const segment of segments) {
    currentPath += `/${segment}`;

    // Get label - use route labels or capitalize segment
    const label = routeLabels[segment] ||
      (segment.length < 36 ? segment.charAt(0).toUpperCase() + segment.slice(1) : 'Details');

    breadcrumbs.push({
      label,
      href: currentPath,
    });
  }

  return (
    <nav className="flex items-center gap-2 px-6 py-3 bg-neutral-900 border-b border-neutral-800">
      <Link
        href="/"
        className="text-neutral-500 hover:text-white transition-colors"
      >
        <Home className="w-4 h-4" />
      </Link>

      {breadcrumbs.map((crumb, index) => {
        const isLast = index === breadcrumbs.length - 1;

        return (
          <div key={crumb.href} className="flex items-center gap-2">
            <ChevronRight className="w-4 h-4 text-neutral-600" />
            {isLast ? (
              <span className="text-sm text-white font-medium">
                {crumb.label}
              </span>
            ) : (
              <Link
                href={crumb.href}
                className={cn(
                  'text-sm text-neutral-400 hover:text-white transition-colors'
                )}
              >
                {crumb.label}
              </Link>
            )}
          </div>
        );
      })}
    </nav>
  );
}
