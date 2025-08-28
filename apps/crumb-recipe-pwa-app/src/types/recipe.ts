export type IngredientToken = {
  raw: string;
  amount?: number;
  amountDisplay?: string;
  unit?: string;
  item?: string;
  note?: string;
};

export type Recipe = {
  id: string;
  title: string;
  image?: string;
  author?: string;
  sourceName?: string;
  sourceUrl: string;
  yield?: string;
  servings?: number;
  times?: { prep?: number; cook?: number; total?: number };
  ingredients: IngredientToken[];
  steps: string[];
  tips?: string[];
  createdAt: number;
  updatedAt: number;
};

export type CookSession = {
  recipeId: string;
  checkedIngredients: Record<number, boolean>;
  checkedSteps: Record<number, boolean>;
  multiplier: number;
  expiresAt: number;
};