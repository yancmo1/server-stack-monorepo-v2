import express from 'express';
import cors from 'cors';
import { fetch } from 'undici';
import * as cheerio from 'cheerio';
import { Readability } from '@mozilla/readability';
import { JSDOM } from 'jsdom';
import { nanoid } from 'nanoid';
import { parseIngredients } from './utils.js';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

// Serve static files from the built frontend
app.use(express.static(join(__dirname, '../dist')));

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Recipe import endpoint
app.post('/api/import', async (req, res) => {
  try {
    const { url } = req.body;
    
    if (!url) {
      return res.status(400).json({
        success: false,
        error: 'URL is required'
      });
    }
    
    console.log(`Importing recipe from: ${url}`);
    
    const recipe = await extractRecipe(url);
    
    res.json({
      success: true,
      recipe
    });
    
  } catch (error) {
    console.error('Import error:', error);
    res.status(500).json({
      success: false,
      error: error instanceof Error ? error.message : 'Failed to import recipe'
    });
  }
});

async function extractRecipe(url) {
  // Fetch the HTML
  const response = await fetch(url, {
    headers: {
      'User-Agent': 'Mozilla/5.0 (compatible; CrumbBot/1.0; +https://github.com/user/crumb)'
    }
  });
  
  if (!response.ok) {
    throw new Error(`Failed to fetch URL: ${response.status} ${response.statusText}`);
  }
  
  const html = await response.text();
  const $ = cheerio.load(html);
  
  // Strategy 1: Try JSON-LD Schema.org
  let recipe = await tryJsonLdExtraction($, url);
  
  // Strategy 2: Try microdata/RDFa
  if (!recipe) {
    recipe = tryMicrodataExtraction($, url);
  }
  
  // Strategy 3: Try print version
  if (!recipe) {
    recipe = await tryPrintVersion($, url);
  }
  
  // Strategy 4: Heuristic fallback with Readability
  if (!recipe) {
    recipe = await tryHeuristicExtraction(html, $, url);
  }
  
  if (!recipe) {
    throw new Error('Could not extract recipe from URL');
  }
  
  // Ensure we have required fields
  if (!recipe.title) {
    recipe.title = $('title').text() || 'Untitled Recipe';
  }
  
  return recipe;
}

async function tryJsonLdExtraction($, url) {
  const scripts = $('script[type="application/ld+json"]');
  
  for (let i = 0; i < scripts.length; i++) {
    try {
      const scriptContent = $(scripts[i]).html();
      if (!scriptContent) continue;
      
      const jsonLd = JSON.parse(scriptContent);
      const recipes = extractRecipesFromJsonLd(jsonLd);
      
      if (recipes.length > 0) {
        return convertJsonLdToRecipe(recipes[0], url);
      }
    } catch (error) {
      console.warn('Failed to parse JSON-LD:', error);
    }
  }
  
  return null;
}

function extractRecipesFromJsonLd(data) {
  const recipes = [];
  
  function findRecipes(obj) {
    if (!obj || typeof obj !== 'object') return;
    
    if (Array.isArray(obj)) {
      obj.forEach(findRecipes);
      return;
    }
    
    // Check if this object is a recipe
    const type = obj['@type'];
    if (type && (type === 'Recipe' || (Array.isArray(type) && type.includes('Recipe')))) {
      recipes.push(obj);
    }
    
    // Recursively search nested objects
    Object.values(obj).forEach(findRecipes);
  }
  
  findRecipes(data);
  return recipes;
}

