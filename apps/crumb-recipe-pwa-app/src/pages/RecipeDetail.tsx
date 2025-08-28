import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Clock, Users, Printer, RotateCcw, Plus, Minus, Trash2, Scale, Camera, Upload } from 'lucide-react';
import { toast } from 'sonner';
import { useRecipeStore, useCookSession } from '../state/session';
import { scaleIngredients, formatFraction, getMultiplierOptions, getIngredientDisplayAmount } from '../utils/scale';
import { isConvertibleToGrams } from '../utils/conversions';
import type { Recipe } from '../types';

export default function RecipeDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { recipes, deleteRecipe, updateRecipe } = useRecipeStore();
  const { 
    currentSession, 
    loadSession, 
    createNewSession,
    toggleIngredient,
    toggleStep,
    setMultiplier,
    resetSession,
    getTimeRemaining
  } = useCookSession();
  
  const [recipe, setRecipe] = useState<Recipe | null>(null);
  const [showGrams, setShowGrams] = useState(false);
  const [currentMultiplier, setCurrentMultiplier] = useState(1); // Local multiplier state
  const [selectedMultiplier, setSelectedMultiplier] = useState('1');
  const [showCustomInput, setShowCustomInput] = useState(false);
  const [customMultiplier, setCustomMultiplier] = useState('1');
  const [isUploadingPhoto, setIsUploadingPhoto] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (id) {
      const foundRecipe = recipes.find(r => r.id === id);
      if (foundRecipe) {
        setRecipe(foundRecipe);
        loadSession(id);
      } else {
        navigate('/');
      }
    }
  }, [id, recipes, navigate, loadSession]);

  // Sync local multiplier with session multiplier
  useEffect(() => {
    if (currentSession?.multiplier) {
      setCurrentMultiplier(currentSession.multiplier);
    }
  }, [currentSession?.multiplier]);

  if (!recipe) {
    return (
      <div className="min-h-screen bg-oatmeal flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-blueberry border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading recipe...</p>
        </div>
      </div>
    );
  }

  // Use local multiplier, fallback to session multiplier
  const multiplier = currentMultiplier || currentSession?.multiplier || 1;
  const scaledIngredients = scaleIngredients(recipe.ingredients, multiplier, showGrams);
  const timeRemaining = getTimeRemaining();
  const hoursRemaining = Math.floor(timeRemaining / (1000 * 60 * 60));
  const minutesRemaining = Math.floor((timeRemaining % (1000 * 60 * 60)) / (1000 * 60));

  // Check if any ingredients can be converted to grams
  const hasConvertibleIngredients = recipe.ingredients.some(ingredient => 
    isConvertibleToGrams(ingredient)
  );

  const handleStartSession = () => {
    if (id) {
      createNewSession(id);
      // Sync the current multiplier to the new session
      if (currentMultiplier !== 1) {
        setTimeout(() => setMultiplier(currentMultiplier), 100);
      }
    }
    toast.success('Cooking session started!');
  };

  const handleResetSession = () => {
    resetSession();
    toast.success('Session reset!');
  };

  const handleMultiplierChange = (newMultiplier: number | string) => {
    if (newMultiplier === 'custom') {
      setShowCustomInput(true);
      return;
    }
    
    const multiplierValue = typeof newMultiplier === 'string' ? parseFloat(newMultiplier) : newMultiplier;
    if (!isNaN(multiplierValue) && multiplierValue > 0) {
      setCurrentMultiplier(multiplierValue);
      // Also update session if active
      if (currentSession) {
        setMultiplier(multiplierValue);
      }
      setShowCustomInput(false);
    }
  };

  const handleCustomMultiplier = () => {
    const value = parseFloat(customMultiplier);
    if (!isNaN(value) && value > 0) {
      handleMultiplierChange(value);
    } else {
      toast.error('Please enter a valid number');
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const handleDelete = async () => {
    if (!recipe || !id) return;
    
    if (confirm(`Are you sure you want to delete "${recipe.title}"? This action cannot be undone.`)) {
      try {
        await deleteRecipe(id);
        toast.success('Recipe deleted successfully');
        navigate('/');
      } catch (error) {
        toast.error('Failed to delete recipe');
      }
    }
  };

  const handlePhotoUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !recipe) return;

    // Check file type
    if (!file.type.startsWith('image/')) {
      toast.error('Please select an image file');
      return;
    }

    // Check file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      toast.error('Image must be smaller than 5MB');
      return;
    }

    setIsUploadingPhoto(true);

    try {
      // Convert image to base64 data URL for local storage
      const reader = new FileReader();
      reader.onload = async (e) => {
        const imageDataUrl = e.target?.result as string;
        
        // Update recipe with new image
        const updatedRecipe = {
          ...recipe,
          image: imageDataUrl,
          updatedAt: Date.now()
        };

        await updateRecipe(updatedRecipe);
        setRecipe(updatedRecipe);
        toast.success('Photo updated successfully!');
        setIsUploadingPhoto(false);
      };

      reader.onerror = () => {
        toast.error('Failed to read image file');
        setIsUploadingPhoto(false);
      };

      reader.readAsDataURL(file);
    } catch (error) {
      console.error('Photo upload error:', error);
      toast.error('Failed to upload photo');
      setIsUploadingPhoto(false);
    }

    // Clear the input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const triggerPhotoUpload = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="min-h-screen bg-oatmeal">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200 no-print">
        <div className="max-w-md mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4 flex-1 min-w-0">
              <button
                onClick={() => navigate('/')}
                className="text-gray-600 hover:text-gray-900 flex-shrink-0"
              >
                <ArrowLeft className="h-6 w-6" />
              </button>
              <h1 className="text-xl font-semibold text-gray-900 truncate">
                {recipe.title}
              </h1>
            </div>
            <button
              onClick={handleDelete}
              className="text-gray-400 hover:text-red-500 p-2 -mr-2 flex-shrink-0"
              title="Delete recipe"
            >
              <Trash2 className="h-5 w-5" />
            </button>
          </div>
        </div>
      </header>

      {/* Session Status */}
      {currentSession && timeRemaining > 0 && (
        <div className="bg-sage text-white p-3 no-print">
          <div className="max-w-md mx-auto px-4 flex items-center justify-between">
            <span className="text-sm">
              Session expires in {hoursRemaining}h {minutesRemaining}m
            </span>
            <button
              onClick={handleResetSession}
              className="text-sm underline hover:no-underline"
            >
              Reset
            </button>
          </div>
        </div>
      )}

      <div className="max-w-md mx-auto px-4 py-6 space-y-6">
        {/* Recipe Info */}
        <div className="bg-white rounded-lg p-6 shadow-sm recipe-content">
          {/* Recipe Image with Upload Option */}
          <div className="relative mb-4">
            {recipe.image ? (
              <div className="relative group">
                <img
                  src={recipe.image}
                  alt={recipe.title}
                  className="w-full h-48 object-cover rounded-lg"
                />
                <button
                  onClick={triggerPhotoUpload}
                  disabled={isUploadingPhoto}
                  className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-50 rounded-lg transition-all duration-200 flex items-center justify-center opacity-0 group-hover:opacity-100"
                >
                  {isUploadingPhoto ? (
                    <div className="w-8 h-8 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  ) : (
                    <div className="flex flex-col items-center text-white">
                      <Camera className="h-8 w-8 mb-1" />
                      <span className="text-sm font-medium">Change Photo</span>
                    </div>
                  )}
                </button>
              </div>
            ) : (
              <button
                onClick={triggerPhotoUpload}
                disabled={isUploadingPhoto}
                className="w-full h-48 bg-gray-100 rounded-lg flex flex-col items-center justify-center hover:bg-gray-200 transition-colors border-2 border-dashed border-gray-300 hover:border-gray-400"
              >
                {isUploadingPhoto ? (
                  <div className="w-8 h-8 border-2 border-gray-400 border-t-transparent rounded-full animate-spin mb-2"></div>
                ) : (
                  <>
                    <Upload className="h-12 w-12 text-gray-400 mb-2" />
                    <span className="text-gray-600 font-medium">Add Photo</span>
                    <span className="text-gray-500 text-sm">Click to upload</span>
                  </>
                )}
              </button>
            )}
            
            {/* Hidden file input */}
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handlePhotoUpload}
              className="hidden"
              capture="environment" // Use camera on mobile
            />
          </div>
          
          <h1 className="text-2xl font-bold text-gray-900 mb-2">{recipe.title}</h1>
          
          <div className="flex items-center space-x-4 text-sm text-gray-600 mb-4">
            {recipe.sourceName && (
              <span>{recipe.sourceName}</span>
            )}
            {recipe.author && (
              <span>by {recipe.author}</span>
            )}
          </div>

          <div className="flex items-center space-x-6 text-sm text-gray-600">
            {recipe.yield && (
              <div className="flex items-center space-x-1">
                <Users className="h-4 w-4" />
                <span>{recipe.yield}</span>
              </div>
            )}
            {recipe.times?.total && (
              <div className="flex items-center space-x-1">
                <Clock className="h-4 w-4" />
                <span>{recipe.times.total} min</span>
              </div>
            )}
          </div>
        </div>

        {/* Scale Control */}
        <div className="bg-white rounded-lg p-4 shadow-sm no-print">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-gray-900">Scale Recipe</h3>
            {hasConvertibleIngredients && (
              <button
                onClick={() => setShowGrams(!showGrams)}
                className={`flex items-center space-x-1 px-2 py-1 rounded text-sm font-medium transition-colors ${
                  showGrams 
                    ? 'bg-sage text-white' 
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
                title="Convert to grams"
              >
                <Scale className="h-4 w-4" />
                <span>Grams</span>
              </button>
            )}
          </div>
          
          <div className="space-y-3">
            <div>
              <label htmlFor="multiplier-select" className="block text-sm font-medium text-gray-700 mb-1">
                Recipe Size
              </label>
              <select
                id="multiplier-select"
                value={multiplier.toString()}
                onChange={(e) => handleMultiplierChange(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blueberry focus:border-transparent bg-white text-gray-900"
              >
                {getMultiplierOptions().map(({ value, label }) => (
                  <option key={value} value={value.toString()}>
                    {label} {value === 1 ? '(Original)' : value < 1 ? '(Smaller)' : '(Larger)'}
                  </option>
                ))}
                <option value="custom">Custom Amount...</option>
              </select>
            </div>
            
            {multiplier !== 1 && (
              <div className="text-sm text-gray-600 bg-gray-50 p-2 rounded">
                Recipe scaled by {formatFraction(multiplier)}×
              </div>
            )}
          </div>

          {showCustomInput && (
            <div className="mt-3 space-y-2">
              <label htmlFor="custom-multiplier" className="block text-sm font-medium text-gray-700">
                Custom Multiplier
              </label>
              <div className="flex items-center space-x-2">
                <input
                  id="custom-multiplier"
                  type="number"
                  step="0.25"
                  min="0.25"
                  max="10"
                  value={customMultiplier}
                  onChange={(e) => setCustomMultiplier(e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blueberry focus:border-transparent"
                  placeholder="e.g., 1.5"
                />
                <button
                  onClick={handleCustomMultiplier}
                  className="px-4 py-2 bg-blueberry text-white rounded-lg hover:bg-blueberry/90 transition-colors"
                >
                  Apply
                </button>
                <button
                  onClick={() => setShowCustomInput(false)}
                  className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Ingredients */}
        <div className="bg-white rounded-lg p-6 shadow-sm recipe-content">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900">Ingredients</h2>
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              {multiplier !== 1 && (
                <span>Scaled by {formatFraction(multiplier)}×</span>
              )}
              {showGrams && (
                <span className="bg-sage text-white px-2 py-1 rounded text-xs">
                  Grams
                </span>
              )}
            </div>
          </div>
          
          <div className="space-y-3">
            {scaledIngredients.map((ingredient, index) => (
              <div
                key={index}
                className="flex items-start space-x-3 ingredient-item"
              >
                {currentSession ? (
                  <button
                    onClick={() => toggleIngredient(index)}
                    className={`mt-1 w-5 h-5 rounded border-2 flex-shrink-0 no-print ${
                      currentSession.checkedIngredients[index]
                        ? 'bg-sage border-sage'
                        : 'border-gray-300'
                    }`}
                  >
                    {currentSession.checkedIngredients[index] && (
                      <svg className="w-3 h-3 text-white m-auto" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    )}
                  </button>
                ) : (
                  <div className="mt-1 w-5 h-5 rounded border-2 border-gray-300 flex-shrink-0 print-only"></div>
                )}
                
                <span className={`text-gray-900 ${currentSession?.checkedIngredients[index] ? 'line-through opacity-60' : ''}`}>
                  {(() => {
                    if (showGrams && ingredient.gramsDisplay) {
                      // Show grams conversion
                      const item = ingredient.item;
                      const note = ingredient.note;
                      
                      return [
                        ingredient.gramsDisplay,
                        item && ` ${item}`,
                        note && ` (${note})`
                      ].filter(Boolean).join('');
                    } else {
                      // Show original measurements
                      const amount = getIngredientDisplayAmount(ingredient, false);
                      const unit = ingredient.unit;
                      const item = ingredient.item;
                      const note = ingredient.note;
                      
                      return [
                        amount,
                        unit && ` ${unit}`,
                        item && ` ${item}`,
                        note && ` (${note})`
                      ].filter(Boolean).join('');
                    }
                  })()}
                  {showGrams && !ingredient.gramsDisplay && (
                    <span className="text-gray-500 text-sm ml-2">(conversion not available)</span>
                  )}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Instructions */}
        <div className="bg-white rounded-lg p-6 shadow-sm recipe-content">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Instructions</h2>
          
          <div className="space-y-4">
            {recipe.steps.map((step, index) => (
              <div key={index} className="flex items-start space-x-3 step-item">
                {currentSession ? (
                  <button
                    onClick={() => toggleStep(index)}
                    className={`mt-1 w-6 h-6 rounded-full border-2 flex-shrink-0 no-print ${
                      currentSession.checkedSteps[index]
                        ? 'bg-sage border-sage'
                        : 'border-gray-300'
                    }`}
                  >
                    {currentSession.checkedSteps[index] && (
                      <svg className="w-4 h-4 text-white m-auto" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    )}
                  </button>
                ) : (
                  <span className="mt-1 w-6 h-6 rounded-full bg-blueberry text-white text-sm flex items-center justify-center flex-shrink-0">
                    {index + 1}
                  </span>
                )}
                
                <p className={`text-gray-900 ${currentSession?.checkedSteps[index] ? 'line-through opacity-60' : ''}`}>
                  {step}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Tips */}
        {recipe.tips && recipe.tips.length > 0 && (
          <div className="bg-white rounded-lg p-6 shadow-sm recipe-content">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Tips</h2>
            <div className="space-y-2">
              {recipe.tips.map((tip, index) => (
                <p key={index} className="text-gray-700">
                  • {tip}
                </p>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Sticky Action Bar */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 p-4 no-print ios-padding">
        <div className="max-w-md mx-auto flex justify-center space-x-4">
          {!currentSession ? (
            <button
              onClick={handleStartSession}
              className="flex-1 bg-blueberry text-white py-3 rounded-lg hover:bg-blueberry/90 transition-colors"
            >
              Start Cooking
            </button>
          ) : (
            <>
              <button
                onClick={handleResetSession}
                className="flex-1 bg-gray-100 text-gray-700 py-3 rounded-lg hover:bg-gray-200 transition-colors flex items-center justify-center space-x-2"
              >
                <RotateCcw className="h-5 w-5" />
                <span>Reset</span>
              </button>
              <button
                onClick={handlePrint}
                className="flex-1 bg-sage text-white py-3 rounded-lg hover:bg-sage/90 transition-colors flex items-center justify-center space-x-2"
              >
                <Printer className="h-5 w-5" />
                <span>Print</span>
              </button>
            </>
          )}
        </div>
      </div>

      {/* Bottom padding for sticky bar */}
      <div className="h-20 no-print"></div>
    </div>
  );
}