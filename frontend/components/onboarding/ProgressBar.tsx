'use client';

import { cn } from '@/lib/utils';

interface ProgressBarProps {
  currentStep: number;
  totalSteps: number;
}

export function ProgressBar({ currentStep, totalSteps }: ProgressBarProps) {
  const progress = ((currentStep + 1) / totalSteps) * 100;

  return (
    <div className="w-full">
      <div className="flex justify-between mb-2">
        {Array.from({ length: totalSteps }, (_, i) => (
          <div
            key={i}
            className={cn(
              'flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium transition-all duration-300',
              i < currentStep && 'bg-purple-600 text-white',
              i === currentStep && 'bg-purple-500 text-white ring-4 ring-purple-500/30',
              i > currentStep && 'bg-neutral-700 text-neutral-400'
            )}
          >
            {i + 1}
          </div>
        ))}
      </div>
      <div className="h-1 bg-neutral-700 rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-purple-600 to-blue-500 transition-all duration-500 ease-out"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}
