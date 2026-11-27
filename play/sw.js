// Robot Lab Breakout offline support: game files come from the cache, the daily puzzle from the network when possible.
const CACHE = "rlb-c19e27b73a";
const FILES = ["./", "index.html", "worlds.json", "manifest.webmanifest", "fonts/Baloo2-700.ttf", "fonts/Baloo2-800.ttf", "fonts/Nunito-400.ttf", "fonts/Nunito-700.ttf", "fonts/Nunito-800.ttf", "icons/icon-192.png", "icons/icon-512.png", "icons/apple-touch-icon.png"];
self.addEventListener("install", e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES)).then(() => self.skipWaiting())); });
self.addEventListener("activate", e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin) return;
  if (url.pathname.endsWith("/daily.json")) {
    const key = new Request(url.origin + url.pathname);
    e.respondWith(fetch(e.request).then(r => { if (r.ok) { const copy = r.clone(); caches.open(CACHE).then(c => c.put(key, copy)); } return r; }).catch(() => caches.match(key)));
    return;
  }
  e.respondWith(caches.match(e.request, {ignoreSearch: true}).then(hit => hit || fetch(e.request).then(r => { if (r.ok && url.pathname.includes("/play/")) { const copy = r.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); } return r; })));
});
