import Fraction from 'fraction.js';
import type { IngredientToken } from '../types/recipe';

// Common unit conversions (all to base units) - for future use
/*
const VOLUME_CONVERSIONS = {
  // to milliliters
  'ml': 1,
  'milliliter': 1,
  'milliliters': 1,
  'l': 1000,
  'liter': 1000,
  'liters': 1000,
  'tsp': 4.92892,
  'teaspoon': 4.92892,
  'teaspoons': 4.92892,
  'tbsp': 14.7868,
  'tablespoon': 14.7868,
  'tablespoons': 14.7868,
  'cup': 236.588,
  'cups': 236.588,
  'pint': 473.176,
  'pints': 473.176,
  'quart': 946.353,
  'quarts': 946.353,
  'gallon': 3785.41,
  'gallons': 3785.41,
  'fl oz': 29.5735,
  'fluid ounce': 29.5735,
  'fluid ounces': 29.5735
};

const WEIGHT_CONVERSIONS = {
  // to grams
  'g': 1,
  'gram': 1,
  'grams': 1,
  'kg': 1000,
  'kilogram': 1000,
  'kilograms': 1000,
  'oz': 28.3495,
  'ounce': 28.3495,
  'ounces': 28.3495,
  'lb': 453.592,
  'pound': 453.592,
  'pounds': 453.592
};
*/

export class ScalingEngine {
  /**
   * Scale a single ingredient based on the multiplier
   */
  static scaleIngredient(ingredient: IngredientToken, multiplier: number): IngredientToken {
    if (!ingredient.amount || multiplier === 1) {
      return ingredient;
    }

    try {
      const originalAmount = new Fraction(ingredient.amount);
      const scaledAmount = originalAmount.mul(multiplier);
      
      // Format the scaled amount nicely
      const amountDisplay = this.formatFraction(scaledAmount);
      
      return {
        ...ingredient,
        amount: scaledAmount.valueOf(),
        amountDisplay
      };
    } catch (error) {
      console.error('Error scaling ingredient:', error);
      return ingredient;
    }
  }

  /**
   * Scale all ingredients in a recipe
   */
  static scaleIngredients(ingredients: IngredientToken[], multiplier: number): IngredientToken[] {
    return ingredients.map(ingredient => this.scaleIngredient(ingredient, multiplier));
  }

  /**
   * Parse ingredient text to extract amount, unit, and item
   */
  static parseIngredient(raw: string): IngredientToken {
    const result: IngredientToken = { raw };
    
    // Pattern to match: amount unit item (note)
    const pattern = /^(\d+(?:[\.\,]\d+)?(?:\/\d+)?(?:\s+\d+\/\d+)?)\s*([a-zA-Z\s]*?)\s+(.+?)(?:\s*\(([^)]+)\))?$/;
    const match = raw.trim().match(pattern);
    
    if (match) {
      const [, amountStr, unitStr, itemStr, note] = match;
      
      try {
        // Parse fractional amounts (e.g., "1 1/2", "3/4", "2.5")
        const amount = this.parseFraction(amountStr.trim());
        result.amount = amount;
        result.amountDisplay = this.formatFraction(new Fraction(amount));
        
        const unit = unitStr.trim().toLowerCase();
        if (unit) {
          result.unit = unit;
        }
        
        result.item = itemStr.trim();
        
        if (note) {
          result.note = note.trim();
        }
      } catch (error) {
        console.error('Error parsing ingredient amount:', error);
      }
    } else {
      // If no amount pattern, assume it's just an item
      result.item = raw.trim();
    }
    
    return result;
  }

  /**
   * Parse fractional string (e.g., "1 1/2", "3/4", "2.5") to decimal
   */
  private static parseFraction(str: string): number {
    try {
      // Handle mixed fractions like "1 1/2"
      const mixedPattern = /^(\d+)\s+(\d+)\/(\d+)$/;
      const mixedMatch = str.match(mixedPattern);
      
      if (mixedMatch) {
        const [, whole, num, denom] = mixedMatch;
        return parseInt(whole) + parseInt(num) / parseInt(denom);
      }
      
      // Use Fraction.js to parse other formats
      return new Fraction(str).valueOf();
    } catch (error) {
      console.error('Error parsing fraction:', str, error);
      return 0;
    }
  }

  /**
   * Format a Fraction to a nice display string
   */
  private static formatFraction(fraction: Fraction): string {
    const decimal = fraction.valueOf();
    
    // For very small amounts, show decimal
    if (decimal < 0.125) {
      return decimal.toFixed(2).replace(/\.?0+$/, '');
    }
    
    // For clean decimals, show decimal
    if (decimal === Math.floor(decimal * 4) / 4) {
      const simplified = fraction.simplify();
      const numerator = Number(simplified.n);
      const denominator = Number(simplified.d);
      
      if (denominator === 1) {
        return numerator.toString();
      } else if (numerator > denominator) {
        // Mixed fraction
        const whole = Math.floor(numerator / denominator);
        const remainder = numerator % denominator;
        return `${whole} ${remainder}/${denominator}`;
      } else {
        return `${numerator}/${denominator}`;
      }
    }
    
    // Default to decimal
    return decimal.toFixed(2).replace(/\.?0+$/, '');
  }

  /**
   * Get suggested multipliers based on common scaling scenarios
   */
  static getSuggestedMultipliers(): Array<{ label: string; value: number }> {
    return [
      { label: '1/2x', value: 0.5 },
      { label: '1x', value: 1 },
      { label: '1.5x', value: 1.5 },
      { label: '2x', value: 2 },
      { label: '3x', value: 3 },
      { label: '4x', value: 4 }
    ];
  }
}