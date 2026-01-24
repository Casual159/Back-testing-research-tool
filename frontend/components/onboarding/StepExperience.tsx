'use client';

import { GraduationCap, TrendingUp, LineChart, Building2 } from 'lucide-react';
import { cn } from '@/lib/utils';

type ExperienceLevel = 'beginner' | 'intermediate' | 'advanced' | 'professional';

interface StepExperienceProps {
  value: ExperienceLevel | null;
  onChange: (level: ExperienceLevel) => void;
}

const options: {
  value: ExperienceLevel;
  label: string;
  description: string;
  icon: React.ElementType;
}[] = [
  {
    value: 'beginner',
    label: 'Beginner',
    description: 'New to trading, want to learn the basics',
    icon: GraduationCap,
  },
  {
    value: 'intermediate',
    label: 'Intermediate',
    description: 'Know the basics, want to test strategies',
    icon: TrendingUp,
  },
  {
    value: 'advanced',
    label: 'Advanced',
    description: 'Actively trading, optimizing strategies',
    icon: LineChart,
  },
  {
    value: 'professional',
    label: 'Professional',
    description: 'Professional trader or quant researcher',
    icon: Building2,
  },
];

export function StepExperience({ value, onChange }: StepExperienceProps) {
  return (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <h2 className="text-2xl font-bold text-white">What&apos;s your trading experience?</h2>
        <p className="text-neutral-400">
          This helps us personalize your research experience
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl mx-auto">
        {options.map((option) => {
          const Icon = option.icon;
          const isSelected = value === option.value;

          return (
            <button
              key={option.value}
              onClick={() => onChange(option.value)}
              className={cn(
                'flex items-start gap-4 p-4 rounded-xl border-2 text-left transition-all duration-200',
                'hover:border-purple-500/50 hover:bg-neutral-800/50',
                isSelected
                  ? 'border-purple-500 bg-purple-500/10'
                  : 'border-neutral-700 bg-neutral-800/30'
              )}
            >
              <div
                className={cn(
                  'p-3 rounded-lg transition-colors',
                  isSelected ? 'bg-purple-500/20 text-purple-400' : 'bg-neutral-700 text-neutral-400'
                )}
              >
                <Icon className="w-6 h-6" />
              </div>
              <div>
                <div className={cn(
                  'font-semibold transition-colors',
                  isSelected ? 'text-white' : 'text-neutral-200'
                )}>
                  {option.label}
                </div>
                <div className="text-sm text-neutral-400">
                  {option.description}
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
