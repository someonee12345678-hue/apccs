/* Offline copy page. It keeps the control panel start page in the browser's cache, so the home screen icon opens
   when the panel is not running. It never deletes a kept copy and uses no other browser storage. Text goes into
   the page only with textContent and createElement. */
"use strict";

var KEEP_CACHE = "control-panel-start-v1";
var KEEP_ADDRESSES = ["/", "/offline.html", "/screen_offline.js"];
var STATUS_ADDRESS = "/api/panel/screens";

function showStatus(text, offline) {
  var status = document.getElementById("status");
  status.textContent = text;
  status.className = offline ? "offline" : "";
}

function registerPanelWorker() {
  if (!("serviceWorker" in navigator)) {
    return Promise.resolve();
  }
  return navigator.serviceWorker.register("sw.js").catch(function () {
    return null;
  });
}

function panelIsRunning() {
  return fetch(STATUS_ADDRESS).then(function (response) {
    return response.ok && response.headers.get("X-Panel-Offline") !== "1";
  }).catch(function () {
    return false;
  });
}

function showKeptList() {
  var list = document.getElementById("kept-list");
  while (list.firstChild) {
    list.removeChild(list.firstChild);
  }
  return caches.open(KEEP_CACHE).then(function (cache) {
    return cache.keys();
  }).then(function (requests) {
    var kept = requests.map(function (request) {
      return new URL(request.url).pathname;
    });
    KEEP_ADDRESSES.forEach(function (address) {
      var item = document.createElement("li");
      item.textContent = address + ": " + (kept.indexOf(address) >= 0 ? "kept" : "not kept yet");
      list.appendChild(item);
    });
  });
}

function keepNow() {
  return registerPanelWorker().then(panelIsRunning).then(function (running) {
    if (!running) {
      showStatus("offline: the control panel is not running, so nothing new was kept.", true);
      return null;
    }
    return caches.open(KEEP_CACHE).then(function (cache) {
      return cache.addAll(KEEP_ADDRESSES);
    }).then(function () {
      showStatus("Kept: the control panel icon now opens even when the panel is not running.", false);
    });
  }).then(showKeptList).catch(function () {
    showStatus("offline: the copy could not be kept on this phone.", true);
  });
}

document.getElementById("keep-now").addEventListener("click", keepNow);
keepNow();
