'use client';

import { useSession } from 'next-auth/react';
import LandingPage from '@/components/landing/LandingPage';
import DashboardPage from '@/components/home/DashboardPage';

export default function HomePage() {
  const { status } = useSession();

  if (status === 'loading') {
    return (
      <div className="min-h-screen bg-neutral-900 flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-purple-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (status === 'unauthenticated') {
    return <LandingPage />;
  }

  return <DashboardPage />;
}
