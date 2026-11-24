/* More screens page. It talks only to relative /api/more/ addresses. Text goes into the page
   only with textContent and createElement. Each screen plugs in with window.apccsMore.register. */
"use strict";

var API_BASE = "/api/more/";
var SCREENS_URL = "/api/more/screens";
var SCREEN_ID_PATTERN = /^[a-z]+$/;
var mounts = {};
var screenSections = {};
var screenButtons = {};

function clear(node) {
  while (node.firstChild) {
    node.removeChild(node.firstChild);
  }
}

function showStatus(text) {
  document.getElementById("status").textContent = text;
}

function readReply(response) {
  return response.json().then(function (body) {
    if (!response.ok) {
      throw new Error(body.reason || "the panel refused the request");
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

window.apccsMore = { register: register };

function selectScreen(name) {
  Object.keys(screenSections).forEach(function (id) {
    var shown = id === name;
    screenSections[id].hidden = !shown;
    screenButtons[id].setAttribute("aria-selected", shown ? "true" : "false");
  });
}

function addScreen(screen, first) {
  if (!SCREEN_ID_PATTERN.test(screen.screen_id)) {
    return;
  }
  var button = document.createElement("button");
  button.type = "button";
  button.id = "button-" + screen.screen_id;
  button.textContent = screen.title;
  button.setAttribute("aria-controls", "more-" + screen.screen_id);
  button.setAttribute("aria-selected", "false");
  button.addEventListener("click", function () { selectScreen(screen.screen_id); });
  document.getElementById("tabs").appendChild(button);
  var section = document.createElement("section");
  section.id = "more-" + screen.screen_id;
  section.hidden = !first;
  document.getElementById("screens").appendChild(section);
  screenButtons[screen.screen_id] = button;
  screenSections[screen.screen_id] = section;
  if (!screen.built) {
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
  fetch(SCREENS_URL).then(readReply).then(function (body) {
    body.screens.forEach(function (screen, index) { addScreen(screen, index === 0); });
    if (body.screens.length) {
      selectScreen(body.screens[0].screen_id);
    }
    showStatus("Ready.");
  }).catch(function (error) {
    showStatus("offline or refused: " + error.message);
  });
}

start();
