/* Mission control page. Read only: it fetches one relative address, the snapshot, and draws it.
   Text goes into the page only with textContent or SVG attributes. */
"use strict";

var SNAPSHOT_URL = "/api/mission/snapshot";
var REFRESH_MS = 30000;
var STATE_WORDS = ["working", "blocked", "done", "idle"];
var DAY_MS = 24 * 60 * 60 * 1000;

var lastSnapshot = null;
var offline = false;

function clear(node) {
  while (node.firstChild) {
    node.removeChild(node.firstChild);
  }
}

function addItem(list, text) {
  var item = document.createElement("li");
  item.textContent = text;
  list.appendChild(item);
}

function svgNode(root, name, attributes) {
  var node = document.createElementNS(root.namespaceURI, name);
  Object.keys(attributes).forEach(function (key) {
    node.setAttribute(key, String(attributes[key]));
  });
  return node;
}

function drawMap(snapshot) {
  var root = document.getElementById("map-svg");
  clear(root);
  var names = Object.keys(snapshot.agents || {});
  var positions = {};
  names.forEach(function (name, index) {
    var angle = (2 * Math.PI * index) / Math.max(names.length, 1) - Math.PI / 2;
    positions[name] = { x: 170 + 110 * Math.cos(angle), y: 130 + 90 * Math.sin(angle) };
  });
  var cutoff = Date.parse(snapshot.generated_at) - DAY_MS;
  (snapshot.handoffs || []).forEach(function (handoff) {
    var from = positions[handoff.from_agent];
    var to = positions[handoff.to_agent];
    if (!from || !to || Date.parse(handoff.time) < cutoff) {
      return;
    }
    root.appendChild(svgNode(root, "line", { x1: from.x, y1: from.y, x2: to.x, y2: to.y }));
    var label = svgNode(root, "text", { x: (from.x + to.x) / 2, y: (from.y + to.y) / 2, "text-anchor": "middle" });
    label.textContent = handoff.kind + " " + handoff.ref;
    root.appendChild(label);
  });
  names.forEach(function (name) {
    var state = snapshot.agents[name].state;
    var group = svgNode(root, "g", {});
    group.appendChild(svgNode(root, "rect", {
      x: positions[name].x - 45, y: positions[name].y - 20, width: 90, height: 40, rx: 6,
      "class": "state-" + (STATE_WORDS.indexOf(state) >= 0 ? state : "idle")
    }));
    var text = svgNode(root, "text", { x: positions[name].x, y: positions[name].y - 3, "text-anchor": "middle", "class": "node-label" });
    text.textContent = name;
    var word = svgNode(root, "text", { x: positions[name].x, y: positions[name].y + 14, "text-anchor": "middle", "class": "node-label" });
    word.textContent = state;
    group.appendChild(text);
    group.appendChild(word);
    root.appendChild(group);
  });
}

function describe(entry) {
  if (entry.batch) {
    return entry.batch + ": " + entry.state + (entry.holder ? " (" + entry.holder + ")" : "") + ", " + entry.time;
  }
  return entry.time + " " + entry.from_agent + " " + entry.kind + " " + entry.ref + (entry.summary ? ": " + entry.summary : "");
}

function drawTimeline(snapshot) {
  var list = document.getElementById("timeline-list");
  clear(list);
  var view = document.getElementById("view").value;
  var entries = (snapshot.timeline && snapshot.timeline[view]) || [];
  entries.forEach(function (entry) {
    addItem(list, describe(entry));
  });
}

function drawJobs(snapshot) {
  var list = document.getElementById("jobs-list");
  clear(list);
  (snapshot.jobs || []).forEach(function (job) {
    addItem(list, job.job + ": " + job.state + (job.holder ? " (" + job.holder + ")" : "") + ", " + job.time);
  });
}

function draw(snapshot) {
  lastSnapshot = snapshot;
  var status = document.getElementById("status");
  status.textContent = (offline ? "offline: showing the last snapshot from " : "Snapshot from ") + snapshot.generated_at;
  drawMap(snapshot);
  drawTimeline(snapshot);
  drawJobs(snapshot);
}

function refresh() {
  fetch(SNAPSHOT_URL)
    .then(function (response) {
      if (!response.ok) {
        throw new Error("snapshot unavailable");
      }
      offline = response.headers.get("X-Mission-Offline") === "1";
      return response.json();
    })
    .then(draw)
    .catch(function () {
      offline = true;
      if (lastSnapshot) {
        draw(lastSnapshot);
      } else {
        document.getElementById("status").textContent = "offline: no snapshot has been saved yet";
      }
    });
}

document.getElementById("view").addEventListener("change", function () {
  if (lastSnapshot) {
    drawTimeline(lastSnapshot);
  }
});

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("sw.js");
}
refresh();
setInterval(refresh, REFRESH_MS);
