'use client';

import { ReactNode, useEffect, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { useSession } from 'next-auth/react';
import { Sidebar } from './Sidebar';
import { Breadcrumbs } from './Breadcrumbs';
import { ChatProvider, ChatSidebar, ChatToggleButton, MainContent } from '@/components/chat';
import { AuthProvider, OnboardingProvider, ProjectProvider, useOnboarding } from '@/lib/contexts';

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

  // Authenticated: render with full shell
  return (
    <OnboardingProvider>
      <ProjectProvider>
        <OnboardingGuard>
          <ShellContent>{children}</ShellContent>
        </OnboardingGuard>
      </ProjectProvider>
    </OnboardingProvider>
  );
}

export function Shell({ children }: { children: ReactNode }) {
  return (
    <AuthProvider>
      <AuthGate>{children}</AuthGate>
    </AuthProvider>
  );
}
