// FinSight AI — Service Worker

const CACHE_NAME = "finsight-v5";

const STATIC_ASSETS = [
  "./",
  "./index.html",
  "./dashboard.html",
  "./assets/style.css",
  "./assets/app.js",
  "./manifest.json"
];

// Install — cache all static assets
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

// Activate — clean old caches
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== CACHE_NAME)
          .map((key) => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

// Fetch — serve from cache, fallback to network
self.addEventListener("fetch", (event) => {
  // API calls — network only, no cache
  if (event.request.url.includes("/api/")) {
    return;
  }

  // Keep JS/CSS fresh so frontend fixes propagate without manual cache clears.
  if (event.request.destination === "script" || event.request.destination === "style") {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, responseClone));
          return response;
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }

  // Always try network first for HTML so dashboard updates are visible immediately.
  if (event.request.mode === "navigate" || event.request.destination === "document") {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, responseClone));
          return response;
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cached) => {
      return cached || fetch(event.request);
    })
  );
});