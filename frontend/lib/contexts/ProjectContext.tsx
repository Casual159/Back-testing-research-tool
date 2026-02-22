'use client';

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';

import { config } from '@/lib/config';

const API_BASE_URL = config.apiUrl;

export interface NotebookBlock {
  id: string;
  type: 'text' | 'backtest_ref' | 'strategy_ref' | 'agent_note';
  content: string;
  created_at: string;
  metadata?: Record<string, unknown>;
}

export interface Project {
  id: string;
  name: string;
  description: string | null;
  thesis: string | null;
  status: 'active' | 'paused' | 'concluded';
  validation_result: 'validated' | 'invalidated' | 'inconclusive' | null;
  notebook?: NotebookBlock[];
  conversation_count: number;
  backtest_count: number;
  created_at: string;
  updated_at: string;
}

export interface ResearchEvent {
  id: string;
  event_type: 'strategy_created' | 'backtest_run' | 'conclusion' | 'note' | 'milestone';
  title: string;
  summary: string | null;
  reference_type: 'conversation' | 'backtest_report' | 'strategy' | null;
  reference_id: string | null;
  data: Record<string, unknown>;
  created_at: string;
}

export interface CreateProjectData {
  name: string;
  description?: string;
  thesis?: string;
}

export interface CreateEventData {
  event_type: ResearchEvent['event_type'];
  title: string;
  summary?: string;
  reference_type?: ResearchEvent['reference_type'];
  reference_id?: string;
  data?: Record<string, unknown>;
}

interface ProjectContextType {
  // Project state
  currentProject: Project | null;
  projects: Project[];
  isLoading: boolean;
  error: string | null;

  // Project actions
  selectProject: (id: string | null) => void;
  createProject: (data: CreateProjectData) => Promise<Project>;
  updateProject: (id: string, data: Partial<CreateProjectData & { status: string; validation_result: string; notebook: NotebookBlock[] }>) => Promise<void>;
  deleteProject: (id: string) => Promise<void>;
  refreshProjects: () => Promise<void>;

  // Events (timeline)
  events: ResearchEvent[];
  eventsLoading: boolean;
  createEvent: (data: CreateEventData) => Promise<void>;
  refreshEvents: () => Promise<void>;
}

const ProjectContext = createContext<ProjectContextType | undefined>(undefined);

const CURRENT_PROJECT_KEY = 'backtesting_current_project';

export function ProjectProvider({ children }: { children: ReactNode }) {
  const [currentProject, setCurrentProject] = useState<Project | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [events, setEvents] = useState<ResearchEvent[]>([]);
  const [eventsLoading, setEventsLoading] = useState(false);

  // Fetch all projects (no dependencies to avoid loops)
  const refreshProjects = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch(`${API_BASE_URL}/projects`);
      if (!response.ok) {
        throw new Error('Failed to fetch projects');
      }

      const data = await response.json();
      setProjects(data);
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      console.error('Failed to fetch projects:', err);
      return [];
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Initial load + restore current project from localStorage
  useEffect(() => {
    const init = async () => {
      const data = await refreshProjects();
      const storedProjectId = localStorage.getItem(CURRENT_PROJECT_KEY);
      if (storedProjectId && data.length > 0) {
        const project = data.find((p: Project) => p.id === storedProjectId);
        if (project) {
          setCurrentProject(project);
        }
      }
    };
    init();
  }, [refreshProjects]);

  // Fetch events for current project (internal with projectId)
  const fetchEvents = useCallback(async (projectId: string) => {
    try {
      setEventsLoading(true);
      const response = await fetch(`${API_BASE_URL}/projects/${projectId}/events`);
      if (!response.ok) {
        throw new Error('Failed to fetch events');
      }

      const data = await response.json();
      setEvents(data);
    } catch (err) {
      console.error('Failed to fetch events:', err);
    } finally {
      setEventsLoading(false);
    }
  }, []);

  // Public refreshEvents uses current project
  const refreshEvents = useCallback(async () => {
    if (currentProject?.id) {
      await fetchEvents(currentProject.id);
    }
  }, [currentProject?.id, fetchEvents]);

  // Load events when project changes
  useEffect(() => {
    if (currentProject) {
      fetchEvents(currentProject.id);
    } else {
      setEvents([]);
    }
  }, [currentProject?.id, fetchEvents]);

  const selectProject = (id: string | null) => {
    if (id === null) {
      setCurrentProject(null);
      localStorage.removeItem(CURRENT_PROJECT_KEY);
      return;
    }

    const project = projects.find(p => p.id === id);
    if (project) {
      setCurrentProject(project);
      localStorage.setItem(CURRENT_PROJECT_KEY, id);
    }
  };

  const createProject = async (data: CreateProjectData): Promise<Project> => {
    const response = await fetch(`${API_BASE_URL}/projects`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create project');
    }

    const result = await response.json();

    // Refresh projects list
    await refreshProjects();

    // Find and return the new project
    const newProject = projects.find(p => p.id === result.project.id);
    if (newProject) {
      setCurrentProject(newProject);
      localStorage.setItem(CURRENT_PROJECT_KEY, newProject.id);
      return newProject;
    }

    // If not found in list yet, fetch it directly
    const projectResponse = await fetch(`${API_BASE_URL}/projects/${result.project.id}`);
    const project = await projectResponse.json();
    setCurrentProject(project);
    localStorage.setItem(CURRENT_PROJECT_KEY, project.id);

    // Refresh to update list
    await refreshProjects();

    return project;
  };

  const updateProject = async (
    id: string,
    data: Partial<CreateProjectData & { status: string; validation_result: string; notebook: NotebookBlock[] }>
  ): Promise<void> => {
    const response = await fetch(`${API_BASE_URL}/projects/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update project');
    }

    await refreshProjects();

    // Update current project if it's the one being updated
    if (currentProject?.id === id) {
      const projectResponse = await fetch(`${API_BASE_URL}/projects/${id}`);
      const project = await projectResponse.json();
      setCurrentProject(project);
    }
  };

  const deleteProject = async (id: string): Promise<void> => {
    const response = await fetch(`${API_BASE_URL}/projects/${id}`, {
      method: 'DELETE'
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete project');
    }

    // Clear current project if it's the one being deleted
    if (currentProject?.id === id) {
      setCurrentProject(null);
      localStorage.removeItem(CURRENT_PROJECT_KEY);
    }

    await refreshProjects();
  };

  const createEvent = async (data: CreateEventData): Promise<void> => {
    if (!currentProject) {
      throw new Error('No project selected');
    }

    const response = await fetch(`${API_BASE_URL}/projects/${currentProject.id}/events`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create event');
    }

    await refreshEvents();
  };

  return (
    <ProjectContext.Provider
      value={{
        currentProject,
        projects,
        isLoading,
        error,
        selectProject,
        createProject,
        updateProject,
        deleteProject,
        refreshProjects,
        events,
        eventsLoading,
        createEvent,
        refreshEvents
      }}
    >
      {children}
    </ProjectContext.Provider>
  );
}

export function useProject() {
  const context = useContext(ProjectContext);
  if (context === undefined) {
    throw new Error('useProject must be used within a ProjectProvider');
  }
  return context;
}
