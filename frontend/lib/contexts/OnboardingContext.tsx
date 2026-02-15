'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiEndpoint } from '@/lib/config';

export interface UserPreferences {
  experience_level: 'beginner' | 'intermediate' | 'advanced' | 'professional';
  goals: string[];
  onboarding_completed_at?: string;
}

interface OnboardingContextType {
  isOnboardingComplete: boolean;
  isLoading: boolean;
  preferences: UserPreferences | null;
  currentStep: number;
  setCurrentStep: (step: number) => void;
  completeOnboarding: (prefs: UserPreferences, projectName?: string, projectThesis?: string) => Promise<string | null>;
  skipOnboarding: () => void;
  resetOnboarding: () => void;
}

const OnboardingContext = createContext<OnboardingContextType | undefined>(undefined);

const STORAGE_KEY = 'backtesting_onboarding';
const PREFERENCES_KEY = 'backtesting_preferences';

export function OnboardingProvider({ children }: { children: ReactNode }) {
  const [isOnboardingComplete, setIsOnboardingComplete] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [preferences, setPreferences] = useState<UserPreferences | null>(null);
  const [currentStep, setCurrentStep] = useState(0);

  // Load state from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    const storedPrefs = localStorage.getItem(PREFERENCES_KEY);

    if (stored === 'complete') {
      setIsOnboardingComplete(true);
    }

    if (storedPrefs) {
      try {
        setPreferences(JSON.parse(storedPrefs));
      } catch (e) {
        console.error('Failed to parse stored preferences:', e);
      }
    }

    setIsLoading(false);
  }, []);

  const completeOnboarding = async (
    prefs: UserPreferences,
    projectName?: string,
    projectThesis?: string
  ): Promise<string | null> => {
    try {
      // Save to backend if creating first project
      if (projectName) {
        const response = await fetch(apiEndpoint('/onboarding/preferences'), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            experience_level: prefs.experience_level,
            goals: prefs.goals,
            first_project_name: projectName,
            first_project_thesis: projectThesis
          })
        });

        if (!response.ok) {
          throw new Error('Failed to save onboarding preferences');
        }

        const data = await response.json();

        // Update local state
        const fullPrefs = {
          ...prefs,
          onboarding_completed_at: new Date().toISOString()
        };

        setPreferences(fullPrefs);
        setIsOnboardingComplete(true);

        // Save to localStorage
        localStorage.setItem(STORAGE_KEY, 'complete');
        localStorage.setItem(PREFERENCES_KEY, JSON.stringify(fullPrefs));

        return data.project_id;
      }

      // Just save preferences locally if no project
      const fullPrefs = {
        ...prefs,
        onboarding_completed_at: new Date().toISOString()
      };

      setPreferences(fullPrefs);
      setIsOnboardingComplete(true);

      localStorage.setItem(STORAGE_KEY, 'complete');
      localStorage.setItem(PREFERENCES_KEY, JSON.stringify(fullPrefs));

      return null;
    } catch (error) {
      console.error('Failed to complete onboarding:', error);
      throw error;
    }
  };

  const skipOnboarding = () => {
    setIsOnboardingComplete(true);
    localStorage.setItem(STORAGE_KEY, 'complete');
  };

  const resetOnboarding = () => {
    setIsOnboardingComplete(false);
    setPreferences(null);
    setCurrentStep(0);
    localStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem(PREFERENCES_KEY);
  };

  return (
    <OnboardingContext.Provider
      value={{
        isOnboardingComplete,
        isLoading,
        preferences,
        currentStep,
        setCurrentStep,
        completeOnboarding,
        skipOnboarding,
        resetOnboarding
      }}
    >
      {children}
    </OnboardingContext.Provider>
  );
}

export function useOnboarding() {
  const context = useContext(OnboardingContext);
  if (context === undefined) {
    throw new Error('useOnboarding must be used within an OnboardingProvider');
  }
  return context;
}
