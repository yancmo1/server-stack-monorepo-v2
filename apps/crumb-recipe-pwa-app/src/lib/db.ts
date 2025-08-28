import Dexie, { type EntityTable } from 'dexie';
import type { Recipe, CookSession } from '../types/recipe';

class CrumbDB extends Dexie {
  recipes!: EntityTable<Recipe, 'id'>;
  cookSessions!: EntityTable<CookSession, 'recipeId'>;

  constructor() {
    super('CrumbDB');
    
    this.version(1).stores({
      recipes: 'id, title, sourceName, sourceUrl, createdAt, updatedAt',
      cookSessions: 'recipeId, expiresAt'
    });
  }
}

export const db = new CrumbDB();