/* Toolbox screen of the more-screens page. Search the researched tools by feature, decision, licence,
   status and words. Text goes in with textContent and createElement. */
"use strict";

(function () {
  var FIELDS = [
    ["feature", "Feature (1 to 12, or part of its name)"],
    ["decision", "Decision (Adopt now, Adopt later, Borrow the idea, Not used, NOT CHECKED)"],
    ["licence", "Licence (part of its name)"],
    ["status", "Status mark"],
    ["words", "Words (all must appear in ability, tool, branch or overlaps)"]
  ];
  var api = null;
  var inputs = {};
  var message = null;
  var counts = null;
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

  function resultLine(row) {
    var source = row.source_row ? " [" + row.source_row + "]" : "";
    return row.feature + " › " + row.branch + ": " + row.ability + " — " + row.tool + source +
      " · licence " + row.licence + " · " + row.decision_word + " " + row.status;
  }

  function showCounts(body) {
    clear(counts);
    addItem(counts, body.total + " rows match.");
    Object.keys(body.counts.by_decision).forEach(function (word) {
      addItem(counts, word + ": " + body.counts.by_decision[word]);
    });
    addItem(counts, "Licences still to check: " + body.counts.licences_to_check);
    if (body.source_note) {
      addItem(counts, "Copy: " + body.source_note + " (given " + body.at + ")");
    }
  }

  function showResults(body) {
    clear(results);
    if (body.status !== "OK") {
      message.textContent = body.status + ": " + (body.reason || "nothing to show.");
      clear(counts);
      return;
    }
    message.textContent = "Showing " + body.shown + " of " + body.total + ".";
    showCounts(body);
    body.results.forEach(function (row) { addItem(results, resultLine(row)); });
  }

  function showProblem(error) {
    message.textContent = "offline or refused: " + error.message;
  }

  function search() {
    var query = new URLSearchParams();
    Object.keys(inputs).forEach(function (name) {
      if (inputs[name].value.trim()) {
        query.set(name, inputs[name].value.trim());
      }
    });
    api.get("search?" + query.toString()).then(showResults).catch(showProblem);
  }

  function load() {
    api.post("load", {}).then(function (body) {
      message.textContent = "Loaded " + body.rows + " rows.";
      return api.get("summary");
    }).then(showResults).catch(showProblem);
  }

  function addField(root, name, labelText) {
    var wrapper = element("div");
    var label = element("label", labelText);
    var input = element("input");
    input.type = "text";
    input.id = "toolbox-" + name;
    label.htmlFor = input.id;
    wrapper.appendChild(label);
    wrapper.appendChild(input);
    root.appendChild(wrapper);
    inputs[name] = input;
  }

  function mount(section, panelApi) {
    api = panelApi;
    section.appendChild(element("h2", "Toolbox"));
    section.appendChild(element("p", "Search the researched tools and abilities. Nothing here is fetched; it reads the copy you gave."));
    FIELDS.forEach(function (field) { addField(section, field[0], field[1]); });
    var searchButton = element("button", "Search");
    searchButton.type = "button";
    searchButton.addEventListener("click", search);
    var loadButton = element("button", "Load the saved copy");
    loadButton.type = "button";
    loadButton.addEventListener("click", load);
    section.appendChild(searchButton);
    section.appendChild(loadButton);
    message = element("p", "Not searched yet.");
    message.setAttribute("role", "status");
    counts = element("ul");
    results = element("ul");
    section.appendChild(message);
    section.appendChild(counts);
    section.appendChild(results);
  }

  window.apccsMore.register("toolbox", mount);
}());
