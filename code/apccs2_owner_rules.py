"""Owner's standing rules that plain code can check (plan/RULEBOOK.md items 19 on).

Inputs: the text of GitHub workflow files.
Outputs: lists of rule breaks, each naming the file and the rule.
Errors: unreadable text gives no triggers, which counts as a break only when a
schedule is found.
"""
import re

# Rule 19 allows one planned clock: the daily progress email (Owner, 13 Nov 13:44).
CLOCK_ALLOWED = {"daily-status.yml": "one progress email a day (Owner, 13 Nov 13:44)"}
MANUAL_ONLY = {"schedule", "workflow_dispatch"}


def workflow_triggers(text: str) -> set[str]:
    """Return the trigger names under a workflow's top-level `on:` key.

    Inputs: workflow file text.
    Outputs: set of trigger names such as {"issues", "schedule"}.
    Errors: none; a file without `on:` gives an empty set.
    """
    triggers: set[str] = set()
    inside = False
    for line in text.splitlines():
        top = re.match(r"^on:\s*(.*)$", line)
        if top:
            rest = top.group(1).split("#", 1)[0].strip()
            if rest:
                return set(re.findall(r"[a-z_]+", rest))
            inside = True
            continue
        if inside:
            if line.strip() and not line.startswith((" ", "\t", "#")):
                break
            key = re.match(r"^\s{2}([a-z_]+):", line)
            if key:
                triggers.add(key.group(1))
    return triggers


def clock_breaks(files: dict[str, str]) -> list[str]:
    """Rule 19, events not clocks: list workflows started only by a clock.

    Inputs: {file name: workflow text}.
    Outputs: one plain line per workflow whose only automatic start is a schedule,
    unless the file is in CLOCK_ALLOWED.
    Errors: none.
    """
    breaks = []
    for name, text in sorted(files.items()):
        triggers = workflow_triggers(text)
        if "schedule" in triggers and not (triggers - MANUAL_ONLY) and name not in CLOCK_ALLOWED:
            breaks.append(f"{name}: starts only on a clock; add the event that should start it (RULEBOOK item 19)")
    return breaks
