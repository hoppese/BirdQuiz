// Cache-first so the app works offline once visited. Bump VERSION on changes.
const VERSION = "v3";
const SHELL = ["./", "index.html", "style.css", "app.js", "birds.json", "manifest.webmanifest"];
self.addEventListener("install", e => e.waitUntil(
  caches.open(VERSION).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())));
self.addEventListener("activate", e => e.waitUntil(
  caches.keys().then(ks => Promise.all(ks.filter(k => k !== VERSION).map(k => caches.delete(k))))
    .then(() => self.clients.claim())));
self.addEventListener("fetch", e => {
  if (e.request.method !== "GET" || /\.mp3$/.test(e.request.url) || e.request.headers.has("range")) return;  // Safari needs real Range responses for audio
  e.respondWith(caches.match(e.request).then(hit => hit || fetch(e.request).then(res => {
    const copy = res.clone(); caches.open(VERSION).then(c => c.put(e.request, copy)); return res; })));
});
