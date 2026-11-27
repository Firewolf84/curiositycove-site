// BOLT's Little Lab offline support
const CACHE = "littlelab-7430ab2245";
const FILES = ["./", "index.html", "manifest.webmanifest", "icons/icon-192.png", "icons/icon-512.png", "icons/apple-touch-icon.png", "../play/fonts/Baloo2-700.ttf", "../play/fonts/Baloo2-800.ttf", "../play/fonts/Nunito-400.ttf", "../play/fonts/Nunito-700.ttf", "../play/fonts/Nunito-800.ttf"];
self.addEventListener("install", e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES)).then(() => self.skipWaiting())); });
self.addEventListener("activate", e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k.startsWith("littlelab-") && k !== CACHE && k !== "littlelab-voice").map(k => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin) return;
  if (e.request.mode === "navigate" || url.pathname.endsWith("/") || url.pathname.endsWith(".html")) {
    e.respondWith(fetch(e.request).then(r => { if (r.ok && !r.redirected) { const copy = r.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); } return r; }).catch(() => caches.match(e.request, {ignoreSearch: true}).then(h => h || caches.match("index.html"))));
    return;
  }
  if (url.pathname.endsWith(".json")) {  // voice list: always ask for the newest
    e.respondWith(fetch(e.request).then(r => { if (r.ok) { const copy = r.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); } return r; }).catch(() => caches.match(e.request, {ignoreSearch: true})));
    return;
  }
  if (url.pathname.endsWith(".mp3")) {  // recordings never change (named by their words): keep them for offline play
    e.respondWith(caches.open("littlelab-voice").then(c => c.match(e.request).then(h => h || fetch(e.request).then(r => { if (r.ok) c.put(e.request, r.clone()); return r; }))));
    return;
  }
  e.respondWith(caches.match(e.request, {ignoreSearch: true}).then(h => h || fetch(e.request)));
});
