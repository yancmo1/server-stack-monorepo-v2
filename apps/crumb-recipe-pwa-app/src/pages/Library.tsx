import { useState, useEffect } from 'react';
import { useRecipeStore } from '../state/session';
import { Link } from 'react-router-dom';
import { Plus, Search, ChefHat, Trash2 } from 'lucide-react';
import { toast } from 'sonner';

export default function Library() {
  const { recipes, searchQuery, searchRecipes, getFilteredRecipes, isLoading, deleteRecipe } = useRecipeStore();
  const [localQuery, setLocalQuery] = useState(searchQuery);

  const filteredRecipes = getFilteredRecipes();

  const handleSearch = (query: string) => {
    setLocalQuery(query);
    searchRecipes(query);
  };

  const handleDelete = async (e: React.MouseEvent, recipeId: string, recipeTitle: string) => {
    e.preventDefault(); // Prevent navigation to recipe detail
    e.stopPropagation();
    
    if (confirm(`Are you sure you want to delete "${recipeTitle}"? This action cannot be undone.`)) {
      try {
        await deleteRecipe(recipeId);
        toast.success('Recipe deleted successfully');
      } catch (error) {
        toast.error('Failed to delete recipe');
      }
    }
  };

  return (
    <div className="min-h-screen bg-oatmeal">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-md mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <ChefHat className="h-8 w-8 text-blueberry" />
              <h1 className="text-2xl font-bold text-gray-900">Crumb</h1>
            </div>
            <Link 
              to="/settings"
              className="text-gray-600 hover:text-gray-900"
            >
              Settings
            </Link>
          </div>
        </div>
      </header>

      <div className="max-w-md mx-auto px-4 py-6">
        {/* Search */}
        <div className="relative mb-6">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
          <input
            type="text"
            placeholder="Search recipes..."
            value={localQuery}
            onChange={(e) => handleSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blueberry focus:border-transparent"
          />
        </div>

        {/* Recipe List */}
        {isLoading ? (
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="bg-white rounded-lg p-4 shadow-sm animate-pulse">
                <div className="flex space-x-4">
                  <div className="w-16 h-16 bg-gray-300 rounded-lg"></div>
                  <div className="flex-1 space-y-2">
                    <div className="h-4 bg-gray-300 rounded w-3/4"></div>
                    <div className="h-3 bg-gray-300 rounded w-1/2"></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : filteredRecipes.length === 0 ? (
          <div className="text-center py-12">
            <ChefHat className="h-16 w-16 mx-auto text-gray-400 mb-4" />
            <h3 className="text-lg font-semibold text-gray-600 mb-2">
              {searchQuery ? 'No recipes found' : 'No recipes yet'}
            </h3>
            <p className="text-gray-500 mb-6">
              {searchQuery 
                ? 'Try searching with different keywords'
                : 'Import your first recipe to get started'
              }
            </p>
            {!searchQuery && (
              <Link
                to="/import"
                className="inline-flex items-center px-6 py-3 bg-blueberry text-white rounded-lg hover:bg-blueberry/90 transition-colors"
              >
                <Plus className="h-5 w-5 mr-2" />
                Import Recipe
              </Link>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {filteredRecipes.map((recipe) => (
              <div
                key={recipe.id}
                className="bg-white rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow relative group"
              >
                <Link
                  to={`/recipe/${recipe.id}`}
                  className="block"
                >
                  <div className="flex space-x-4">
                    {recipe.image ? (
                      <img
                        src={recipe.image}
                        alt={recipe.title}
                        className="w-16 h-16 object-cover rounded-lg"
                      />
                    ) : (
                      <div className="w-16 h-16 bg-dough rounded-lg flex items-center justify-center">
                        <ChefHat className="h-8 w-8 text-gray-600" />
                      </div>
                    )}
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-gray-900 truncate pr-8">
                        {recipe.title}
                      </h3>
                      <p className="text-sm text-gray-600 truncate">
                        {recipe.sourceName || 'Unknown Source'}
                      </p>
                      <div className="flex items-center space-x-4 mt-1 text-xs text-gray-500">
                        {recipe.yield && (
                          <span>Serves {recipe.yield}</span>
                        )}
                        {recipe.times?.total && (
                          <span>{recipe.times.total} min</span>
                        )}
                      </div>
                    </div>
                  </div>
                </Link>
                
                {/* Delete button */}
                <button
                  onClick={(e) => handleDelete(e, recipe.id, recipe.title)}
                  className="absolute top-4 right-4 p-1 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors opacity-0 group-hover:opacity-100"
                  title="Delete recipe"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Floating Action Button */}
        <Link
          to="/import"
          className="fixed bottom-6 right-6 bg-blueberry text-white p-4 rounded-full shadow-lg hover:bg-blueberry/90 transition-colors"
        >
          <Plus className="h-6 w-6" />
        </Link>
      </div>
    </div>
  );
}