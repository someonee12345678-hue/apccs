/* Mission control service worker. It keeps the six app files and the last snapshot, so the page
   still opens offline and shows the last snapshot marked offline. */
"use strict";

var CACHE_NAME = "mission-control-v1";
var SNAPSHOT_URL = "/api/mission/snapshot";
var APP_FILES = ["index.html", "app.js", "style.css", "manifest.webmanifest", "sw.js", "icon.svg"];

self.addEventListener("install", function (event) {
  event.waitUntil(caches.open(CACHE_NAME).then(function (cache) {
    return cache.addAll(APP_FILES);
  }));
});

self.addEventListener("activate", function (event) {
  event.waitUntil(self.clients.claim());
});

function offlineCopy(response) {
  var headers = new Headers(response.headers);
  headers.set("X-Mission-Offline", "1");
  return response.blob().then(function (body) {
    return new Response(body, { status: 200, headers: headers });
  });
}

self.addEventListener("fetch", function (event) {
  var url = new URL(event.request.url);
  if (event.request.method !== "GET" || url.origin !== self.location.origin) {
    return;
  }
  if (url.pathname === SNAPSHOT_URL) {
    event.respondWith(
      fetch(event.request)
        .then(function (response) {
          var copy = response.clone();
          caches.open(CACHE_NAME).then(function (cache) {
            cache.put(SNAPSHOT_URL, copy);
          });
          return response;
        })
        .catch(function () {
          return caches.match(SNAPSHOT_URL).then(function (saved) {
            return saved ? offlineCopy(saved) : Response.error();
          });
        })
    );
    return;
  }
  event.respondWith(caches.match(event.request).then(function (saved) {
    return saved || fetch(event.request);
  }));
});
