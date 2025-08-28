import Fraction from 'fraction.js';
import type { IngredientToken, ScaledIngredient } from '../types';
import { convertToGrams, type ConversionResult } from './conversions';

/**
 * Scale ingredient amounts by a multiplier and return clean fraction display
 */
export function scaleIngredient(ingredient: IngredientToken, multiplier: number, showGrams = false): ScaledIngredient {
  const scaled: ScaledIngredient = { ...ingredient };
  
  if (ingredient.amount && multiplier !== 1) {
    const scaledAmount = ingredient.amount * multiplier;
    scaled.scaledAmount = scaledAmount;
    scaled.scaledAmountDisplay = formatFraction(scaledAmount);
  }
  
  // Add gram conversion if requested
  if (showGrams) {
    const baseConversion = convertToGrams(ingredient);
    if (baseConversion.isConvertible) {
      const scaledGrams = Math.round(baseConversion.grams * multiplier);
      scaled.gramsDisplay = `${scaledGrams}g`;
      scaled.gramsAmount = scaledGrams;
    }
  }
  
  return scaled;
}

/**
 * Scale all ingredients in a recipe
 */
export function scaleIngredients(ingredients: IngredientToken[], multiplier: number, showGrams = false): ScaledIngredient[] {
  return ingredients.map(ingredient => scaleIngredient(ingredient, multiplier, showGrams));
}

/**
 * Format a decimal number as a nice fraction for display
 */
export function formatFraction(amount: number): string {
  try {
    const fraction = new Fraction(amount);
    
    // For very small amounts or exact decimals, show decimal
    if (amount < 0.125 || (amount % 1 === 0 && amount <= 20)) {
      return amount.toString();
    }
    
    // Convert to mixed number for display
    const whole = Math.floor(fraction.valueOf());
    const remaining = fraction.sub(whole);
    
    if (whole === 0) {
      return fraction.toFraction();
    } else if (remaining.valueOf() === 0) {
      return whole.toString();
    } else {
      return `${whole} ${remaining.toFraction()}`;
    }
  } catch (error) {
    // Fallback to decimal
    return amount.toString();
  }
}

/**
 * Parse common fraction strings to decimal
 */
export function parseFraction(fractionStr: string): number {
  try {
    // Handle mixed numbers like "1 1/2"
    const mixedMatch = fractionStr.match(/^(\d+)\s+(\d+)\/(\d+)$/);
    if (mixedMatch) {
      const whole = parseInt(mixedMatch[1]);
      const numerator = parseInt(mixedMatch[2]);
      const denominator = parseInt(mixedMatch[3]);
      return whole + (numerator / denominator);
    }
    
    // Handle simple fractions like "1/2"
    const fractionMatch = fractionStr.match(/^(\d+)\/(\d+)$/);
    if (fractionMatch) {
      const numerator = parseInt(fractionMatch[1]);
      const denominator = parseInt(fractionMatch[2]);
      return numerator / denominator;
    }
    
    // Handle decimals and whole numbers
    const decimal = parseFloat(fractionStr);
    if (!isNaN(decimal)) {
      return decimal;
    }
    
    // Use Fraction.js as fallback
    return new Fraction(fractionStr).valueOf();
  } catch (error) {
    return NaN;
  }
}

/**
 * Get display value for an ingredient (scaled or original)
 */
export function getIngredientDisplayAmount(ingredient: ScaledIngredient, preferGrams = false): string {
  // If grams are requested and available, use them
  if (preferGrams && ingredient.gramsDisplay) {
    return ingredient.gramsDisplay;
  }
  
  if (ingredient.scaledAmountDisplay) {
    return ingredient.scaledAmountDisplay;
  }
  
  if (ingredient.amountDisplay) {
    return ingredient.amountDisplay;
  }
  
  if (ingredient.amount !== undefined) {
    return formatFraction(ingredient.amount);
  }
  
  return '';
}

/**
 * Create nice multiplier options for UI
 */
export function getMultiplierOptions(): Array<{ value: number; label: string }> {
  return [
    { value: 0.25, label: '¼×' },
    { value: 0.5, label: '½×' },
    { value: 0.75, label: '¾×' },
    { value: 1, label: '1×' },
    { value: 1.25, label: '1¼×' },
    { value: 1.5, label: '1½×' },
    { value: 1.75, label: '1¾×' },
    { value: 2, label: '2×' },
    { value: 2.5, label: '2½×' },
    { value: 3, label: '3×' },
  ];
}

/**
 * Snap a multiplier to common fractions if close enough
 */
export function snapMultiplier(value: number): number {
  const commonFractions = [0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.5, 3];
  const tolerance = 0.05;
  
  for (const fraction of commonFractions) {
    if (Math.abs(value - fraction) <= tolerance) {
      return fraction;
    }
  }
  
  return value;
}