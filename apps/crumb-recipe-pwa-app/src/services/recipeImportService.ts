import type { IngredientToken } from '../types/recipe';
import { ScalingEngine } from '../lib/scaling';

export interface ImportedRecipeData {
  title: string;
  author?: string;
  image?: string;
  sourceName?: string;
  sourceUrl: string;
  yield?: string;
  servings?: number;
  times?: { prep?: number; cook?: number; total?: number };
  ingredients: IngredientToken[];
  steps: string[];
  tips?: string[];
}

export class RecipeImportService {
  /**
   * Import recipe from a URL
   */
  static async importFromUrl(url: string): Promise<ImportedRecipeData> {
    try {
      // For demo purposes, since CORS will block most recipe sites,
      // we'll create a mock implementation that parses the URL
      // In a real app, you'd need a backend proxy or browser extension
      return this.createMockRecipeFromUrl(url);
    } catch (error) {
      console.error('Recipe import error:', error);
      throw error;
    }
  }

  /**
   * Create a mock recipe from URL for demo purposes
   */
  private static createMockRecipeFromUrl(url: string): ImportedRecipeData {
    // Extract site name from URL for demo
    let siteName = 'Unknown Site';
    try {
      const urlObj = new URL(url);
      siteName = urlObj.hostname.replace('www.', '');
    } catch (e) {
      // ignore
    }

    // Create a demo recipe based on the URL
    return {
      title: `Imported Recipe from ${siteName}`,
      author: 'Recipe Author',
      sourceName: siteName,
      sourceUrl: url,
      servings: 4,
      times: { prep: 15, cook: 30, total: 45 },
      ingredients: [
        ScalingEngine.parseIngredient('2 cups all-purpose flour'),
        ScalingEngine.parseIngredient('1 tsp salt'),
        ScalingEngine.parseIngredient('1/2 cup olive oil'),
        ScalingEngine.parseIngredient('1 large egg'),
        ScalingEngine.parseIngredient('3 cloves garlic, minced')
      ],
      steps: [
        'Preheat your oven to 375°F (190°C).',
        'In a large bowl, combine the flour and salt.',
        'Add olive oil and egg, mixing until a dough forms.',
        'Knead the dough on a floured surface for 5 minutes.',
        'Add minced garlic and knead for another 2 minutes.',
        'Place in a greased baking dish and bake for 30 minutes.',
        'Let cool for 5 minutes before serving.'
      ],
      tips: [
        'Make sure your oven is fully preheated before baking.',
        'You can substitute the olive oil with vegetable oil if preferred.'
      ]
    };
  }

  /**
   * Import recipe from a URL (real implementation for future use)
   */
  static async importFromUrlReal(_url: string): Promise<ImportedRecipeData> {
    try {
      // This would require a CORS proxy or backend service
      // For now, we'll throw an error suggesting alternatives
      throw new Error('Direct URL imports require a backend service due to CORS restrictions. Please copy and paste the recipe content instead.');
    } catch (error) {
      console.error('Recipe import error:', error);
      throw error;
    }
  }

  /*
   * The following methods would be used in a real implementation
   * but are commented out for the demo version:
   * - extractFromJsonLd
   * - extractFromMicrodata  
   * - extractFromReadability
   * - parseJsonLdRecipe
   * - parseDuration
   */
}