// v2: HTML・データは「ネットワーク優先」にして、更新が古いキャッシュに邪魔されないようにした。
// オフライン時（または通信が遅いとき）はキャッシュから表示する。
const CACHE = "minecraft-recipe-v2";
const CORE = ["./", "./index.html", "./manifest.webmanifest", "./data/recipes.json"];
const NETWORK_TIMEOUT_MS = 4000;

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE)
      // 1つ失敗（初回ビルド前の recipes.json など）しても残りは保存する
      .then(cache => Promise.allSettled(CORE.map(url => cache.add(new Request(url, { cache: "reload" })))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

function networkFirst(req) {
  return new Promise(resolve => {
    let settled = false;
    const finish = res => { if (!settled) { settled = true; resolve(res); } };
    const fromCache = () => caches.match(req, { ignoreSearch: true }).then(hit => hit || caches.match("./index.html"));
    const timer = setTimeout(() => fromCache().then(hit => hit && finish(hit)), NETWORK_TIMEOUT_MS);
    fetch(req).then(res => {
      clearTimeout(timer);
      if (res.ok) {
        const copy = res.clone();
        caches.open(CACHE).then(cache => cache.put(req, copy));
      }
      finish(res);
    }).catch(() => {
      clearTimeout(timer);
      fromCache().then(hit => finish(hit || Response.error()));
    });
  });
}

self.addEventListener("fetch", event => {
  const req = event.request;
  if (req.method !== "GET" || new URL(req.url).origin !== self.location.origin) return;
  event.respondWith(networkFirst(req));
});
