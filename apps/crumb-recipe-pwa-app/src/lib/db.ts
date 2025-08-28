import Dexie, { type Table } from 'dexie';
import type { Recipe, CookSession } from '../types/recipe';

class CrumbDB extends Dexie {
  recipes!: Table<Recipe, string>;
  cookSessions!: Table<CookSession, string>;

  constructor() {
    super('CrumbDB');
    
    this.version(1).stores({
      recipes: 'id, title, sourceName, sourceUrl, createdAt, updatedAt',
      cookSessions: 'recipeId, expiresAt'
    });
  }
}

export const db = new CrumbDB();