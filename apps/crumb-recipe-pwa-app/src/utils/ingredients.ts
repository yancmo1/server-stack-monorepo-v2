import type { IngredientToken } from '../types';

/**
 * Parse ingredient lines into structured tokens
 * Uses regex patterns to extract amount, unit, ingredient, and notes
 */
export function parseIngredient(raw: string): IngredientToken {
  const cleaned = raw.trim();
  
  // Start with the raw text
  const token: IngredientToken = { raw: cleaned };
  
  // Pattern to match: [amount] [unit] [ingredient] [(note)]
  // Examples:
  // - "1 1/2 cups bread flour"
  // - "2 tablespoons olive oil (room temperature)"
  // - "1/4 teaspoon salt"
  // - "3-4 medium apples, diced"
  
  const pattern = /^(\d+(?:\s+\d+\/\d+|\.\d+|\/\d+)?(?:\s*-\s*\d+(?:\.\d+)?)?)\s*([a-zA-Z]+(?:\s+[a-zA-Z]+)?)?\s*(.+?)(?:\s*\(([^)]+)\))?$/;
  
  const match = cleaned.match(pattern);
  
  if (match) {
    const [, amountStr, unit, ingredient, note] = match;
    
    // Parse amount
    if (amountStr) {
      const amount = parseAmount(amountStr.trim());
      if (!isNaN(amount)) {
        token.amount = amount;
        token.amountDisplay = formatAmountDisplay(amountStr.trim());
      }
    }
    
    // Parse unit
    if (unit) {
      token.unit = normalizeUnit(unit.trim());
    }
    
    // Parse ingredient name
    if (ingredient) {
      token.item = ingredient.trim();
    }
    
    // Parse note
    if (note) {
      token.note = note.trim();
    }
  } else {
    // Fallback: try to extract just the amount at the beginning
    const simpleAmountMatch = cleaned.match(/^(\d+(?:\s+\d+\/\d+|\.\d+|\/\d+)?)/);
    if (simpleAmountMatch) {
      const amount = parseAmount(simpleAmountMatch[1]);
      if (!isNaN(amount)) {
        token.amount = amount;
        token.amountDisplay = formatAmountDisplay(simpleAmountMatch[1]);
        token.item = cleaned.replace(simpleAmountMatch[0], '').trim();
      }
    } else {
      // No amount found, treat entire string as ingredient
      token.item = cleaned;
    }
  }
  
  return token;
}

/**
 * Parse amount string to decimal number
 */
function parseAmount(amountStr: string): number {
  // Handle ranges like "2-3" or "1-2" - take the first number
  const rangeMatch = amountStr.match(/^(\d+(?:\.\d+)?)\s*-\s*\d+/);
  if (rangeMatch) {
    return parseFloat(rangeMatch[1]);
  }
  
  // Handle mixed numbers like "1 1/2"
  const mixedMatch = amountStr.match(/^(\d+)\s+(\d+)\/(\d+)$/);
  if (mixedMatch) {
    const whole = parseInt(mixedMatch[1]);
    const numerator = parseInt(mixedMatch[2]);
    const denominator = parseInt(mixedMatch[3]);
    return whole + (numerator / denominator);
  }
  
  // Handle fractions like "1/2"
  const fractionMatch = amountStr.match(/^(\d+)\/(\d+)$/);
  if (fractionMatch) {
    const numerator = parseInt(fractionMatch[1]);
    const denominator = parseInt(fractionMatch[2]);
    return numerator / denominator;
  }
  
  // Handle decimals and whole numbers
  return parseFloat(amountStr);
}

/**
 * Format amount for display (preserve original formatting when possible)
 */
function formatAmountDisplay(amountStr: string): string {
  // Preserve the original formatting for mixed numbers and fractions
  if (amountStr.includes('/') || amountStr.includes(' ')) {
    return amountStr;
  }
  
  // For decimals, show up to 2 decimal places
  const num = parseFloat(amountStr);
  if (num % 1 === 0) {
    return num.toString();
  } else {
    return num.toFixed(2).replace(/\.?0+$/, '');
  }
}

/**
 * Normalize unit names to standard forms
 */
function normalizeUnit(unit: string): string {
  const unitMap: Record<string, string> = {
    // Volume
    'cup': 'cup',
    'cups': 'cup',
    'c': 'cup',
    'tablespoon': 'tbsp',
    'tablespoons': 'tbsp',
    'tbsp': 'tbsp',
    'tbs': 'tbsp',
    'teaspoon': 'tsp',
    'teaspoons': 'tsp',
    'tsp': 'tsp',
    'fluid ounce': 'fl oz',
    'fluid ounces': 'fl oz',
    'fl oz': 'fl oz',
    'pint': 'pint',
    'pints': 'pint',
    'quart': 'quart',
    'quarts': 'quart',
    'gallon': 'gallon',
    'gallons': 'gallon',
    'liter': 'l',
    'liters': 'l',
    'l': 'l',
    'milliliter': 'ml',
    'milliliters': 'ml',
    'ml': 'ml',
    
    // Weight
    'pound': 'lb',
    'pounds': 'lb',
    'lb': 'lb',
    'lbs': 'lb',
    'ounce': 'oz',
    'ounces': 'oz',
    'oz': 'oz',
    'gram': 'g',
    'grams': 'g',
    'g': 'g',
    'kilogram': 'kg',
    'kilograms': 'kg',
    'kg': 'kg',
    
    // Length
    'inch': 'inch',
    'inches': 'inch',
    'in': 'inch',
    
    // Count
    'piece': 'piece',
    'pieces': 'piece',
    'slice': 'slice',
    'slices': 'slice',
    'clove': 'clove',
    'cloves': 'clove',
    'head': 'head',
    'heads': 'head',
    'bunch': 'bunch',
    'bunches': 'bunch',
    
    // Size modifiers
    'small': 'small',
    'medium': 'medium',
    'large': 'large',
    'extra large': 'extra large'
  };
  
  const normalized = unitMap[unit.toLowerCase()];
  return normalized || unit;
}

/**
 * Parse multiple ingredient lines
 */
export function parseIngredients(ingredientLines: string[]): IngredientToken[] {
  return ingredientLines
    .filter(line => line.trim().length > 0)
    .map(line => parseIngredient(line));
}

/**
 * Get common units for autocomplete/suggestions
 */
export function getCommonUnits(): string[] {
  return [
    'cup', 'tbsp', 'tsp', 'fl oz', 'pint', 'quart', 'gallon',
    'ml', 'l', 'lb', 'oz', 'g', 'kg', 'inch',
    'piece', 'slice', 'clove', 'head', 'bunch',
    'small', 'medium', 'large'
  ];
}