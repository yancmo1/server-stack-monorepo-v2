import React from 'react';
import { useRecipeStore } from '../stores/recipeStore';
import { ChefHat, Plus, Clock, Users } from 'lucide-react';
import type { Recipe } from '../types/recipe';

interface RecipeListProps {
  onRecipeSelect: (recipe: Recipe) => void;
  onStartCooking: (recipe: Recipe) => void;
}

export function RecipeList({ onRecipeSelect, onStartCooking }: RecipeListProps) {
  const { recipes, fetchRecipes, loading } = useRecipeStore();

  // Fetch recipes on component mount
  React.useEffect(() => {
    fetchRecipes();
  }, [fetchRecipes]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
      </div>
    );
  }

  if (recipes.length === 0) {
    return (
      <div className="text-center py-12">
        <ChefHat className="mx-auto h-12 w-12 text-gray-400 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No recipes yet</h3>
        <p className="text-gray-600 mb-6">Get started by adding your first recipe</p>
        <button className="inline-flex items-center px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors">
          <Plus className="w-4 h-4 mr-2" />
          Add Recipe
        </button>
      </div>
    );
  }

  return (
    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      {recipes.map((recipe) => (
        <div key={recipe.id} className="bg-white rounded-lg shadow-md overflow-hidden">
          {recipe.image && (
            <img 
              src={recipe.image} 
              alt={recipe.title}
              className="w-full h-48 object-cover"
            />
          )}
          <div className="p-4">
            <h3 className="font-bold text-lg mb-2 line-clamp-2">{recipe.title}</h3>
            {recipe.author && (
              <p className="text-sm text-gray-600 mb-2">by {recipe.author}</p>
            )}
            
            <div className="flex items-center gap-4 text-sm text-gray-500 mb-4">
              {recipe.times?.total && (
                <div className="flex items-center">
                  <Clock className="w-4 h-4 mr-1" />
                  {recipe.times.total}min
                </div>
              )}
              {recipe.servings && (
                <div className="flex items-center">
                  <Users className="w-4 h-4 mr-1" />
                  {recipe.servings} servings
                </div>
              )}
            </div>

            <div className="flex gap-2">
              <button 
                onClick={() => onRecipeSelect(recipe)}
                className="flex-1 px-3 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
              >
                View
              </button>
              <button 
                onClick={() => onStartCooking(recipe)}
                className="flex-1 px-3 py-2 bg-orange-500 text-white rounded-md hover:bg-orange-600 transition-colors"
              >
                Cook
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}