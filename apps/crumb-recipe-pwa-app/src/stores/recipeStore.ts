import { create } from 'zustand';
import type { Recipe } from '../types/recipe';
import { db } from '../lib/db';

interface RecipeStore {
  recipes: Recipe[];
  loading: boolean;
  error: string | null;
  
  // Actions
  fetchRecipes: () => Promise<void>;
  addRecipe: (recipe: Omit<Recipe, 'id' | 'createdAt' | 'updatedAt'>) => Promise<void>;
  updateRecipe: (id: string, updates: Partial<Recipe>) => Promise<void>;
  deleteRecipe: (id: string) => Promise<void>;
  importRecipeFromUrl: (url: string) => Promise<void>;
}

export const useRecipeStore = create<RecipeStore>((set, get) => ({
  recipes: [],
  loading: false,
  error: null,

  fetchRecipes: async () => {
    set({ loading: true, error: null });
    try {
      const recipes = await db.recipes.orderBy('updatedAt').reverse().toArray();
      set({ recipes, loading: false });
    } catch (error) {
      set({ error: 'Failed to fetch recipes', loading: false });
    }
  },

  addRecipe: async (recipeData) => {
    set({ loading: true, error: null });
    try {
      const now = Date.now();
      const recipe: Recipe = {
        ...recipeData,
        id: crypto.randomUUID(),
        createdAt: now,
        updatedAt: now
      };
      
      await db.recipes.add(recipe);
      const recipes = [...get().recipes, recipe];
      set({ recipes, loading: false });
    } catch (error) {
      set({ error: 'Failed to add recipe', loading: false });
    }
  },

  updateRecipe: async (id, updates) => {
    set({ loading: true, error: null });
    try {
      const updatedRecipe = { ...updates, updatedAt: Date.now() };
      await db.recipes.update(id, updatedRecipe);
      
      const recipes = get().recipes.map(recipe => 
        recipe.id === id ? { ...recipe, ...updatedRecipe } : recipe
      );
      set({ recipes, loading: false });
    } catch (error) {
      set({ error: 'Failed to update recipe', loading: false });
    }
  },

  deleteRecipe: async (id) => {
    set({ loading: true, error: null });
    try {
      await db.recipes.delete(id);
      await db.cookSessions.delete(id); // Also delete any cook sessions
      
      const recipes = get().recipes.filter(recipe => recipe.id !== id);
      set({ recipes, loading: false });
    } catch (error) {
      set({ error: 'Failed to delete recipe', loading: false });
    }
  },

  importRecipeFromUrl: async (_url) => {
    set({ loading: true, error: null });
    try {
      // This will be implemented with the recipe import service
      throw new Error('Recipe import not yet implemented');
    } catch (error) {
      set({ error: 'Failed to import recipe', loading: false });
    }
  }
}));