function convertJsonLdToRecipe(jsonLd, sourceUrl) {
  const now = Date.now();
  
  // Extract basic info
  const title = jsonLd.name || 'Untitled Recipe';
  const author = typeof jsonLd.author === 'string' ? jsonLd.author : jsonLd.author?.name;
  const image = extractImageUrl(jsonLd.image);
  
  // Extract ingredients
  const ingredientLines = jsonLd.recipeIngredient || [];
  const ingredients = parseIngredients(ingredientLines);
  
  // Extract instructions with better parsing
  const instructions = jsonLd.recipeInstructions || [];
  const steps = instructions.map(instruction => {
    if (typeof instruction === 'string') {
      return instruction.trim();
    }
    if (instruction.text) {
      return instruction.text.trim();
    }
    if (instruction.name) {
      return instruction.name.trim();
    }
    // Handle HowToStep objects
    if (instruction['@type'] === 'HowToStep') {
      return instruction.text || instruction.name || '';
    }
    // Handle nested objects
    if (typeof instruction === 'object') {
      // Try common property names
      for (const prop of ['text', 'name', 'description', 'instructions']) {
        if (instruction[prop] && typeof instruction[prop] === 'string') {
          return instruction[prop].trim();
        }
      }
    }
    return '';
  }).filter(step => step.length > 0 && step.length > 10); // Filter out very short steps (likely headers)
  
  // Extract times
  const times = {};
  if (jsonLd.prepTime) times.prep = parseDuration(jsonLd.prepTime);
  if (jsonLd.cookTime) times.cook = parseDuration(jsonLd.cookTime);
  if (jsonLd.totalTime) times.total = parseDuration(jsonLd.totalTime);
  
  // Extract yield/servings
  const recipeYield = jsonLd.recipeYield;
  const yield_ = typeof recipeYield === 'string' ? recipeYield : recipeYield?.toString();
  const servings = typeof recipeYield === 'number' ? recipeYield : undefined;
  
  return {
    id: nanoid(),
    title,
    author,
    image,
    sourceUrl,
    sourceName: extractSourceName(sourceUrl),
    yield: yield_,
    servings,
    times: Object.keys(times).length > 0 ? times : undefined,
    ingredients,
    steps,
    createdAt: now,
    updatedAt: now
  };
}

function tryMicrodataExtraction($, url) {
  // Look for microdata recipe elements
  const recipeElements = $('[itemtype*="Recipe"]');
  
  if (recipeElements.length === 0) return null;
  
  const recipeEl = recipeElements.first();
  const now = Date.now();
  
  const title = recipeEl.find('[itemprop="name"]').first().text() || 'Untitled Recipe';
  const author = recipeEl.find('[itemprop="author"]').first().text();
  const image = recipeEl.find('[itemprop="image"]').first().attr('src');
  
  // Extract ingredients
  const ingredientElements = recipeEl.find('[itemprop="recipeIngredient"]');
  const ingredientLines = ingredientElements.map((_, el) => $(el).text()).get();
  const ingredients = parseIngredients(ingredientLines);
  
  // Extract instructions
  const instructionElements = recipeEl.find('[itemprop="recipeInstructions"]');
  const steps = instructionElements.map((_, el) => $(el).text()).get().filter(step => step.length > 0);
  
  return {
    id: nanoid(),
    title,
    author,
    image,
    sourceUrl: url,
    sourceName: extractSourceName(url),
    ingredients,
    steps,
    createdAt: now,
    updatedAt: now
  };
}

async function tryPrintVersion($, url) {
  // Look for print links
  const printLink = $('a[href*="print"], link[rel="print"]').first();
  if (printLink.length === 0) return null;
  
  const printUrl = printLink.attr('href');
  if (!printUrl) return null;
  
  try {
    const fullPrintUrl = new URL(printUrl, url).toString();
    return await extractRecipe(fullPrintUrl);
  } catch (error) {
    console.warn('Failed to extract from print version:', error);
    return null;
  }
}

async function tryHeuristicExtraction(html, $, url) {
  try {
    // Use Readability to get the main content
    const dom = new JSDOM(html);
    const reader = new Readability(dom.window.document);
    const article = reader.parse();
    
    if (!article) return null;
    
    const content$ = cheerio.load(article.content);
    const now = Date.now();
    
    // Extract title
    const title = article.title || $('h1').first().text() || 'Untitled Recipe';
    
    // Find ingredients section
    const ingredients = extractIngredientsByHeuristics(content$);
    
    // Find instructions section
    const steps = extractInstructionsByHeuristics(content$);
    
    // Find tips section
    const tips = extractTipsByHeuristics(content$);
    
    if (ingredients.length === 0 || steps.length === 0) {
      return null;
    }
    
    return {
      id: nanoid(),
      title,
      sourceUrl: url,
      sourceName: extractSourceName(url),
      ingredients: parseIngredients(ingredients),
      steps,
      tips: tips.length > 0 ? tips : undefined,
      createdAt: now,
      updatedAt: now
    };
  } catch (error) {
    console.warn('Heuristic extraction failed:', error);
    return null;
  }
}

