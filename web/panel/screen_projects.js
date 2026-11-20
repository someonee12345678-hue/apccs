/* Projects screen of the control panel. One button per project; the data of the chosen project is shown
   only under its own button, so projects never mix. Text goes in with textContent and createElement. */
"use strict";

(function () {
  var VIEWS = ["summary", "full", "milestones", "chronological"];
  var api = null;
  var root = null;
  var detail = null;
  var chosen = null;

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

  function heading(text) {
    return element("h3", text);
  }

  function notChecked(part) {
    var note = element("p", "NOT CHECKED: " + (part.reason || "no data was given."));
    return note;
  }

  function showHistory(part) {
    var box = element("div");
    box.appendChild(heading("Batch history"));
    if (part.status !== "OK") {
      box.appendChild(notChecked(part));
      return box;
    }
    var list = element("ul");
    part.data.lines.forEach(function (line) { addItem(list, line); });
    part.data.open.forEach(function (row) {
      addItem(list, "Batch " + row.batch_id + " is open (PR #" + row.pr_number + ").");
    });
    if (!list.firstChild) {
      addItem(list, "No batches yet.");
    }
    box.appendChild(list);
    return box;
  }

  function recordLines(record) {
    return Object.keys(record).map(function (name) { return name + ": " + record[name]; }).join(" | ");
  }

  function fillLog(list, part) {
    clear(list);
    if (part.status !== "OK") {
      addItem(list, "NOT CHECKED: " + (part.reason || "no log was given."));
      return;
    }
    part.data.records.forEach(function (record) { addItem(list, recordLines(record)); });
    part.data.bad_records.forEach(function (bad) {
      addItem(list, "Record " + bad.record_number + " was not used: " + bad.reason);
    });
    if (!list.firstChild) {
      addItem(list, "No records match.");
    }
  }

  function showLog(project, part) {
    var box = element("div");
    box.appendChild(heading("Log"));
    var viewLabel = element("label", "Log view");
    viewLabel.setAttribute("for", "log-view");
    var select = element("select");
    select.id = "log-view";
    VIEWS.forEach(function (view) {
      var option = element("option", view);
      option.value = view;
      select.appendChild(option);
    });
    var tagLabel = element("label", "Search by tag");
    tagLabel.setAttribute("for", "log-tag");
    var tag = element("input");
    tag.id = "log-tag";
    tag.type = "text";
    var button = element("button", "Show the log");
    button.type = "button";
    var list = element("ul");
    button.addEventListener("click", function () {
      var query = "log?id=" + encodeURIComponent(project) + "&view=" + encodeURIComponent(select.value)
        + "&tag=" + encodeURIComponent(tag.value);
      api.get(query).then(function (answer) { fillLog(list, answer); }).catch(function (error) {
        clear(list);
        addItem(list, "offline or refused: " + error.message);
      });
    });
    [viewLabel, select, tagLabel, tag, button, list].forEach(function (node) { box.appendChild(node); });
    fillLog(list, part);
    return box;
  }

  function showProgress(part) {
    var box = element("div");
    box.appendChild(heading("Progress and predicted finish"));
    if (part.status !== "OK") {
      box.appendChild(notChecked(part));
      return box;
    }
    box.appendChild(element("p", part.data.line));
    var list = element("ul");
    part.data.per_project.forEach(function (row) {
      addItem(list, row.project_id + ": built " + row.built + ", ready " + row.ready + ", worded " + row.worded
        + ", not worded " + row.not_worded + ", finish " + (row.finish_date || "no estimate"));
    });
    part.data.no_estimate.forEach(function (row) {
      addItem(list, "No estimate for " + row.batch_id + ": " + row.reason);
    });
    box.appendChild(list);
    return box;
  }

  function showLabels(part) {
    var box = element("div");
    box.appendChild(heading("Label check"));
    if (part.status !== "OK") {
      box.appendChild(notChecked(part));
    } else {
      box.appendChild(element("p", part.data.line));
    }
    return box;
  }

  function showRunCommand(command) {
    var box = element("div");
    box.appendChild(heading("Run command"));
    var code = element("p", command);
    code.id = "run-command";
    var copy = element("button", "Copy");
    copy.type = "button";
    copy.addEventListener("click", function () {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(command).then(function () { copy.textContent = "Copied"; });
      }
    });
    box.appendChild(code);
    box.appendChild(copy);
    return box;
  }

  function showProject(project, view) {
    clear(detail);
    detail.appendChild(element("h3", "Project: " + project));
    detail.appendChild(showRunCommand(view.run_command));
    detail.appendChild(showHistory(view.history));
    detail.appendChild(showLog(project, view.log));
    detail.appendChild(showProgress(view.progress));
    detail.appendChild(showLabels(view.labels));
  }

  function choose(project, button, buttons) {
    chosen = project;
    buttons.forEach(function (other) { other.setAttribute("aria-pressed", other === button ? "true" : "false"); });
    api.get("project?id=" + encodeURIComponent(project)).then(function (view) {
      if (chosen === project) {
        showProject(project, view);
      }
    }).catch(function (error) {
      clear(detail);
      detail.appendChild(element("p", "offline or refused: " + error.message));
    });
  }

  function showList(body) {
    var bar = element("div");
    var buttons = [];
    body.projects.forEach(function (project) {
      var button = element("button", project.name);
      button.type = "button";
      button.setAttribute("aria-pressed", "false");
      button.addEventListener("click", function () { choose(project.project_id, button, buttons); });
      if (!project.has_switcher_data) {
        button.textContent = project.name + " (no data yet)";
      }
      buttons.push(button);
      bar.appendChild(button);
    });
    root.appendChild(bar);
    detail = element("div");
    root.appendChild(detail);
  }

  function mount(section, panelApi) {
    root = section;
    api = panelApi;
    clear(root);
    root.appendChild(element("p", "Choose a project. Each project's data is kept apart."));
    api.get("list").then(showList).catch(function (error) {
      root.appendChild(element("p", "offline or refused: " + error.message));
    });
  }

  window.apccsPanel.register("projects", mount);
}());
