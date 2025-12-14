'use client';

import { Button } from '@/components/ui/button';

interface ConfirmationCardProps {
  prompt: string;
  onConfirm: () => void;
  onCancel: () => void;
  disabled?: boolean;
}

export function ConfirmationCard({ prompt, onConfirm, onCancel, disabled }: ConfirmationCardProps) {
  // Map prompts to appropriate button labels
  const getButtonLabels = (prompt: string): { confirm: string; cancel: string } => {
    const promptLower = prompt.toLowerCase();

    if (promptLower.includes('backtest')) {
      return { confirm: 'Run', cancel: 'Cancel' };
    }
    if (promptLower.includes('strategy') || promptLower.includes('create')) {
      return { confirm: 'Create', cancel: 'Cancel' };
    }
    if (promptLower.includes('fetch') || promptLower.includes('download')) {
      return { confirm: 'Fetch', cancel: 'Cancel' };
    }

    return { confirm: 'Yes', cancel: 'No' };
  };

  const labels = getButtonLabels(prompt);

  return (
    <div className="mx-4 my-2 p-3 rounded-md bg-neutral-800 border border-neutral-700">
      <p className="text-sm text-neutral-300 mb-2">{prompt}</p>
      <div className="flex gap-2">
        <Button
          onClick={onConfirm}
          disabled={disabled}
          size="sm"
          className="bg-green-600 hover:bg-green-700 text-white"
        >
          {labels.confirm}
        </Button>
        <Button
          onClick={onCancel}
          disabled={disabled}
          size="sm"
          variant="ghost"
          className="text-neutral-400 hover:text-neutral-200 hover:bg-neutral-700"
        >
          {labels.cancel}
        </Button>
      </div>
    </div>
  );
}
