"""Jules builder: sends the next directed batch to Google's Jules.

Owner request, 2026-11-25 16:21 America/Vancouver: "Find a way to produce the same
results maybe with software running on the site." Jules (free plan: 15 tasks a day,
3 at once) builds the batch in Google's cloud and opens the pull request. The
auto-merge gate then merges it when its checks are green, as for the Claude builder.

One batch at a time, in "Directed at:" order. No AI runs here: this file only reads
GitHub, copies the batch wording out of plan/QUEUE.md and sends it to Jules.
It needs the repository secret JULES_API_KEY (set only by the Owner) and never prints it.
It stops when an open issue title starts with STOP or a STOP file is on main.
Problems go to the Owner by email through the Daily status workflow, once per issue.
"""
import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

REPO = os.environ.get("GITHUB_REPOSITORY", "someonee12345678-hue/apccs")
OWNER = REPO.split("/")[0]
GH_TOKEN = os.environ.get("GH_TOKEN", "")
KEY = os.environ.get("JULES_API_KEY", "")
JULES = "https://jules.googleapis.com/v1alpha/"
BUSY, SENT, STUCK = "jules-working", "jules-pr-open", "jules-stuck"
HOLD = {"hold", "do-not-merge", "do not merge"}
WORK_HOURS, MERGE_HOURS = 8, 12
SESSION_MARK, PR_MARK = "<!-- jules-session: ", "<!-- jules-pr: "
MAX_TEXT = 90000


def call(url, method="GET", body=None, headers=None):
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
            return resp.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as err:
        return err.code, {"error": err.read().decode("utf-8", "replace")[:400]}


def gh(path, method="GET", body=None):
    return call("https://api.github.com/" + path, method, body,
                {"Authorization": "Bearer " + GH_TOKEN, "Accept": "application/vnd.github+json"})


def jules(path, method="GET", body=None):
    return call(JULES + path, method, body, {"X-Goog-Api-Key": KEY})


def labels(issue):
    return {lab.get("name", "").lower() for lab in issue.get("labels", [])}


def comment(num, text):
    gh(f"repos/{REPO}/issues/{num}/comments", "POST", {"body": text})


def add_label(num, name):
    gh(f"repos/{REPO}/issues/{num}/labels", "POST", {"labels": [name]})


def drop_label(num, name):
    gh(f"repos/{REPO}/issues/{num}/labels/{name}", "DELETE")


def problem(issue, lines):
    """Mark the issue stuck, explain on it, and email the Owner once."""
    num = issue["number"]
    if STUCK in labels(issue):
        return
    for name in (BUSY, SENT):
        if name in labels(issue):
            drop_label(num, name)
    add_label(num, STUCK)
    note = "\n".join(["Jules builder problem on #%d:" % num] + lines[:4])
    comment(num, note + "\n\nRemove the label `jules-stuck` to let the Jules builder try this issue again.")
    gh(f"repos/{REPO}/actions/workflows/daily-status.yml/dispatches", "POST",
       {"ref": "main", "inputs": {"note": note}})


def marker(num, mark):
    """Return (value, time) of the newest comment holding the marker, or (None, None)."""
    code, items = gh(f"repos/{REPO}/issues/{num}/comments?per_page=100")
    if code != 200:
        return None, None
    for item in reversed(items):
        body = item.get("body") or ""
        if mark in body:
            value = body.split(mark, 1)[1].split("-->", 1)[0].strip()
            return value, datetime.fromisoformat(item["created_at"].replace("Z", "+00:00"))
    return None, None


def order_key(issue):
    found = re.search(r"Directed at:\s*(\S+)", issue.get("body") or "")
    stamp = found.group(1) if found else issue["created_at"]
    try:
        when = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        when = datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00"))
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return when, issue["number"]


def section_end(lines, start, level):
    """Index of the next heading at this level or higher, after start."""
    for k in range(start + 1, len(lines)):
        match = re.match(r"(#+)\s", lines[k])
        if match and len(match.group(1)) <= level:
            return k
    return len(lines)


