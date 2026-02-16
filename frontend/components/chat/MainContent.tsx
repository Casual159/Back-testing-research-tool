'use client';

import { useChatContext } from './ChatProvider';
import { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface MainContentProps {
  children: ReactNode;
  leftMargin?: string;
}

export function MainContent({ children, leftMargin = '' }: MainContentProps) {
  const { isOpen, chatWidth } = useChatContext();

  return (
    <div
      className={cn(
        'min-h-screen transition-all duration-300 ease-in-out',
        leftMargin,
      )}
      style={isOpen ? { marginRight: `${chatWidth}px` } : undefined}
    >
      {children}
    </div>
  );
}
