'use client';

import { ReactNode, useEffect, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { Sidebar } from './Sidebar';
import { Breadcrumbs } from './Breadcrumbs';
import { ChatProvider, ChatSidebar, ChatToggleButton, MainContent } from '@/components/chat';
import { OnboardingProvider, ProjectProvider, useOnboarding } from '@/lib/contexts';

const SIDEBAR_COLLAPSED_KEY = 'sidebar_collapsed';

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

export function Shell({ children }: { children: ReactNode }) {
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
