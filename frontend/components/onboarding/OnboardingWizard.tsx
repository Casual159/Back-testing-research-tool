'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, ArrowRight, Rocket, SkipForward } from 'lucide-react';
import { ProgressBar } from './ProgressBar';
import { StepExperience } from './StepExperience';
import { StepGoals } from './StepGoals';
import { StepProject } from './StepProject';
import { useOnboarding, UserPreferences } from '@/lib/contexts';
import { cn } from '@/lib/utils';

type ExperienceLevel = UserPreferences['experience_level'];

const TOTAL_STEPS = 3;

export function OnboardingWizard() {
  const router = useRouter();
  const { completeOnboarding, skipOnboarding } = useOnboarding();

  const [currentStep, setCurrentStep] = useState(0);
  const [experienceLevel, setExperienceLevel] = useState<ExperienceLevel | null>(null);
  const [goals, setGoals] = useState<string[]>([]);
  const [projectName, setProjectName] = useState('');
  const [projectThesis, setProjectThesis] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canProceed = () => {
    switch (currentStep) {
      case 0:
        return experienceLevel !== null;
      case 1:
        return goals.length > 0;
      case 2:
        return true; // Project creation is optional
      default:
        return false;
    }
  };

  const handleNext = () => {
    if (currentStep < TOTAL_STEPS - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleComplete = async () => {
    if (!experienceLevel) return;

    setIsSubmitting(true);
    setError(null);

    try {
      const preferences: UserPreferences = {
        experience_level: experienceLevel,
        goals,
      };

      const projectId = await completeOnboarding(
        preferences,
        projectName || undefined,
        projectThesis || undefined
      );

      // Navigate to project or home
      if (projectId) {
        router.push(`/projects/${projectId}`);
      } else {
        router.push('/projects');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSkip = () => {
    skipOnboarding();
    router.push('/');
  };

  return (
    <div className="min-h-screen bg-neutral-900 flex flex-col">
      {/* Header */}
      <header className="p-6">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <div className="w-40">
            {currentStep > 0 && (
              <button
                onClick={handleBack}
                className="flex items-center gap-2 text-neutral-400 hover:text-white transition-colors"
              >
                <ArrowLeft className="w-4 h-4" />
                Back
              </button>
            )}
          </div>

          <ProgressBar currentStep={currentStep} totalSteps={TOTAL_STEPS} />

          <div className="w-40 flex justify-end">
            <button
              onClick={handleSkip}
              className="flex items-center gap-2 text-neutral-500 hover:text-neutral-300 text-sm transition-colors"
            >
              Skip
              <SkipForward className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="flex-1 flex items-center justify-center p-6">
        <div className="w-full max-w-4xl">
          {/* Step content with animation */}
          <div className="transition-all duration-300">
            {currentStep === 0 && (
              <StepExperience value={experienceLevel} onChange={setExperienceLevel} />
            )}
            {currentStep === 1 && (
              <StepGoals value={goals} onChange={setGoals} />
            )}
            {currentStep === 2 && (
              <StepProject
                projectName={projectName}
                projectThesis={projectThesis}
                onProjectNameChange={setProjectName}
                onProjectThesisChange={setProjectThesis}
              />
            )}
          </div>

          {/* Error message */}
          {error && (
            <div className="mt-4 p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-center">
              {error}
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="p-6">
        <div className="max-w-3xl mx-auto flex justify-center">
          {currentStep < TOTAL_STEPS - 1 ? (
            <button
              onClick={handleNext}
              disabled={!canProceed()}
              className={cn(
                'flex items-center gap-2 px-8 py-3 rounded-lg font-medium transition-all duration-200',
                canProceed()
                  ? 'bg-purple-600 hover:bg-purple-500 text-white'
                  : 'bg-neutral-700 text-neutral-500 cursor-not-allowed'
              )}
            >
              Continue
              <ArrowRight className="w-4 h-4" />
            </button>
          ) : (
            <button
              onClick={handleComplete}
              disabled={isSubmitting}
              className={cn(
                'flex items-center gap-2 px-8 py-3 rounded-lg font-medium transition-all duration-200',
                'bg-gradient-to-r from-purple-600 to-blue-500 hover:from-purple-500 hover:to-blue-400 text-white',
                isSubmitting && 'opacity-50 cursor-wait'
              )}
            >
              {isSubmitting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Setting up...
                </>
              ) : (
                <>
                  <Rocket className="w-4 h-4" />
                  {projectName ? 'Create Project & Start' : 'Get Started'}
                </>
              )}
            </button>
          )}
        </div>
      </footer>
    </div>
  );
}
