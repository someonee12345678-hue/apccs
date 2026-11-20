/* Control panel page. It talks only to relative /api/panel/ addresses. Text goes into the page
   only with textContent and createElement. Later screens plug in with window.apccsPanel.register. */
"use strict";

var API_BASE = "/api/panel/";
var SCREEN_ID_PATTERN = /^[a-z]+$/;
var mounts = {};
var screenSections = {};

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

function showStatus(text, offline) {
  var line = document.getElementById("status");
  line.textContent = text;
  line.className = offline ? "offline" : "";
}

function readReply(response) {
  var offline = response.headers.get("X-Panel-Offline") === "1";
  return response.json().then(function (body) {
    if (!response.ok) {
      throw new Error(body.reason || "the panel refused the request");
    }
    if (offline) {
      showStatus("offline: showing the last answers", true);
    }
    return body;
  });
}

function getJson(path) {
  return fetch(API_BASE + path).then(readReply);
}

function postJson(path, body) {
  return fetch(API_BASE + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  }).then(readReply);
}

function register(screenId, mount) {
  if (!SCREEN_ID_PATTERN.test(screenId) || typeof mount !== "function") {
    return;
  }
  mounts[screenId] = mount;
  var section = screenSections[screenId];
  if (section) {
    clear(section);
    mount(section, {
      get: function (path) { return getJson(screenId + "/" + path); },
      post: function (path, body) { return postJson(screenId + "/" + path, body); }
    });
  }
}

window.apccsPanel = { register: register };

function selectTab(name) {
  ["home", "projects"].forEach(function (tab) {
    var shown = tab === name;
    document.getElementById("tab-" + tab).hidden = !shown;
    document.getElementById("button-" + tab).setAttribute("aria-selected", shown ? "true" : "false");
  });
}

function showInstall(result) {
  document.getElementById("install-line").textContent = result.line;
}

function showHistory(body) {
  var list = document.getElementById("install-history");
  clear(list);
  body.checks.forEach(function (row) {
    addItem(list, row.at + ": " + row.decision + " (version " + row.version + ")");
  });
}

function showProjects(body) {
  var list = document.getElementById("project-list");
  clear(list);
  body.projects.forEach(function (project) {
    var ready = project.ready ? "ready for the builder" : "not ready for the builder";
    addItem(list, project.name + " - " + project.repository + (project.private ? " (private)" : "") + " - " + ready);
  });
}

function showTools(body) {
  var result = document.getElementById("tools-result");
  var steps = document.getElementById("tools-steps");
  clear(result);
  clear(steps);
  body.tools.forEach(function (tool) {
    addItem(result, tool.tool + ": " + (tool.present ? "present" : "missing"));
  });
  body.next_steps.forEach(function (line) {
    addItem(steps, line);
  });
}

function reportProblem(error) {
  showStatus("offline or refused: " + error.message, true);
}

function loadScreen(screen) {
  if (!SCREEN_ID_PATTERN.test(screen.screen_id)) {
    return;
  }
  var section = document.getElementById("screen-" + screen.screen_id);
  if (!section) {
    return;
  }
  screenSections[screen.screen_id] = section;
  if (!screen.built) {
    clear(section);
    var note = document.createElement("p");
    note.textContent = "The " + screen.title + " screen is not built yet (batch " + screen.batch + ").";
    section.appendChild(note);
    return;
  }
  var script = document.createElement("script");
  script.src = "screen_" + screen.screen_id + ".js";
  document.body.appendChild(script);
}

function start() {
  document.getElementById("button-home").addEventListener("click", function () { selectTab("home"); });
  document.getElementById("button-projects").addEventListener("click", function () { selectTab("projects"); });
  document.getElementById("check-install").addEventListener("click", function () {
    postJson("home/install_check", {}).then(showInstall).then(function () {
      return getJson("home/checks");
    }).then(showHistory).catch(reportProblem);
  });
  document.getElementById("check-tools").addEventListener("click", function () {
    postJson("home/tools", { listing: document.getElementById("tools-listing").value })
      .then(showTools).catch(reportProblem);
  });
  getJson("home/projects").then(showProjects).catch(reportProblem);
  getJson("home/checks").then(showHistory).catch(reportProblem);
  getJson("screens").then(function (body) {
    body.screens.forEach(loadScreen);
    showStatus("Ready.", false);
  }).catch(reportProblem);
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("sw.js").catch(function () { return null; });
  }
}

start();
