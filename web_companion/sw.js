const CACHE_NAME = "softwarecenter-companion-v3";
const OFFLINE_ASSETS = [
  "./",
  "./index.html",
  "./app.css",
  "./app.js",
  "./library.js",
  "./manifest.webmanifest",
  "./icon.svg",
  "./icons/Icon-192.png",
  "./icons/Icon-512.png",
  "./icons/Icon-maskable-192.png",
  "./icons/Icon-maskable-512.png",
  "./icons/apple-touch-icon-180.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(OFFLINE_ASSETS)),
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== CACHE_NAME)
          .map((key) => caches.delete(key)),
      ),
    ),
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") {
    return;
  }
  event.respondWith(
    caches.match(event.request, { ignoreSearch: true }).then(
      (cached) =>
        cached ||
        fetch(event.request).catch(
          () => new Response("Offline", { status: 503, headers: { "Content-Type": "text/plain" } })
        )
    )
  );
});
