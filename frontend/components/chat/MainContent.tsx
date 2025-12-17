'use client';

import { useChatContext } from './ChatProvider';
import { ReactNode } from 'react';

interface MainContentProps {
  children: ReactNode;
}

export function MainContent({ children }: MainContentProps) {
  const { isOpen } = useChatContext();

  return (
    <div
      className={`min-h-screen transition-all duration-300 ease-in-out ${
        isOpen ? 'sm:mr-[420px]' : ''
      }`}
    >
      {children}
    </div>
  );
}
