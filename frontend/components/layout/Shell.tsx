'use client';

import { ReactNode, useEffect, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { useSession } from 'next-auth/react';
import { Sidebar } from './Sidebar';
import { Breadcrumbs } from './Breadcrumbs';
import { ChatProvider, ChatSidebar, ChatToggleButton, MainContent } from '@/components/chat';
import { AuthProvider, OnboardingProvider, ProjectProvider, useOnboarding } from '@/lib/contexts';
import { apiEndpoint } from '@/lib/config';

const SIDEBAR_COLLAPSED_KEY = 'sidebar_collapsed';

/** Routes that render without the app shell (no sidebar, no breadcrumbs) */
const PUBLIC_ROUTES = ['/', '/login', '/register'];

interface ShellContentProps {
  children: ReactNode;
}

function ShellContent({ children }: ShellContentProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const pathname = usePathname();

  // Sync sidebar collapsed state
  useEffect(() => {
    const handleStorageChange = () => {
      const stored = localStorage.getItem(SIDEBAR_COLLAPSED_KEY);
      setSidebarCollapsed(stored === 'true');
    };

    handleStorageChange();
    window.addEventListener('storage', handleStorageChange);

    // Also listen for custom events (for same-tab updates)
    const handleCustomChange = () => handleStorageChange();
    window.addEventListener('sidebar-toggle', handleCustomChange);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('sidebar-toggle', handleCustomChange);
    };
  }, []);

  // Determine left margin based on sidebar state
  const leftMargin = sidebarCollapsed ? 'ml-16' : 'ml-60';

  // Skip layout for onboarding page
  if (pathname === '/onboarding') {
    return <>{children}</>;
  }

  return (
    <ChatProvider>
      <Sidebar />
      <MainContent leftMargin={leftMargin}>
        <div className="min-h-screen bg-neutral-900">
          <Breadcrumbs />
          <main className="px-6 py-4">
            {children}
          </main>
        </div>
      </MainContent>
      <ChatSidebar />
      <ChatToggleButton />
    </ChatProvider>
  );
}

function OnboardingGuard({ children }: { children: ReactNode }) {
  const { isOnboardingComplete, isLoading } = useOnboarding();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    // Don't redirect while loading
    if (isLoading) return;

    // Don't redirect if already on onboarding page
    if (pathname === '/onboarding') return;

    // Redirect to onboarding if not complete
    if (!isOnboardingComplete) {
      router.push('/onboarding');
    }
  }, [isOnboardingComplete, isLoading, pathname, router]);

  // Show loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-neutral-900 flex items-center justify-center">
        <div className="animate-pulse">
          <div className="w-12 h-12 border-4 border-purple-500 border-t-transparent rounded-full animate-spin" />
        </div>
      </div>
    );
  }

  // If not complete and not on onboarding, show nothing while redirecting
  if (!isOnboardingComplete && pathname !== '/onboarding') {
    return null;
  }

  return <>{children}</>;
}

/**
 * AccountStatusGuard: checks if the user's account is active.
 * Pending users see an invite code entry screen.
 */
function AccountStatusGuard({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [inviteCode, setInviteCode] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetch(apiEndpoint('/auth/me'))
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        setStatus(data?.account_status || 'active');
      })
      .catch(() => setStatus('active')) // fail open
      .finally(() => setLoading(false));
  }, []);

  const handleRedeem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteCode.trim()) return;

    setSubmitting(true);
    setError('');

    try {
      const res = await fetch(apiEndpoint(`/invite/redeem?invite_code=${encodeURIComponent(inviteCode)}`), {
        method: 'POST',
      });
      const data = await res.json();

      if (!res.ok) {
        setError(data.detail || 'Failed to redeem invite code');
        setSubmitting(false);
        return;
      }

      setStatus('active');
    } catch {
      setError('Something went wrong');
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-neutral-900 flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-purple-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (status === 'suspended') {
    return (
      <div className="min-h-screen bg-neutral-900 flex items-center justify-center px-4">
        <div className="text-center max-w-md">
          <h1 className="text-2xl font-bold text-white mb-2">Account Suspended</h1>
          <p className="text-neutral-400">Your account has been suspended. Please contact the administrator.</p>
        </div>
      </div>
    );
  }

  if (status === 'pending') {
    return (
      <div className="min-h-screen bg-neutral-900 flex items-center justify-center px-4">
        <div className="w-full max-w-sm space-y-6">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-white mb-2">Account Pending</h1>
            <p className="text-neutral-400 text-sm">
              Enter an invite code to activate your account, or wait for administrator approval.
            </p>
          </div>

          <form onSubmit={handleRedeem} className="space-y-4">
            {error && (
              <div className="p-3 rounded-lg bg-red-900/30 border border-red-700 text-red-400 text-sm">
                {error}
              </div>
            )}

            <input
              type="text"
              value={inviteCode}
              onChange={(e) => setInviteCode(e.target.value)}
              placeholder="Enter invite code"
              className="w-full px-4 py-2.5 rounded-lg bg-neutral-800 border border-neutral-700 text-white placeholder-neutral-500 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500"
            />

            <button
              type="submit"
              disabled={submitting || !inviteCode.trim()}
              className="w-full px-4 py-2.5 rounded-lg bg-purple-600 text-white font-medium hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {submitting ? 'Activating...' : 'Activate Account'}
            </button>
          </form>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

/**
 * AuthGate: renders public pages without the shell,
 * authenticated pages with the full app shell.
 */
function AuthGate({ children }: { children: ReactNode }) {
  const { status } = useSession();
  const pathname = usePathname();

  const isPublicRoute = PUBLIC_ROUTES.includes(pathname);

  // Public routes: render children directly (no shell)
  // The page component itself decides what to show (e.g., landing vs dashboard)
  if (isPublicRoute && status !== 'authenticated') {
    return <>{children}</>;
  }

  // Loading state
  if (status === 'loading') {
    return (
      <div className="min-h-screen bg-neutral-900 flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-purple-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  // Authenticated: check account status, then render full shell
  return (
    <AccountStatusGuard>
      <OnboardingProvider>
        <ProjectProvider>
          <OnboardingGuard>
            <ShellContent>{children}</ShellContent>
          </OnboardingGuard>
        </ProjectProvider>
      </OnboardingProvider>
    </AccountStatusGuard>
  );
}

export function Shell({ children }: { children: ReactNode }) {
  return (
    <AuthProvider>
      <AuthGate>{children}</AuthGate>
    </AuthProvider>
  );
}
