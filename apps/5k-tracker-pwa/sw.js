// Service Worker for Race Tracker PWA - lightweight cache versioning
const CACHE_PREFIX = 'race-tracker-v';
// IMPORTANT: bump this value on deploy (we set headers no-cache for sw.js and manifest)
const CACHE_VERSION = '1';
const CACHE_NAME = `${CACHE_PREFIX}${CACHE_VERSION}`;
const PRECACHE_URLS = [
  '/tracker/manifest.json',
  '/tracker/static/css/style.css',
  '/tracker/'
];

self.addEventListener('install', (event) => {
  console.log('[Service Worker] Install, precaching:', PRECACHE_URLS);
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(PRECACHE_URLS))
  );
});

self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activate - clearing old caches');
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(
      keys.filter(k => k.indexOf(CACHE_PREFIX) === 0 && k !== CACHE_NAME)
          .map(oldKey => caches.delete(oldKey))
    ))
    .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  // For navigation and app shell, prefer network but fallback to cache
  if (event.request.mode === 'navigate' || (event.request.method === 'GET' && event.request.headers.get('accept')?.includes('text/html'))) {
    event.respondWith(
      fetch(event.request).catch(() => caches.match('/tracker/') )
    );
    return;
  }

  // For other requests, try cache first then network
  event.respondWith(
    caches.match(event.request).then((resp) => resp || fetch(event.request))
  );
});
