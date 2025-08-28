import { useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';
import { Toaster } from 'sonner';
import { useRecipeStore } from './state/session';
import Library from './pages/Library';
import ImportRecipe from './pages/ImportRecipe';
import RecipeDetail from './pages/RecipeDetail';
import Settings from './pages/Settings';
import { registerSW } from 'virtual:pwa-register';

// Register service worker
if ('serviceWorker' in navigator) {
  const updateSW = registerSW({
    onNeedRefresh() {
      if (confirm('New content available. Reload?')) {
        updateSW(true);
      }
    },
    onOfflineReady() {
      console.log('App ready to work offline');
    },
  });
}

function App() {
  const loadRecipes = useRecipeStore((state) => state.loadRecipes);

  useEffect(() => {
    loadRecipes();
  }, [loadRecipes]);

  return (
    <div className="min-h-screen bg-background">
      <Routes>
        <Route path="/" element={<Library />} />
        <Route path="/import" element={<ImportRecipe />} />
        <Route path="/recipe/:id" element={<RecipeDetail />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
      <Toaster 
        position="top-center"
        toastOptions={{
          style: {
            background: 'hsl(var(--card))',
            color: 'hsl(var(--foreground))',
            border: '1px solid hsl(var(--border))',
          },
        }}
      />
    </div>
  );
}

export default App;