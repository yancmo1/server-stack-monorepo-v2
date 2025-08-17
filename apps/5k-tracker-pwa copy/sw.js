// Service Worker for Race Tracker PWA
self.addEventListener('install', function(event) {
  console.log('[Service Worker] Installing Service Worker ...', event);
});

self.addEventListener('activate', function(event) {
  console.log('[Service Worker] Activating Service Worker ...', event);
});

self.addEventListener('fetch', function(event) {
  // You can add custom fetch logic here for offline support
  console.log('[Service Worker] Fetching something ...', event.request.url);
});
