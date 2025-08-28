import { useEffect } from 'react';
import { useCookSessionStore } from '../stores/cookSessionStore';
import { ScalingEngine } from '../lib/scaling';
import { ArrowLeft, Check, Clock, Users, Scale, X } from 'lucide-react';
import type { Recipe } from '../types/recipe';

interface CookSessionProps {
  recipe: Recipe;
  onBack: () => void;
}

export function CookSession({ recipe, onBack }: CookSessionProps) {
  const {
    currentSession,
    toggleIngredient,
    toggleStep,
    updateMultiplier,
    endSession,
    loadSession
  } = useCookSessionStore();

  useEffect(() => {
    loadSession(recipe.id);
  }, [recipe.id, loadSession]);

  if (!currentSession) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading cooking session...</p>
        </div>
      </div>
    );
  }

  const scaledIngredients = ScalingEngine.scaleIngredients(recipe.ingredients, currentSession.multiplier);
  const suggestedMultipliers = ScalingEngine.getSuggestedMultipliers();

  const checkedIngredientsCount = Object.values(currentSession.checkedIngredients).filter(Boolean).length;
  const checkedStepsCount = Object.values(currentSession.checkedSteps).filter(Boolean).length;
  const totalProgress = (checkedIngredientsCount + checkedStepsCount) / (recipe.ingredients.length + recipe.steps.length) * 100;

  const handleEndSession = async () => {
    await endSession();
    onBack();
  };

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <button
            onClick={onBack}
            className="inline-flex items-center text-gray-600 hover:text-gray-900"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to recipe
          </button>
          
          <button
            onClick={handleEndSession}
            className="inline-flex items-center px-3 py-2 text-red-600 hover:text-red-800"
          >
            <X className="h-4 w-4 mr-2" />
            End Session
          </button>
        </div>

        <h1 className="text-2xl font-bold text-gray-900 mb-2">Cooking: {recipe.title}</h1>
        
        <div className="flex items-center gap-6 text-sm text-gray-500 mb-4">
          {recipe.times?.total && (
            <div className="flex items-center">
              <Clock className="w-4 h-4 mr-1" />
              {recipe.times.total}min total
            </div>
          )}
          {recipe.servings && (
            <div className="flex items-center">
              <Users className="w-4 h-4 mr-1" />
              {Math.round(recipe.servings * currentSession.multiplier)} servings
            </div>
          )}
        </div>

        {/* Progress Bar */}
        <div className="mb-4">
          <div className="flex justify-between text-sm text-gray-600 mb-1">
            <span>Progress</span>
            <span>{Math.round(totalProgress)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-orange-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${totalProgress}%` }}
            ></div>
          </div>
        </div>

        {/* Scaling Control */}
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-600">
            {checkedIngredientsCount} of {recipe.ingredients.length} ingredients • {checkedStepsCount} of {recipe.steps.length} steps
          </div>
          
          <div className="flex items-center space-x-2">
            <Scale className="h-4 w-4 text-gray-500" />
            <select
              value={currentSession.multiplier}
              onChange={(e) => updateMultiplier(Number(e.target.value))}
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
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Ingredients Checklist */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Ingredients ({checkedIngredientsCount}/{recipe.ingredients.length})
            </h2>
            
            <div className="space-y-3">
              {scaledIngredients.map((ingredient, index) => {
                const isChecked = currentSession.checkedIngredients[index] || false;
                return (
                  <label
                    key={index}
                    className={`flex items-start p-3 rounded-lg border-2 cursor-pointer transition-colors ${
                      isChecked
                        ? 'bg-green-50 border-green-200'
                        : 'bg-white border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={() => toggleIngredient(index)}
                      className="sr-only"
                    />
                    <div className={`flex-shrink-0 w-5 h-5 rounded border-2 flex items-center justify-center mr-3 mt-0.5 ${
                      isChecked ? 'bg-green-500 border-green-500' : 'border-gray-300'
                    }`}>
                      {isChecked && <Check className="w-3 h-3 text-white" />}
                    </div>
                    <span className={`${isChecked ? 'line-through text-gray-500' : 'text-gray-800'}`}>
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
                  </label>
                );
              })}
            </div>
          </div>
        </div>

        {/* Steps Checklist */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Instructions ({checkedStepsCount}/{recipe.steps.length})
            </h2>
            
            <div className="space-y-4">
              {recipe.steps.map((step, index) => {
                const isChecked = currentSession.checkedSteps[index] || false;
                return (
                  <label
                    key={index}
                    className={`flex items-start p-4 rounded-lg border-2 cursor-pointer transition-colors ${
                      isChecked
                        ? 'bg-green-50 border-green-200'
                        : 'bg-white border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={() => toggleStep(index)}
                      className="sr-only"
                    />
                    <div className={`flex-shrink-0 w-6 h-6 rounded border-2 flex items-center justify-center mr-4 mt-0.5 ${
                      isChecked ? 'bg-green-500 border-green-500 text-white' : 'border-gray-300 text-gray-600'
                    }`}>
                      {isChecked ? (
                        <Check className="w-4 h-4" />
                      ) : (
                        <span className="text-sm font-medium">{index + 1}</span>
                      )}
                    </div>
                    <p className={`leading-relaxed ${
                      isChecked ? 'line-through text-gray-500' : 'text-gray-800'
                    }`}>
                      {step}
                    </p>
                  </label>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Success State */}
      {totalProgress === 100 && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center">
          <div className="bg-white p-8 rounded-lg shadow-xl max-w-md mx-4 text-center">
            <div className="text-6xl mb-4">🎉</div>
            <h3 className="text-2xl font-bold text-gray-900 mb-2">Congratulations!</h3>
            <p className="text-gray-600 mb-6">You've completed cooking {recipe.title}. Enjoy your meal!</p>
            <button
              onClick={handleEndSession}
              className="w-full px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors"
            >
              Finish Cooking
            </button>
          </div>
        </div>
      )}
    </div>
  );
}