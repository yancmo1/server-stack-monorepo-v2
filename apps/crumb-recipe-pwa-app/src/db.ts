import Dexie, { Table } from 'dexie';
import type { Recipe, CookSession } from './types';

export class CrumbDB extends Dexie {
  recipes!: Table<Recipe>;
  sessions!: Table<CookSession>;

  constructor() {
    super('CrumbDB');
    
    this.version(1).stores({
      recipes: 'id, title, sourceName, sourceUrl, createdAt, updatedAt',
      sessions: 'recipeId, expiresAt'
    });
  }

  async cleanupExpiredSessions() {
    const now = Date.now();
    await this.sessions.where('expiresAt').below(now).delete();
  }

  async getActiveSession(recipeId: string): Promise<CookSession | undefined> {
    const session = await this.sessions.get(recipeId);
    if (!session) return undefined;
    
    if (session.expiresAt < Date.now()) {
      await this.sessions.delete(recipeId);
      return undefined;
    }
    
    return session;
  }

  async createSession(recipeId: string, durationHours = 72): Promise<CookSession> {
    const session: CookSession = {
      recipeId,
      checkedIngredients: {},
      checkedSteps: {},
      multiplier: 1,
      expiresAt: Date.now() + (durationHours * 60 * 60 * 1000)
    };
    
    await this.sessions.put(session);
    return session;
  }

  async updateSession(session: CookSession): Promise<void> {
    await this.sessions.put(session);
  }

  async extendSession(recipeId: string, additionalHours = 48): Promise<void> {
    const session = await this.getActiveSession(recipeId);
    if (session) {
      session.expiresAt = Math.max(
        session.expiresAt,
        Date.now()
      ) + (additionalHours * 60 * 60 * 1000);
      await this.sessions.put(session);
    }
  }

  async deleteSession(recipeId: string): Promise<void> {
    await this.sessions.delete(recipeId);
  }

  async searchRecipes(query: string): Promise<Recipe[]> {
    const lowerQuery = query.toLowerCase();
    return this.recipes
      .filter((recipe: Recipe) => 
        recipe.title.toLowerCase().includes(lowerQuery) ||
        recipe.sourceName?.toLowerCase().includes(lowerQuery) ||
        recipe.ingredients.some((ing: any) => 
          ing.raw.toLowerCase().includes(lowerQuery) ||
          ing.item?.toLowerCase().includes(lowerQuery)
        )
      )
      .toArray();
  }

  async getRecentRecipes(limit = 10): Promise<Recipe[]> {
    return this.recipes
      .orderBy('updatedAt')
      .reverse()
      .limit(limit)
      .toArray();
  }

  async exportData() {
    const recipes = await this.recipes.toArray();
    return {
      recipes,
      exportedAt: Date.now(),
      version: '1.0.0'
    };
  }

  async importData(data: { recipes: Recipe[] }) {
    for (const recipe of data.recipes) {
      await this.recipes.put(recipe);
    }
  }
}

// Create singleton instance
export const db = new CrumbDB();