def batch_text(batch, issue_body, path="plan/QUEUE.md"):
    """Return (wording, target repository) for a batch, or ("", "") if not found."""
    with open(path, encoding="utf-8") as handle:
        lines = handle.read().split("\n")
    name = re.compile(r"\b" + re.escape(batch) + r"\b")
    starts = [k for k, line in enumerate(lines) if re.match(r"###\s+Batch\s+" + re.escape(batch) + r"\b", line)]
    if not starts:
        return "", ""
    start = starts[-1]
    end = start + 1
    while end < len(lines) and not (lines[end].startswith("## ") or re.match(r"###\s+Batch\s", lines[end])):
        end += 1
    parent = max((k for k in range(start) if lines[k].startswith("## ")), default=start)
    first_sub = next((k for k in range(parent + 1, start) if lines[k].startswith("### ")), start)
    parts = ["\n".join(lines[parent:min(first_sub, parent + 150)]), "\n".join(lines[start:end])]
    for k in range(end, len(lines)):
        match = re.match(r"(#{2,4})\s", lines[k])
        if match and name.search(lines[k]):
            parts.append("\n".join(lines[k:section_end(lines, k, len(match.group(1)))]))
    text = "\n\n".join(parts)[:MAX_TEXT]
    found = re.search(r"\*\*Target repository:\*\*\s*`?([\w.-]+/[\w.-]+)", "\n".join(lines[start:end]))
    if not found:
        found = re.search(r"target(?: repository)?:?\s*`?([\w.-]+/[\w.-]+)", issue_body or "", re.I)
    if found:
        target = found.group(1)
    else:
        short = re.search(r"\((apccs|uclrcde|omniguide|corolla-obd)\b", issue_body or "")
        target = f"{OWNER}/{short.group(1)}" if short else REPO
    return text, target


def prompt_for(batch, num, target, text):
    closes = f' and the line "Closes {REPO}#{num}"' if target == REPO else ""
    plan = ("The whole plan is in plan/QUEUE.md if the wording refers to a rule by name."
            if target == REPO else
            f"This repository can't see the plan repository ({REPO}); the parts of the plan this batch needs are quoted below.")
    return f"""Build one worded batch exactly as worded below: nothing more, nothing less.
Batch: {batch}. Target repository: {target} (this repository). Directed issue: {REPO}#{num}.

Rules that override anything else:
- Read AGENTS.md in this repository first and follow it.
- Add only the files the batch names. Never change or delete other files, and never touch .github/, tools/, AGENTS.md, CLAUDE.md, BUILDER_RUNBOOK.md, PROJECTS.md or plan/.
- Python standard library only. Made-up data only. No keys, passwords or personal details.
- Every instruction gets the normal-use test and the bad-input test its wording asks for. Run the repository's full test command from AGENTS.md and make it pass before you finish.
- Never invent wording beyond the batch. Where the wording leaves a choice, take the plainest reading and list it in the pull request description.
- Open one pull request against main titled "Batch {batch}: <a few words>". Description: one plain line per instruction, the test summary, the canary line, every place the wording left a choice{closes}.
{plan}

=== Batch wording, copied from {REPO} plan/QUEUE.md. Later corrections and audits that name this batch follow it; a later one wins where they differ. ===
{text}
"""