function extractIngredientsByHeuristics($) {
  const ingredientHeaders = $('h1, h2, h3, h4').filter((_, el) => {
    const text = $(el).text().toLowerCase();
    return /ingredient|shopping|grocery/i.test(text);
  });
  
  if (ingredientHeaders.length === 0) return [];
  
  const ingredientSection = ingredientHeaders.first().nextUntil('h1, h2, h3, h4');
  const ingredients = [];
  
  ingredientSection.find('li').each((_, el) => {
    const text = $(el).text().trim();
    if (text) ingredients.push(text);
  });
  
  // If no list items found, try paragraphs
  if (ingredients.length === 0) {
    ingredientSection.find('p').each((_, el) => {
      const text = $(el).text().trim();
      if (text && text.length < 200) { // Reasonable length for ingredient
        ingredients.push(text);
      }
    });
  }
  
  return ingredients;
}

function extractInstructionsByHeuristics($) {
  const instructionHeaders = $('h1, h2, h3, h4').filter((_, el) => {
    const text = $(el).text().toLowerCase();
    return /instruction|method|direction|step|preparation|how to|recipe/i.test(text);
  });
  
  let steps = [];
  
  if (instructionHeaders.length > 0) {
    const instructionSection = instructionHeaders.first().nextUntil('h1, h2, h3, h4');
    
    // Try ordered lists first
    instructionSection.find('ol li').each((_, el) => {
      const text = $(el).text().trim();
      if (text && text.length > 10) {
        steps.push(text);
      }
    });
    
    // If no ordered list, try any list items
    if (steps.length === 0) {
      instructionSection.find('li').each((_, el) => {
        const text = $(el).text().trim();
        if (text && text.length > 10) {
          steps.push(text);
        }
      });
    }
    
    // If no lists, try paragraphs
    if (steps.length === 0) {
      instructionSection.find('p').each((_, el) => {
        const text = $(el).text().trim();
        if (text && text.length > 20) { // Longer text for instructions
          steps.push(text);
        }
      });
    }
  }
  
  // Fallback: Look for numbered steps anywhere in the document
  if (steps.length === 0) {
    $('p, div').each((_, el) => {
      const text = $(el).text().trim();
      // Look for text that starts with numbers and contains cooking-related words
      if (/^\d+\.?\s+/.test(text) && 
          /\b(mix|stir|add|bake|cook|heat|combine|whisk|fold|pour|place|remove)\b/i.test(text) &&
          text.length > 20) {
        steps.push(text);
      }
    });
  }
  
  // Fallback: Look for elements with step-like classes or ids
  if (steps.length === 0) {
    $('[class*="step"], [class*="instruction"], [id*="step"], [id*="instruction"]').each((_, el) => {
      const text = $(el).text().trim();
      if (text && text.length > 20) {
        steps.push(text);
      }
    });
  }
  
  return steps.slice(0, 20); // Limit to reasonable number of steps
}

function extractTipsByHeuristics($) {
  const tipHeaders = $('h1, h2, h3, h4').filter((_, el) => {
    const text = $(el).text().toLowerCase();
    return /tip|note|chef|pro|hint|advice/i.test(text);
  });
  
  if (tipHeaders.length === 0) return [];
  
  const tipSection = tipHeaders.first().nextUntil('h1, h2, h3, h4');
  const tips = [];
  
  tipSection.find('li, p').each((_, el) => {
    const text = $(el).text().trim();
    if (text) tips.push(text);
  });
  
  return tips;
}

function extractImageUrl(image) {
  if (typeof image === 'string') return image;
  if (Array.isArray(image)) return image[0];
  if (image && typeof image === 'object' && image.url) return image.url;
  return undefined;
}

function parseDuration(duration) {
  // Parse ISO 8601 durations (PT15M) or simple formats (15 minutes)
  const iso8601Match = duration.match(/PT(?:(\d+)H)?(?:(\d+)M)?/);
  if (iso8601Match) {
    const hours = parseInt(iso8601Match[1] || '0');
    const minutes = parseInt(iso8601Match[2] || '0');
    return hours * 60 + minutes;
  }
  
  // Try to extract minutes from text
  const minuteMatch = duration.match(/(\d+)\s*(?:minute|min)/i);
  if (minuteMatch) return parseInt(minuteMatch[1]);
  
  const hourMatch = duration.match(/(\d+)\s*(?:hour|hr)/i);
  if (hourMatch) return parseInt(hourMatch[1]) * 60;
  
  return 0;
}

function extractSourceName(url) {
  try {
    const domain = new URL(url).hostname;
    return domain.replace(/^www\./, '');
  } catch {
    return 'Unknown Source';
  }
}

// Serve the React app for all non-API routes (must be last!)
app.get('*', (req, res) => {
  res.sendFile(join(__dirname, '../dist/index.html'));
});

app.listen(PORT, () => {
  console.log(`Recipe import server running on port ${PORT}`);
});