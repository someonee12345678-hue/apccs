/* Control panel service worker. It keeps the six app files, each screen script once seen, and
   the last answers, so the page still opens offline and says so. */
"use strict";

var CACHE_NAME = "control-panel-v1";
var APP_FILES = ["index.html", "app.js", "style.css", "manifest.webmanifest", "sw.js", "icon.svg"];
var KEPT_ANSWERS = ["/api/panel/screens", "/api/panel/home/projects", "/api/panel/home/checks"];

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
  headers.set("X-Panel-Offline", "1");
  return response.blob().then(function (body) {
    return new Response(body, { status: 200, headers: headers });
  });
}

function isScreenScript(pathname) {
  return /^\/screen_[a-z]+\.js$/.test(pathname);
}

self.addEventListener("fetch", function (event) {
  var url = new URL(event.request.url);
  if (event.request.method !== "GET" || url.origin !== self.location.origin) {
    return;
  }
  if (KEPT_ANSWERS.indexOf(url.pathname) >= 0 || isScreenScript(url.pathname)) {
    event.respondWith(
      fetch(event.request)
        .then(function (response) {
          var copy = response.clone();
          caches.open(CACHE_NAME).then(function (cache) {
            cache.put(url.pathname, copy);
          });
          return response;
        })
        .catch(function () {
          return caches.match(url.pathname).then(function (saved) {
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
