import { useState } from 'react';
import { RecipeList } from './components/RecipeList';
import { RecipeDetail } from './components/RecipeDetail';
import { CookSession } from './components/CookSession';
import { RecipeImportModal } from './components/RecipeImportModal';
import { ChefHat, Plus, Search } from 'lucide-react';
import type { Recipe } from './types/recipe';

type View = 'list' | 'detail' | 'cooking';

function App() {
  const [currentView, setCurrentView] = useState<View>('list');
  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null);
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);

  const handleRecipeSelect = (recipe: Recipe) => {
    setSelectedRecipe(recipe);
    setCurrentView('detail');
  };

  const handleStartCooking = (recipe: Recipe) => {
    setSelectedRecipe(recipe);
    setCurrentView('cooking');
  };

  const handleBackToList = () => {
    setCurrentView('list');
    setSelectedRecipe(null);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <ChefHat className="h-8 w-8 text-orange-500 mr-3" />
              <h1 className="text-xl font-bold text-gray-900">Crumb</h1>
            </div>
            
            <div className="flex items-center space-x-4">
              <button className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
                <Search className="h-4 w-4 mr-2" />
                Search
              </button>
              <button 
                onClick={() => setIsImportModalOpen(true)}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-orange-500 hover:bg-orange-600"
              >
                <Plus className="h-4 w-4 mr-2" />
                Add Recipe
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {currentView === 'list' && (
          <RecipeList 
            onRecipeSelect={handleRecipeSelect}
            onStartCooking={handleStartCooking}
          />
        )}
        
        {currentView === 'detail' && selectedRecipe && (
          <RecipeDetail 
            recipe={selectedRecipe}
            onBack={handleBackToList}
            onStartCooking={() => handleStartCooking(selectedRecipe)}
          />
        )}
        
        {currentView === 'cooking' && selectedRecipe && (
          <CookSession 
            recipe={selectedRecipe}
            onBack={handleBackToList}
          />
        )}
      </main>

      {/* Import Modal */}
      <RecipeImportModal 
        isOpen={isImportModalOpen}
        onClose={() => setIsImportModalOpen(false)}
      />
    </div>
  );
}

export default App;
