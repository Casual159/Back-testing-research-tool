'use client';

import { BookOpen, Lightbulb, Settings2, GraduationCap, Bot, Check } from 'lucide-react';
import { cn } from '@/lib/utils';

interface StepGoalsProps {
  value: string[];
  onChange: (goals: string[]) => void;
}

const goals = [
  {
    id: 'learn',
    label: 'Learn about trading',
    description: 'Understand how strategies work',
    icon: BookOpen,
  },
  {
    id: 'test_ideas',
    label: 'Test my ideas',
    description: 'Validate trading hypotheses',
    icon: Lightbulb,
  },
  {
    id: 'optimize',
    label: 'Optimize strategies',
    description: 'Improve existing approaches',
    icon: Settings2,
  },
  {
    id: 'research',
    label: 'Academic research',
    description: 'Quantitative analysis',
    icon: GraduationCap,
  },
  {
    id: 'automation',
    label: 'Build trading bots',
    description: 'Automate strategies',
    icon: Bot,
  },
];

export function StepGoals({ value, onChange }: StepGoalsProps) {
  const toggleGoal = (goalId: string) => {
    if (value.includes(goalId)) {
      onChange(value.filter((g) => g !== goalId));
    } else {
      onChange([...value, goalId]);
    }
  };

  return (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <h2 className="text-2xl font-bold text-white">What do you want to achieve?</h2>
        <p className="text-neutral-400">
          Select all that apply - you can change this later
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 max-w-3xl mx-auto">
        {goals.map((goal) => {
          const Icon = goal.icon;
          const isSelected = value.includes(goal.id);

          return (
            <button
              key={goal.id}
              onClick={() => toggleGoal(goal.id)}
              className={cn(
                'relative flex flex-col items-center gap-2 p-4 rounded-xl border-2 text-center transition-all duration-200',
                'hover:border-purple-500/50 hover:bg-neutral-800/50',
                isSelected
                  ? 'border-purple-500 bg-purple-500/10'
                  : 'border-neutral-700 bg-neutral-800/30'
              )}
            >
              {isSelected && (
                <div className="absolute top-2 right-2">
                  <Check className="w-5 h-5 text-purple-400" />
                </div>
              )}
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
                  {goal.label}
                </div>
                <div className="text-xs text-neutral-400">
                  {goal.description}
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {value.length === 0 && (
        <p className="text-center text-sm text-neutral-500">
          Select at least one goal to continue
        </p>
      )}
    </div>
  );
}
