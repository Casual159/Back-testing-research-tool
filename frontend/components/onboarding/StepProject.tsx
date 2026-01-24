'use client';

import { Sparkles } from 'lucide-react';

interface StepProjectProps {
  projectName: string;
  projectThesis: string;
  onProjectNameChange: (name: string) => void;
  onProjectThesisChange: (thesis: string) => void;
}

export function StepProject({
  projectName,
  projectThesis,
  onProjectNameChange,
  onProjectThesisChange,
}: StepProjectProps) {
  return (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 mb-4">
          <Sparkles className="w-8 h-8 text-white" />
        </div>
        <h2 className="text-2xl font-bold text-white">Create your first project</h2>
        <p className="text-neutral-400 max-w-md mx-auto">
          Projects help you organize your research. Each project can have its own strategies,
          backtests, and conclusions.
        </p>
      </div>

      <div className="max-w-lg mx-auto space-y-4">
        <div>
          <label htmlFor="projectName" className="block text-sm font-medium text-neutral-300 mb-1">
            Project Name
          </label>
          <input
            id="projectName"
            type="text"
            value={projectName}
            onChange={(e) => onProjectNameChange(e.target.value)}
            placeholder="e.g., RSI Mean Reversion Study"
            className="w-full px-4 py-3 bg-neutral-800 border border-neutral-700 rounded-lg text-white placeholder-neutral-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
          />
        </div>

        <div>
          <label htmlFor="projectThesis" className="block text-sm font-medium text-neutral-300 mb-1">
            Research Hypothesis <span className="text-neutral-500">(optional)</span>
          </label>
          <textarea
            id="projectThesis"
            value={projectThesis}
            onChange={(e) => onProjectThesisChange(e.target.value)}
            placeholder="e.g., RSI oversold conditions in ranging markets provide profitable mean reversion opportunities"
            rows={3}
            className="w-full px-4 py-3 bg-neutral-800 border border-neutral-700 rounded-lg text-white placeholder-neutral-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all resize-none"
          />
          <p className="mt-1 text-xs text-neutral-500">
            What trading idea do you want to research?
          </p>
        </div>
      </div>

      <div className="text-center">
        <p className="text-sm text-neutral-500">
          You can skip this step and create projects later
        </p>
      </div>
    </div>
  );
}
