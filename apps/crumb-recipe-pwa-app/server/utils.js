// Improved ingredient parsing utility
function parseIngredients(ingredientLines) {
  return ingredientLines
    .filter(line => line.trim().length > 0)
    .map(line => parseIngredient(line));
}

function parseIngredient(raw) {
  const cleaned = raw.trim();
  const token = { raw: cleaned };
  
  // Common units to recognize
  const commonUnits = [
    // Volume
    'cup', 'cups', 'c',
    'tablespoon', 'tablespoons', 'tbsp', 'tbs', 'tb',
    'teaspoon', 'teaspoons', 'tsp', 'ts',
    'fluid ounce', 'fluid ounces', 'fl oz', 'fl. oz.',
    'pint', 'pints', 'pt',
    'quart', 'quarts', 'qt',
    'gallon', 'gallons', 'gal',
    'liter', 'liters', 'l',
    'milliliter', 'milliliters', 'ml',
    
    // Weight
    'pound', 'pounds', 'lb', 'lbs',
    'ounce', 'ounces', 'oz',
    'gram', 'grams', 'g',
    'kilogram', 'kilograms', 'kg',
    
    // Count/Other
    'piece', 'pieces', 'pc',
    'slice', 'slices',
    'clove', 'cloves',
    'head', 'heads',
    'bunch', 'bunches',
    'package', 'packages', 'pkg',
    'can', 'cans',
    'jar', 'jars',
    'bottle', 'bottles',
    'box', 'boxes',
    
    // Size descriptors that are often units
    'large', 'medium', 'small',
    'whole', 'half'
  ];
  
  // Create regex pattern that matches common units
  const unitPattern = commonUnits.map(u => u.replace(/\./g, '\\.')).join('|');
  
  // Enhanced pattern: [amount] [unit] [ingredient] [(note)]
  // More careful about unit boundaries
  const pattern = new RegExp(
    `^(\\d+(?:\\s+\\d+/\\d+|/\\d+|\\.\\d+)?(?:\\s*[-–]\\s*\\d+(?:\\.\\d+)?)?)`  + // amount
    `(?:\\s+(${unitPattern})s?\\b)?`  + // optional unit
    `\\s*(.+?)` + // ingredient (everything else)
    `(?:\\s*\\(([^)]+)\\))?$`,  // optional note in parentheses
    'i'
  );
  
  const match = cleaned.match(pattern);
  
  if (match) {
    const [, amountStr, unit, ingredient, note] = match;
    
    // Parse amount
    if (amountStr) {
      const amount = parseAmount(amountStr.trim());
      if (!isNaN(amount)) {
        token.amount = amount;
        token.amountDisplay = amountStr.trim();
      }
    }
    
    // Parse unit - clean it up
    if (unit) {
      token.unit = unit.trim().toLowerCase();
    }
    
    // Parse ingredient name - remove leading/trailing punctuation and spaces
    if (ingredient) {
      let cleanIngredient = ingredient.trim();
      // Remove leading commas, periods, etc.
      cleanIngredient = cleanIngredient.replace(/^[,.\s]+|[,.\s]+$/g, '');
      token.item = cleanIngredient;
    }
    
    // Parse note
    if (note) {
      token.note = note.trim();
    }
  } else {
    // Fallback: try to extract amount at the beginning
    const simpleAmountMatch = cleaned.match(/^(\d+(?:\s+\d+\/\d+|\.\d+|\/\d+)?(?:\s*[-–]\s*\d+(?:\.\d+)?)?)/);
    if (simpleAmountMatch) {
      const amount = parseAmount(simpleAmountMatch[1]);
      if (!isNaN(amount)) {
        token.amount = amount;
        token.amountDisplay = simpleAmountMatch[1];
        const remaining = cleaned.replace(simpleAmountMatch[0], '').trim();
        
        // Try to extract unit from the beginning of remaining text
        const remainingUnitMatch = remaining.match(new RegExp(`^(${unitPattern})s?\\b`, 'i'));
        if (remainingUnitMatch) {
          token.unit = remainingUnitMatch[1].toLowerCase();
          token.item = remaining.replace(remainingUnitMatch[0], '').trim();
        } else {
          token.item = remaining;
        }
      }
    } else {
      // No amount found, treat entire string as ingredient
      token.item = cleaned;
    }
  }
  
  // Clean up any remaining issues
  if (token.item) {
    // Remove extra whitespace and clean up
    token.item = token.item.replace(/\s+/g, ' ').trim();
    // Remove leading punctuation
    token.item = token.item.replace(/^[,.\-\s]+/, '');
  }
  
  return token;
}

function parseAmount(amountStr) {
  // Handle ranges like "2-3" or "1-2" - take the first number
  const rangeMatch = amountStr.match(/^(\d+(?:\.\d+)?)\s*[-–]\s*\d+/);
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
  
  // Handle fractions like "1/2" or "¾"
  const fractionMatch = amountStr.match(/^(\d+)\/(\d+)$/);
  if (fractionMatch) {
    const numerator = parseInt(fractionMatch[1]);
    const denominator = parseInt(fractionMatch[2]);
    return numerator / denominator;
  }
  
  // Handle unicode fractions
  const unicodeFractions = {
    '¼': 0.25, '½': 0.5, '¾': 0.75,
    '⅐': 1/7, '⅑': 1/9, '⅒': 0.1, '⅓': 1/3, '⅔': 2/3,
    '⅕': 0.2, '⅖': 0.4, '⅗': 0.6, '⅘': 0.8, '⅙': 1/6, '⅚': 5/6,
    '⅛': 0.125, '⅜': 0.375, '⅝': 0.625, '⅞': 0.875
  };
  
  for (const [unicode, value] of Object.entries(unicodeFractions)) {
    if (amountStr.includes(unicode)) {
      const remaining = amountStr.replace(unicode, '').trim();
      if (remaining) {
        const wholeNum = parseFloat(remaining);
        return isNaN(wholeNum) ? value : wholeNum + value;
      }
      return value;
    }
  }
  
  // Handle decimals and whole numbers
  return parseFloat(amountStr);
}

export { parseIngredients, parseIngredient };