def follow_busy(issue, now):
    """Check the batch Jules is working on. Return True only if it is now stuck."""
    num = issue["number"]
    value, sent_at = marker(num, SESSION_MARK)
    if not value:
        problem(issue, ["It is marked as sent to Jules, but the session record is missing.",
                        "You need to do: nothing; remove the label jules-stuck to retry."])
        return True
    session, _, target = value.partition(" target=")
    code, data = jules(session)
    if code != 200:
        print(f"#{num}: Jules answered {code}; will check again next run.")
        return False
    pr_url = ""
    for out in data.get("outputs", []) or []:
        pr_url = (out.get("pullRequest") or {}).get("url") or pr_url
    state = str(data.get("state", ""))
    if pr_url:
        drop_label(num, BUSY)
        add_label(num, SENT)
        comment(num, f"Jules opened {pr_url}. The auto-merge gate merges it when its checks are green.\n{PR_MARK}{pr_url} -->")
        if target and target != REPO:
            gh(f"repos/{REPO}/issues/{num}", "PATCH", {"state": "closed"})
        return False
    if state == "AWAITING_PLAN_APPROVAL":
        jules(session + ":approvePlan", "POST", {})
        return False
    if "FAIL" in state or "AWAITING_USER" in state or now - sent_at > timedelta(hours=WORK_HOURS):
        problem(issue, [f"Jules session {session} is '{state or 'unknown'}' with no pull request after {WORK_HOURS} hours or less.",
                        "What I tried: sent it once and checked it every few hours.",
                        "You need to do: open jules.google.com and answer or restart that task, or remove the label jules-stuck to resend it."])
        return True
    print(f"#{num}: Jules is still working ({state or 'running'}).")
    return False


def send(issue):
    num = issue["number"]
    batch = re.match(r"Directed:\s*(\S+)", issue["title"]).group(1)
    text, target = batch_text(batch, issue.get("body") or "")
    if not text:
        problem(issue, [f"No wording headed 'Batch {batch}' was found in plan/QUEUE.md.",
                        "You need to do: nothing; the wording run or Claude fixes the plan."])
        return
    body = {"prompt": prompt_for(batch, num, target, text), "title": f"Batch {batch}",
            "sourceContext": {"source": f"sources/github/{target}", "githubRepoContext": {"startingBranch": "main"}},
            "automationMode": "AUTO_CREATE_PR"}
    code, data = jules("sessions", "POST", body)
    if code != 200:
        problem(issue, [f"Jules refused Batch {batch} for {target} (answer {code}).",
                        "If the answer says the source isn't found, the Jules GitHub app needs access to that repository.",
                        "You need to do: in jules.google.com, give the Jules app access to " + target + ", then remove the label jules-stuck."])
        print(str(data)[:300])
        return
    session = data.get("name") or ("sessions/" + str(data.get("id", "")))
    link = data.get("url", "")
    add_label(num, BUSY)
    comment(num, f"Sent Batch {batch} to Jules for {target}{(': ' + link) if link else '.'}\n{SESSION_MARK}{session} target={target} -->")
    print(f"#{num}: Batch {batch} sent to Jules for {target}.")


def main():
    if not KEY:
        print("The JULES_API_KEY secret isn't set yet, so nothing was sent.")
        return
    if os.path.exists("STOP"):
        print("STOP file on main.")
        return
    code, issues = gh(f"repos/{REPO}/issues?state=open&per_page=100")
    if code != 200:
        print(f"GitHub answered {code}.")
        return
    issues = [i for i in issues if "pull_request" not in i]
    if any(i["title"].strip().upper().startswith("STOP") for i in issues):
        print("Open STOP issue.")
        return
    directed = sorted((i for i in issues
                       if "directed" in labels(i) and i["user"]["login"] == OWNER
                       and re.match(r"Directed:\s*(?!OG-)\S+", i["title"]) and not labels(i) & HOLD),
                      key=order_key)
    now = datetime.now(timezone.utc)
    for issue in directed:
        tags = labels(issue)
        if STUCK in tags:
            continue
        if BUSY in tags:
            if not follow_busy(issue, now):
                return
            continue
        if SENT in tags:
            _, opened_at = marker(issue["number"], PR_MARK)
            if opened_at and now - opened_at > timedelta(hours=MERGE_HOURS):
                problem(issue, [f"Jules's pull request for #{issue['number']} isn't merged after {MERGE_HOURS} hours.",
                                "You need to do: nothing if Jules is fixing its checks; otherwise Claude looks at it after the reset."])
                continue
            print(f"#{issue['number']}: waiting for the gate to merge Jules's pull request.")
            return
        send(issue)
        return
    print("Nothing to send.")


if __name__ == "__main__":
    main()
