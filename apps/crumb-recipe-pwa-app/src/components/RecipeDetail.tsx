import { useState } from 'react';
import { useCookSessionStore } from '../stores/cookSessionStore';
import { ScalingEngine } from '../lib/scaling';
import { Clock, Users, ChefHat, Scale, ArrowLeft, Play } from 'lucide-react';
import type { Recipe } from '../types/recipe';

interface RecipeDetailProps {
  recipe: Recipe;
  onBack: () => void;
  onStartCooking: () => void;
}

export function RecipeDetail({ recipe, onBack, onStartCooking }: RecipeDetailProps) {
  const [multiplier, setMultiplier] = useState(1);
  const { startCookSession } = useCookSessionStore();
  
  const scaledIngredients = ScalingEngine.scaleIngredients(recipe.ingredients, multiplier);
  const suggestedMultipliers = ScalingEngine.getSuggestedMultipliers();

  const handleStartCooking = async () => {
    await startCookSession(recipe.id);
    onStartCooking();
  };

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={onBack}
          className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to recipes
        </button>
        
        <div className="bg-white rounded-lg shadow-sm overflow-hidden">
          {recipe.image && (
            <img 
              src={recipe.image} 
              alt={recipe.title}
              className="w-full h-64 object-cover"
            />
          )}
          
          <div className="p-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h1 className="text-3xl font-bold text-gray-900 mb-2">{recipe.title}</h1>
                {recipe.author && (
                  <p className="text-gray-600">by {recipe.author}</p>
                )}
                {recipe.sourceName && (
                  <p className="text-sm text-gray-500">from {recipe.sourceName}</p>
                )}
              </div>
              
              <button
                onClick={handleStartCooking}
                className="inline-flex items-center px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors"
              >
                <Play className="h-4 w-4 mr-2" />
                Start Cooking
              </button>
            </div>

            <div className="flex items-center gap-6 text-sm text-gray-500 mb-6">
              {recipe.times?.total && (
                <div className="flex items-center">
                  <Clock className="w-4 h-4 mr-1" />
                  {recipe.times.total}min total
                </div>
              )}
              {recipe.times?.prep && (
                <div className="flex items-center">
                  <Clock className="w-4 h-4 mr-1" />
                  {recipe.times.prep}min prep
                </div>
              )}
              {recipe.times?.cook && (
                <div className="flex items-center">
                  <Clock className="w-4 h-4 mr-1" />
                  {recipe.times.cook}min cook
                </div>
              )}
              {recipe.servings && (
                <div className="flex items-center">
                  <Users className="w-4 h-4 mr-1" />
                  {Math.round(recipe.servings * multiplier)} servings
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        {/* Ingredients */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900 flex items-center">
                <ChefHat className="h-5 w-5 mr-2" />
                Ingredients
              </h2>
              
              {/* Scaling Controls */}
              <div className="flex items-center space-x-2">
                <Scale className="h-4 w-4 text-gray-500" />
                <select
                  value={multiplier}
                  onChange={(e) => setMultiplier(Number(e.target.value))}
                  className="text-sm border border-gray-300 rounded-md px-2 py-1"
                >
                  {suggestedMultipliers.map(({ label, value }) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            
            <ul className="space-y-2">
              {scaledIngredients.map((ingredient, index) => (
                <li key={index} className="flex items-start">
                  <span className="inline-block w-2 h-2 bg-orange-500 rounded-full mt-2 mr-3 flex-shrink-0"></span>
                  <span className="text-gray-800">
                    {ingredient.amountDisplay && (
                      <span className="font-medium">{ingredient.amountDisplay} </span>
                    )}
                    {ingredient.unit && (
                      <span className="text-gray-600">{ingredient.unit} </span>
                    )}
                    <span>{ingredient.item}</span>
                    {ingredient.note && (
                      <span className="text-gray-500 text-sm"> ({ingredient.note})</span>
                    )}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Instructions */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Instructions</h2>
            
            <ol className="space-y-4">
              {recipe.steps.map((step, index) => (
                <li key={index} className="flex items-start">
                  <span className="inline-flex items-center justify-center w-6 h-6 bg-orange-500 text-white text-sm font-medium rounded-full mr-4 flex-shrink-0 mt-0.5">
                    {index + 1}
                  </span>
                  <p className="text-gray-800 leading-relaxed">{step}</p>
                </li>
              ))}
            </ol>
          </div>

          {/* Tips */}
          {recipe.tips && recipe.tips.length > 0 && (
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-6 mt-6">
              <h3 className="text-lg font-semibold text-orange-800 mb-3">Tips</h3>
              <ul className="space-y-2">
                {recipe.tips.map((tip, index) => (
                  <li key={index} className="flex items-start text-orange-700">
                    <span className="inline-block w-1.5 h-1.5 bg-orange-500 rounded-full mt-2 mr-3 flex-shrink-0"></span>
                    {tip}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}