/* Projects screen of the control panel. It plugs in with window.apccsPanel.register and talks only to
   relative /api/panel/projects/ addresses through the api object it is given. Text goes into the page only
   with textContent and createElement. Each project's data is shown only under its own button. */
"use strict";

var LOG_VIEWS = ["summary", "full", "milestones", "chronological"];

function clearNode(node) {
  while (node.firstChild) {
    node.removeChild(node.firstChild);
  }
}

function addLine(parent, tag, text) {
  var node = document.createElement(tag);
  node.textContent = text;
  parent.appendChild(node);
  return node;
}

function addList(parent, lines) {
  var list = document.createElement("ul");
  lines.forEach(function (line) {
    addLine(list, "li", line);
  });
  parent.appendChild(list);
}

function partNote(part) {
  return part.status + ": " + (part.reason || "");
}

function copyCommand(command, note) {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(command).then(function () {
      note.textContent = "Copied.";
    }, function () {
      note.textContent = "Could not copy. Select the command and copy it.";
    });
  } else {
    note.textContent = "Could not copy. Select the command and copy it.";
  }
}

function showRunCommand(area, command) {
  addLine(area, "h3", "Run the tests");
  addLine(area, "p", command);
  var button = addLine(area, "button", "Copy");
  button.type = "button";
  var note = addLine(area, "p", "");
  note.setAttribute("role", "status");
  button.addEventListener("click", function () {
    copyCommand(command, note);
  });
}

function showHistory(area, history) {
  addLine(area, "h3", "Batch history");
  if (history.status !== "CHECKED") {
    addLine(area, "p", partNote(history));
    return;
  }
  addLine(area, "p", history.counts.merged + " merged, " + history.counts.open + " open.");
  addList(area, history.lines);
  addList(area, history.open.map(function (row) {
    return "Batch " + row.batch_id + " is open (PR #" + row.pr_number + ").";
  }));
}

function recordLines(record) {
  return Object.keys(record).map(function (name) {
    return name + ": " + record[name];
  });
}

function showLogResult(target, answer) {
  clearNode(target);
  if (answer.status !== "CHECKED") {
    addLine(target, "p", partNote(answer));
    return;
  }
  addLine(target, "p", answer.count + " records shown in the " + answer.view + " view.");
  answer.records.forEach(function (record) {
    addList(target, recordLines(record));
  });
  answer.bad_records.forEach(function (bad) {
    addLine(target, "p", "Record " + bad.place + " is not in the Owner's format: " + bad.reason);
  });
}

function showLog(area, projectId, api) {
  addLine(area, "h3", "Log");
  var viewLabel = addLine(area, "label", "Log view");
  viewLabel.htmlFor = "log-view";
  var picker = document.createElement("select");
  picker.id = "log-view";
  picker.style.fontSize = "16px";
  LOG_VIEWS.forEach(function (name) {
    var option = document.createElement("option");
    option.value = name;
    option.textContent = name;
    picker.appendChild(option);
  });
  area.appendChild(picker);
  var tagLabel = addLine(area, "label", "Search by tag");
  tagLabel.htmlFor = "log-tag";
  var tagBox = document.createElement("input");
  tagBox.id = "log-tag";
  tagBox.type = "text";
  tagBox.maxLength = 60;
  tagBox.style.fontSize = "16px";
  tagBox.style.maxWidth = "100%";
  area.appendChild(tagBox);
  var go = addLine(area, "button", "Show the log");
  go.type = "button";
  var target = document.createElement("div");
  area.appendChild(target);
  function load() {
    var path = "log?id=" + encodeURIComponent(projectId) + "&view=" + encodeURIComponent(picker.value);
    if (tagBox.value) {
      path += "&tag=" + encodeURIComponent(tagBox.value);
    }
    api.get(path).then(function (answer) {
      showLogResult(target, answer);
    }).catch(function (error) {
      clearNode(target);
      addLine(target, "p", "offline or refused: " + error.message);
    });
  }
  go.addEventListener("click", load);
  load();
}

function showProgress(area, progress) {
  addLine(area, "h3", "Progress and predicted finish");
  if (progress.status !== "CHECKED") {
    addLine(area, "p", partNote(progress));
    return;
  }
  addLine(area, "p", progress.line);
  if (progress.project) {
    var row = progress.project;
    addLine(area, "p", "Built " + row.built + ", ready " + row.ready + ", worded " + row.worded +
      ", not worded " + row.not_worded + ". Finish: " + (row.finish_date || "no estimate") + ".");
  }
  addList(area, progress.no_estimate.map(function (item) {
    return "No estimate for " + item.batch_id + ": " + item.reason + ".";
  }));
}

function showLabels(area, labels) {
  addLine(area, "h3", "Built-in label check");
  if (labels.line) {
    addLine(area, "p", labels.status + ": " + labels.line);
  } else {
    addLine(area, "p", partNote(labels));
  }
}

function showProject(area, projectId, api) {
  clearNode(area);
  api.get("project?id=" + encodeURIComponent(projectId)).then(function (project) {
    addLine(area, "h2", projectId);
    showRunCommand(area, project.run_command);
    showHistory(area, project.history);
    showLog(area, projectId, api);
    showProgress(area, project.progress);
    showLabels(area, project.labels);
  }).catch(function (error) {
    addLine(area, "p", "offline or refused: " + error.message);
  });
}

function mount(section, api) {
  clearNode(section);
  var buttons = document.createElement("div");
  var area = document.createElement("div");
  section.appendChild(buttons);
  section.appendChild(area);
  api.get("list").then(function (answer) {
    answer.projects.forEach(function (project) {
      var button = addLine(buttons, "button", project.name + (project.has_data ? "" : " (no saved data)"));
      button.type = "button";
      button.addEventListener("click", function () {
        showProject(area, project.id, api);
      });
    });
    addLine(area, "p", "Choose a project above.");
  }).catch(function (error) {
    addLine(area, "p", "offline or refused: " + error.message);
  });
}

window.apccsPanel.register("projects", mount);
