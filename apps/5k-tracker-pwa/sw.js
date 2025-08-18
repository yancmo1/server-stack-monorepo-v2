// Service Worker for Race Tracker PWA - lightweight cache versioning
const CACHE_PREFIX = 'race-tracker-v';
// IMPORTANT: bump this value on deploy (we set headers no-cache for sw.js and manifest)
const CACHE_VERSION = '7';
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
  const req = event.request;
  const accept = req.headers.get('accept') || '';

  // Navigation and HTML: network-first with offline fallback to cached shell
  if (req.mode === 'navigate' || (req.method === 'GET' && accept.includes('text/html'))) {
    event.respondWith(
      fetch(req).catch(() => caches.match('/tracker/'))
    );
    return;
  }

  // CSS/JS: network-first so style/script updates land immediately after deploy
  if (accept.includes('text/css') || accept.includes('javascript')) {
    event.respondWith((async () => {
      try {
        const fresh = await fetch(req);
        const cache = await caches.open(CACHE_NAME);
        cache.put(req, fresh.clone());
        return fresh;
      } catch (e) {
        const cached = await caches.match(req);
        return cached || fetch(req);
      }
    })());
    return;
  }

  // Images and others: cache-first with network fallback
  event.respondWith(
    caches.match(req).then((resp) => resp || fetch(req))
  );
});
