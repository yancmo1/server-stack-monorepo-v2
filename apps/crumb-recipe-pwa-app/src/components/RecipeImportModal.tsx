import { useState } from 'react';
import { useRecipeStore } from '../stores/recipeStore';
import { X, Globe, Plus } from 'lucide-react';

interface RecipeImportModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function RecipeImportModal({ isOpen, onClose }: RecipeImportModalProps) {
  const [url, setUrl] = useState('');
  const { importRecipeFromUrl, loading, error } = useRecipeStore();

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    
    try {
      await importRecipeFromUrl(url.trim());
      setUrl('');
      onClose();
    } catch (error) {
      // Error is handled by the store
    }
  };

  const handleClose = () => {
    setUrl('');
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-gray-900">Import Recipe</h3>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="recipe-url" className="block text-sm font-medium text-gray-700 mb-2">
              Recipe URL
            </label>
            <div className="relative">
              <Globe className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
              <input
                id="recipe-url"
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://example.com/recipe"
                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:ring-orange-500 focus:border-orange-500"
                required
                disabled={loading}
              />
            </div>
            <p className="mt-1 text-sm text-gray-500">
              Enter the URL of a recipe page to import it automatically
            </p>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          <div className="flex space-x-3">
            <button
              type="button"
              onClick={handleClose}
              className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !url.trim()}
              className="flex-1 inline-flex items-center justify-center px-4 py-2 text-sm font-medium text-white bg-orange-500 border border-transparent rounded-md hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              ) : (
                <Plus className="h-4 w-4 mr-2" />
              )}
              {loading ? 'Importing...' : 'Import Recipe'}
            </button>
          </div>
        </form>

        <div className="mt-4 text-xs text-gray-500">
          <p className="mb-2"><strong>Demo Mode:</strong> This will create a sample recipe based on the URL you provide.</p>
          <p>In a full implementation, this would:</p>
          <p>• Extract recipes from sites with structured data (JSON-LD, microdata)</p>
          <p>• Support most popular cooking websites</p>
          <p>• Parse any page with clear recipe formatting</p>
        </div>
      </div>
    </div>
  );
}