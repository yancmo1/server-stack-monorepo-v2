import { create } from 'zustand';
import type { CookSession } from '../types/recipe';
import { db } from '../lib/db';

interface CookSessionStore {
  currentSession: CookSession | null;
  loading: boolean;
  
  // Actions
  startCookSession: (recipeId: string) => Promise<void>;
  updateSession: (updates: Partial<CookSession>) => Promise<void>;
  toggleIngredient: (index: number) => Promise<void>;
  toggleStep: (index: number) => Promise<void>;
  updateMultiplier: (multiplier: number) => Promise<void>;
  endSession: () => Promise<void>;
  loadSession: (recipeId: string) => Promise<void>;
  cleanupExpiredSessions: () => Promise<void>;
}

export const useCookSessionStore = create<CookSessionStore>((set, get) => ({
  currentSession: null,
  loading: false,

  startCookSession: async (recipeId) => {
    set({ loading: true });
    try {
      // Check if session already exists
      const existingSession = await db.cookSessions.get(recipeId);
      
      if (existingSession && existingSession.expiresAt > Date.now()) {
        set({ currentSession: existingSession, loading: false });
        return;
      }

      // Create new session (expires in 24 hours)
      const session: CookSession = {
        recipeId,
        checkedIngredients: {},
        checkedSteps: {},
        multiplier: 1,
        expiresAt: Date.now() + 24 * 60 * 60 * 1000 // 24 hours
      };

      await db.cookSessions.put(session);
      set({ currentSession: session, loading: false });
    } catch (error) {
      console.error('Failed to start cook session:', error);
      set({ loading: false });
    }
  },

  updateSession: async (updates) => {
    const { currentSession } = get();
    if (!currentSession) return;

    const updatedSession = { ...currentSession, ...updates };
    try {
      await db.cookSessions.put(updatedSession);
      set({ currentSession: updatedSession });
    } catch (error) {
      console.error('Failed to update session:', error);
    }
  },

  toggleIngredient: async (index) => {
    const { currentSession } = get();
    if (!currentSession) return;

    const checkedIngredients = {
      ...currentSession.checkedIngredients,
      [index]: !currentSession.checkedIngredients[index]
    };

    await get().updateSession({ checkedIngredients });
  },

  toggleStep: async (index) => {
    const { currentSession } = get();
    if (!currentSession) return;

    const checkedSteps = {
      ...currentSession.checkedSteps,
      [index]: !currentSession.checkedSteps[index]
    };

    await get().updateSession({ checkedSteps });
  },

  updateMultiplier: async (multiplier) => {
    await get().updateSession({ multiplier });
  },

  endSession: async () => {
    const { currentSession } = get();
    if (!currentSession) return;

    try {
      await db.cookSessions.delete(currentSession.recipeId);
      set({ currentSession: null });
    } catch (error) {
      console.error('Failed to end session:', error);
    }
  },

  loadSession: async (recipeId) => {
    try {
      const session = await db.cookSessions.get(recipeId);
      if (session && session.expiresAt > Date.now()) {
        set({ currentSession: session });
      } else if (session) {
        // Session expired, clean it up
        await db.cookSessions.delete(recipeId);
      }
    } catch (error) {
      console.error('Failed to load session:', error);
    }
  },

  cleanupExpiredSessions: async () => {
    try {
      const now = Date.now();
      await db.cookSessions.where('expiresAt').below(now).delete();
    } catch (error) {
      console.error('Failed to cleanup expired sessions:', error);
    }
  }
}));