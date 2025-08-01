/**
 * 5K Tracker Service Worker
 * Provides offline functionality and asset caching for the Progressive Web App
 */

const CACHE_NAME = '5k-tracker-v1';
const urlsToCache = [
  '/',
  '/dashboard',
  '/races',
  '/add_race',
  '/statistics',
  '/static/css/style.css',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png',
  '/static/manifest.json',
  // Bootstrap CSS
  'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css',
  // Font Awesome CSS
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css',
  // Bootstrap JS
  'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js'
];

// Install event - cache essential resources
self.addEventListener('install', event => {
  console.log('Service Worker: Installing...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Service Worker: Caching essential resources...');
        return cache.addAll(urlsToCache);
      })
      .then(() => {
        console.log('Service Worker: Installation complete');
        return self.skipWaiting();
      })
      .catch(error => {
        console.error('Service Worker: Installation failed:', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  console.log('Service Worker: Activating...');
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('Service Worker: Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      console.log('Service Worker: Activation complete');
      return self.clients.claim();
    })
  );
});

// Fetch event - serve from cache when offline, with network-first strategy for dynamic content
self.addEventListener('fetch', event => {
  const request = event.request;
  const url = new URL(request.url);
  
  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }
  
  // Handle different types of requests
  if (url.pathname.startsWith('/static/') || 
      url.hostname === 'cdn.jsdelivr.net' || 
      url.hostname === 'cdnjs.cloudflare.com') {
    // Cache-first strategy for static assets and CDN resources
    event.respondWith(
      caches.match(request)
        .then(response => {
          if (response) {
            return response;
          }
          return fetch(request).then(response => {
            // Don't cache if not a valid response
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }
            
            // Clone the response
            const responseToCache = response.clone();
            
            caches.open(CACHE_NAME)
              .then(cache => {
                cache.put(request, responseToCache);
              });
            
            return response;
          });
        })
        .catch(() => {
          // If both cache and network fail, return a fallback for images
          if (request.destination === 'image') {
            return new Response(
              '<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg"><rect width="200" height="200" fill="#ddd"/><text x="50%" y="50%" text-anchor="middle" dy=".3em">Image unavailable</text></svg>',
              { headers: { 'Content-Type': 'image/svg+xml' } }
            );
          }
        })
    );
  } else if (url.pathname.startsWith('/')) {
    // Network-first strategy for app routes
    event.respondWith(
      fetch(request)
        .then(response => {
          // Clone the response
          const responseToCache = response.clone();
          
          // Cache successful responses
          if (response.status === 200) {
            caches.open(CACHE_NAME)
              .then(cache => {
                cache.put(request, responseToCache);
              });
          }
          
          return response;
        })
        .catch(() => {
          // Fall back to cache
          return caches.match(request)
            .then(response => {
              if (response) {
                return response;
              }
              // If no cached version, return offline page
              return caches.match('/')
                .then(fallbackResponse => {
                  if (fallbackResponse) {
                    return fallbackResponse;
                  }
                  // Ultimate fallback
                  return new Response(
                    '<!DOCTYPE html><html><head><title>5K Tracker - Offline</title><meta name="viewport" content="width=device-width, initial-scale=1.0"></head><body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;"><h1>🏃‍♂️ 5K Tracker</h1><p>You are currently offline. Please check your internet connection and try again.</p><button onclick="window.location.reload()">Retry</button></body></html>',
                    { 
                      headers: { 
                        'Content-Type': 'text/html',
                        'Cache-Control': 'no-cache'
                      } 
                    }
                  );
                });
            });
        })
    );
  }
});

// Background sync for race data (if supported)
self.addEventListener('sync', event => {
  console.log('Service Worker: Background sync triggered:', event.tag);
  
  if (event.tag === 'race-sync') {
    event.waitUntil(
      // This would sync pending race data when connection is restored
      syncRaceData()
    );
  }
});

// Handle push notifications (future feature)
self.addEventListener('push', event => {
  console.log('Service Worker: Push message received');
  
  const options = {
    body: event.data ? event.data.text() : 'New race reminder!',
    icon: '/tracker/static/icons/icon-192x192.png',
    badge: '/tracker/static/icons/favicon-32x32.png',
    vibrate: [200, 100, 200],
    data: {
      url: '/dashboard'
    },
    actions: [
      {
        action: 'view',
        title: 'View Dashboard'
      },
      {
        action: 'dismiss',
        title: 'Dismiss'
      }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification('5K Tracker', options)
  );
});

// Handle notification clicks
self.addEventListener('notificationclick', event => {
  console.log('Service Worker: Notification click received');
  
  event.notification.close();
  
  if (event.action === 'view') {
    event.waitUntil(
      clients.openWindow('/dashboard')
    );
  }
});

// Helper function for syncing race data
async function syncRaceData() {
  try {
    // This would implement actual sync logic with the server
    console.log('Service Worker: Syncing race data...');
    return Promise.resolve();
  } catch (error) {
    console.error('Service Worker: Race data sync failed:', error);
    throw error;
  }
}