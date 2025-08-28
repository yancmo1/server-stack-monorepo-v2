// Canonical Recipe model
export type IngredientToken = {
  raw: string;         // original line, always keep
  amount?: number;     // 1.5
  amountDisplay?: string; // "1 1/2" (nice fraction)
  unit?: string;       // "cup", "g"
  item?: string;       // "bread flour"
  note?: string;       // "room temp"
};

export type Recipe = {
  id: string;          // nanoid
  title: string;
  image?: string;
  author?: string;
  sourceName?: string; // e.g., "The Clever Carrot"
  sourceUrl: string;
  yield?: string;      // e.g., "12 pancakes"
  servings?: number;   // numeric serving size if known
  times?: { prep?: number; cook?: number; total?: number }; // minutes
  ingredients: IngredientToken[];
  steps: string[];     // ordered steps
  tips?: string[];     // optional extra tips/notes
  createdAt: number;
  updatedAt: number;
};

// Ephemeral cook-session state (per-recipe)
export type CookSession = {
  recipeId: string;
  checkedIngredients: Record<number, boolean>; // index => checked
  checkedSteps: Record<number, boolean>;
  multiplier: number;  // e.g., 1.5 (default 1)
  expiresAt: number;   // epoch ms; default now + 72h
};

// API types
export type ImportRequest = {
  url: string;
};

export type ImportResponse = {
  success: boolean;
  recipe?: Recipe;
  error?: string;
};

// Scaling types
export type ScaledIngredient = IngredientToken & {
  scaledAmount?: number;
  scaledAmountDisplay?: string;
  gramsAmount?: number;
  gramsDisplay?: string;
};

// UI types
export type ToastType = 'success' | 'error' | 'info';

export type SessionStatus = 'active' | 'expiring' | 'expired';

// Storage types
export type ExportData = {
  recipes: Recipe[];
  exportedAt: number;
  version: string;
};

// Theme types
export type Theme = 'light' | 'dark' | 'system';

// Settings types
export type Settings = {
  theme: Theme;
  keepSessionsOnClose: boolean;
  autoExtendSessions: boolean;
};

// JSON-LD Schema.org types for parsing
export interface JsonLdRecipe {
  '@type': string | string[];
  name?: string;
  author?: string | { name?: string; '@type'?: string };
  image?: string | string[] | { url?: string };
  description?: string;
  recipeIngredient?: string[];
  recipeInstructions?: Array<string | { text?: string; name?: string }>;
  recipeYield?: string | number;
  totalTime?: string;
  prepTime?: string;
  cookTime?: string;
  nutrition?: {
    servingSize?: string;
  };
  aggregateRating?: {
    ratingValue?: number;
    reviewCount?: number;
  };
  review?: Array<{
    reviewBody?: string;
    author?: { name?: string };
  }>;
}