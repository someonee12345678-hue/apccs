/* Logs screen of the more-screens page. One search and one timeline across every project's log.
   Text goes in with textContent and createElement. Each project keeps its own heading. */
"use strict";

(function () {
  var AGENTS = ["GE", "MU", "CG", "CL", "MI"];
  var VIEWS = ["summary", "full", "milestones", "chronological"];
  var TEXT_FIELDS = [
    ["words", "Words (every word must appear, up to 5)"],
    ["tag", "Tag (for example SG-1)"]
  ];
  var DATE_FIELDS = [
    ["since", "Since (YYYY-MM-DD)"],
    ["until", "Until (YYYY-MM-DD)"]
  ];
  var api = null;
  var inputs = {};
  var viewPicker = null;
  var agentBoxes = {};
  var message = null;
  var results = null;

  function clear(node) {
    while (node.firstChild) {
      node.removeChild(node.firstChild);
    }
  }

  function element(name, text) {
    var node = document.createElement(name);
    if (text !== undefined) {
      node.textContent = text;
    }
    return node;
  }

  function addItem(list, text) {
    list.appendChild(element("li", text));
  }

  function recordLine(record) {
    return Object.keys(record).map(function (name) {
      return name + ": " + record[name];
    }).join(" | ");
  }

  function showGroups(body) {
    clear(results);
    message.textContent = body.total + " records match.";
    body.groups.forEach(function (group) {
      results.appendChild(element("h3", group.project_id + " (" + group.count + ")"));
      var list = element("ul");
      group.records.forEach(function (record) { addItem(list, recordLine(record)); });
      results.appendChild(list);
    });
  }

  function showTimeline(body) {
    clear(results);
    message.textContent = "Showing " + body.shown + " of " + body.count + ".";
    var list = element("ul");
    body.lines.forEach(function (line) { addItem(list, line); });
    results.appendChild(list);
  }

  function showProblem(error) {
    message.textContent = "offline or refused: " + error.message;
  }

  function checkedAgents() {
    return AGENTS.filter(function (code) { return agentBoxes[code].checked; });
  }

  function search() {
    var query = new URLSearchParams();
    ["words", "tag", "since", "until"].forEach(function (name) {
      if (inputs[name].value.trim()) {
        query.set(name, inputs[name].value.trim());
      }
    });
    query.set("view", viewPicker.value);
    if (checkedAgents().length) {
      query.set("agents", checkedAgents().join(","));
    }
    api.get("search?" + query.toString()).then(showGroups).catch(showProblem);
  }

  function timeline() {
    var view = viewPicker.value === "milestones" || viewPicker.value === "chronological" ? viewPicker.value : "milestones";
    api.get("timeline?view=" + view).then(showTimeline).catch(showProblem);
  }

  function addField(root, name, labelText, kind) {
    var wrapper = element("div");
    var label = element("label", labelText);
    var input = element("input");
    input.type = kind;
    input.id = "logs-" + name;
    label.htmlFor = input.id;
    wrapper.appendChild(label);
    wrapper.appendChild(input);
    root.appendChild(wrapper);
    inputs[name] = input;
  }

  function addViewPicker(root) {
    var wrapper = element("div");
    var label = element("label", "View");
    viewPicker = element("select");
    viewPicker.id = "logs-view";
    label.htmlFor = viewPicker.id;
    VIEWS.forEach(function (name) {
      var option = element("option", name);
      option.value = name;
      viewPicker.appendChild(option);
    });
    wrapper.appendChild(label);
    wrapper.appendChild(viewPicker);
    root.appendChild(wrapper);
  }

  function addAgentBoxes(root) {
    var group = element("div");
    group.appendChild(element("p", "Agents (none ticked means all)"));
    AGENTS.forEach(function (code) {
      var box = element("input");
      box.type = "checkbox";
      box.id = "logs-agent-" + code;
      var label = element("label", code);
      label.htmlFor = box.id;
      group.appendChild(box);
      group.appendChild(label);
      agentBoxes[code] = box;
    });
    root.appendChild(group);
  }

  function addButton(root, text, action) {
    var button = element("button", text);
    button.type = "button";
    button.addEventListener("click", action);
    root.appendChild(button);
  }

  function mount(section, panelApi) {
    api = panelApi;
    section.appendChild(element("h2", "Logs"));
    section.appendChild(element("p", "Search every project's log at once, or see one timeline. Each project stays under its own name."));
    TEXT_FIELDS.forEach(function (field) { addField(section, field[0], field[1], "text"); });
    addViewPicker(section);
    DATE_FIELDS.forEach(function (field) { addField(section, field[0], field[1], "text"); });
    addAgentBoxes(section);
    addButton(section, "Search", search);
    addButton(section, "Timeline", timeline);
    message = element("p", "Not searched yet.");
    message.setAttribute("role", "status");
    results = element("div");
    section.appendChild(message);
    section.appendChild(results);
  }

  window.apccsMore.register("logs", mount);
}());
