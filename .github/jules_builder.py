"""Jules builder: sends the next directed batch to Google's Jules.

Owner request, 2026-11-25 16:21 America/Vancouver: "Find a way to produce the same
results maybe with software running on the site." Jules (free plan: 15 tasks a day,
3 at once) builds the batch in Google's cloud and opens the pull request. The
auto-merge gate then merges it when its checks are green, as for the Claude builder.
One batch at a time per target repository, in "Directed at:" order. No AI runs here.
Added 2026-11-25 23:19 (Owner: "Can't you manage everything better faster without
using your limited so fast"): a second lane, the Jules task inbox. Any issue the Owner's
account opens with the label `jules-task` is sent to Jules as written, one at a time,
on the repository named in a "Repository: owner/repo" line (default: this one), one at a time. Claude
runs, Gemini or the Owner hand heavy reading, auditing or coding work to Jules this way.

Inputs: GitHub issues labelled `directed` or `jules-task`, plan/QUEUE.md, and the environment values
GITHUB_REPOSITORY, GH_TOKEN and JULES_API_KEY (the key is set only by the Owner and
is never printed).
Outputs: at most one new Jules session per run, labels and comments on the directed
issue, and at most one problem email per issue through the Daily status workflow.
Errors: a missing key, a STOP issue or a STOP file ends the run in one line; GitHub or
Jules answers other than success are reported on the issue, never raised.
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
SOURCES: list[str] = []
BUSY, SENT, STUCK, TASK = "jules-working", "jules-pr-open", "jules-stuck", "jules-task"
HOLD = {"hold", "do-not-merge", "do not merge"}
WORK_HOURS, MERGE_HOURS = 8, 12
SESSION_MARK, PR_MARK = "<!-- jules-session: ", "<!-- jules-pr: "
MAX_TEXT = 90000
# The Owner's Jules account is on the free basic plan (his screenshot, 2026-11-26 00:19):
# 15 tasks a day, 3 at once. Batches run one per target repository (apccs and uclrcde, so at
# most 2) and the task inbox one at a time, so no more than 3 run together.
MAX_TASKS = 1


def call(url: str, method: str = "GET", body: dict | None = None, headers: dict | None = None) -> tuple[int, object]:
    """Send one HTTPS request.

    Inputs: url, method, optional JSON body and headers.
    Outputs: (status code, parsed JSON or an {"error": text} dict).
    Errors: HTTP errors are returned as their code, not raised.
    """
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
            return resp.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as err:
        return err.code, {"error": err.read().decode("utf-8", "replace")[:400]}


def gh(path: str, method: str = "GET", body: dict | None = None) -> tuple[int, object]:
    """Call the GitHub REST API with this run's own short-lived token.

    Inputs: API path after https://api.github.com/, method, optional body.
    Outputs: (status code, parsed JSON).
    Errors: none raised; see call().
    """
    return call("https://api.github.com/" + path, method, body,
                {"Authorization": "Bearer " + GH_TOKEN, "Accept": "application/vnd.github+json"})


def jules(path: str, method: str = "GET", body: dict | None = None) -> tuple[int, object]:
    """Call the Jules API with the Owner's key.

    Inputs: path after the v1alpha base, method, optional body.
    Outputs: (status code, parsed JSON).
    Errors: none raised; see call().
    """
    return call(JULES + path, method, body, {"X-Goog-Api-Key": KEY})


def candidate_keys() -> list[str]:
    """List every saved Jules key, so a key saved under another name still works.

    Inputs: environment values JULES_KEYS (one per line) and JULES_API_KEY.
    Outputs: distinct non-empty keys, in the order given.
    Errors: none; nothing saved gives [].
    """
    found = [line.strip() for line in os.environ.get("JULES_KEYS", "").splitlines() if line.strip()]
    found.append(os.environ.get("JULES_API_KEY", "").strip())
    unique: list[str] = []
    for key in found:
        if key and key not in unique:
            unique.append(key)
    return unique


def choose_key() -> tuple[list[str], int]:
    """Try each saved key against Jules and keep the first one Jules accepts.

    Inputs: the candidate keys.
    Outputs: (source names Jules can see, last answer code); sets KEY, or "" if none works.
    Errors: none raised; a refused key is skipped.
    """
    global KEY
    last = 0
    for key in candidate_keys():
        KEY = key
        code, data = jules("sources?pageSize=100")
        last = code
        if code == 200:
            return [src.get("name", "") for src in data.get("sources", []) or []], code
    KEY = ""
    return [], last


def labels(issue: dict) -> set[str]:
    """Return the issue's label names in lower case.

    Inputs: a GitHub issue record.
    Outputs: set of label names.
    Errors: none; missing labels give an empty set.
    """
    return {lab.get("name", "").lower() for lab in issue.get("labels", [])}


def comment(num: int, text: str) -> None:
    """Post one comment on an issue.

    Inputs: issue number and text.
    Outputs: none.
    Errors: GitHub refusals are ignored.
    """
    gh(f"repos/{REPO}/issues/{num}/comments", "POST", {"body": text})


def add_label(num: int, name: str) -> None:
    """Add one label to an issue.

    Inputs: issue number and label name.
    Outputs: none.
    Errors: GitHub refusals are ignored.
    """
    gh(f"repos/{REPO}/issues/{num}/labels", "POST", {"labels": [name]})


def drop_label(num: int, name: str) -> None:
    """Remove one label from an issue.

    Inputs: issue number and label name.
    Outputs: none.
    Errors: GitHub refusals are ignored.
    """
    gh(f"repos/{REPO}/issues/{num}/labels/{name}", "DELETE")


def problem(issue: dict, lines: list[str]) -> None:
    """Mark the issue stuck, explain on it, and email the Owner once.

    Inputs: the directed issue and up to four plain lines.
    Outputs: label jules-stuck, one comment, one Daily status email.
    Errors: an issue already marked stuck is left alone, so it never emails twice.
    """
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


def marker(num: int, mark: str) -> tuple[str | None, datetime | None]:
    """Find the newest comment holding a marker.

    Inputs: issue number and marker text.
    Outputs: (value after the marker, comment time), or (None, None).
    Errors: a GitHub refusal gives (None, None).
    """
    code, items = gh(f"repos/{REPO}/issues/{num}/comments?per_page=100")
    if code != 200:
        return None, None
    for item in reversed(items):
        body = item.get("body") or ""
        if mark in body:
            value = body.split(mark, 1)[1].split("-->", 1)[0].strip()
            return value, datetime.fromisoformat(item["created_at"].replace("Z", "+00:00"))
    return None, None


def order_key(issue: dict) -> tuple[datetime, int]:
    """Sort key: the issue's "Directed at:" time, else its creation time.

    Inputs: a GitHub issue record.
    Outputs: (time with zone, issue number).
    Errors: an unreadable time falls back to the creation time.
    """
    found = re.search(r"Directed at:\s*(\S+)", issue.get("body") or "")
    stamp = found.group(1) if found else issue["created_at"]
    try:
        when = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        when = datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00"))
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return when, issue["number"]


def section_end(lines: list[str], start: int, level: int) -> int:
    """Find where a heading's section ends.

    Inputs: plan lines, the heading's index and its level (number of #).
    Outputs: index of the next heading at this level or higher, or the line count.
    Errors: none.
    """
    for k in range(start + 1, len(lines)):
        match = re.match(r"(#+)\s", lines[k])
        if match and len(match.group(1)) <= level:
            return k
    return len(lines)


def batch_text(batch: str, issue_body: str, path: str = "plan/QUEUE.md") -> tuple[str, str]:
    """Copy a batch's wording and find its target repository.

    Inputs: batch name, the directed issue's body, and the plan path.
    Outputs: (parent intro + newest batch section + later headings naming the batch,
    target "owner/repo"), or ("", "") when no "### Batch <name>" heading exists.
    Errors: a missing plan file raises OSError, which fails the run visibly.
    """
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


def prompt_for(batch: str, num: int, target: str, text: str) -> str:
    """Build the task text Jules receives.

    Inputs: batch name, directed issue number, target repository, batch wording.
    Outputs: the full task text, rules first and wording last.
    Errors: none.
    """
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


def follow_busy(issue: dict, now: datetime) -> bool:
    """Check the batch Jules is working on.

    Inputs: the directed issue marked jules-working and the current time.
    Outputs: True only if the issue is now stuck (so the next batch may be sent).
    Errors: a Jules answer other than 200 waits for the next run.
    """
    num = issue["number"]
    value, sent_at = marker(num, SESSION_MARK)
    if not value or sent_at is None:
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
    if state == "COMPLETED":
        problem(issue, [f"Jules session {session} finished without opening a pull request.",
                        "You need to do: nothing; Claude reads the session after the reset, or remove the label jules-stuck to resend it."])
        return True
    if "FAIL" in state or "AWAITING_USER" in state or now - sent_at > timedelta(hours=WORK_HOURS):
        problem(issue, [f"Jules session {session} is '{state or 'unknown'}' with no pull request after {WORK_HOURS} hours or less.",
                        "What I tried: sent it once and checked it every few hours.",
                        "You need to do: open jules.google.com and answer or restart that task, or remove the label jules-stuck to resend it."])
        return True
    print(f"#{num}: Jules is still working ({state or 'running'}).")
    return False


def send(issue: dict) -> None:
    """Send one directed batch to Jules.

    Inputs: the directed issue.
    Outputs: a Jules session that opens a pull request, label jules-working and a
    comment holding the session record.
    Errors: missing wording or a Jules refusal goes to problem().
    """
    num = issue["number"]
    batch = re.match(r"Directed:\s*(\S+)", issue["title"]).group(1)
    text, target = batch_text(batch, issue.get("body") or "")
    if not text:
        problem(issue, [f"No wording headed 'Batch {batch}' was found in plan/QUEUE.md.",
                        "You need to do: nothing; the wording run or Claude fixes the plan."])
        return
    if SOURCES and f"sources/github/{target}" not in SOURCES:
        problem(issue, [f"Jules can't see {target}.",
                        "You need to do: open https://github.com/settings/installations, tap Configure next to Google Labs Jules, add " + target.split("/")[1] + " under Repository access, and tap Save; then remove the label jules-stuck."])
        return
    body = {"prompt": prompt_for(batch, num, target, text), "title": f"Batch {batch}",
            "sourceContext": {"source": f"sources/github/{target}", "githubRepoContext": {"startingBranch": "main"}},
            "automationMode": "AUTO_CREATE_PR"}
    code, data = jules("sessions", "POST", body)
    if code != 200:
        problem(issue, [f"Jules refused Batch {batch} for {target} (answer {code}).",
                        "You need to do: nothing yet; Claude reads the answer in the run log."])
        print(str(data)[:300])
        return
    session = data.get("name") or ("sessions/" + str(data.get("id", "")))
    link = data.get("url", "")
    add_label(num, BUSY)
    comment(num, f"Sent Batch {batch} to Jules for {target}{(': ' + link) if link else '.'}\n{SESSION_MARK}{session} target={target} -->")
    print(f"#{num}: Batch {batch} sent to Jules for {target}.")


def send_task(issue: dict) -> None:
    """Send one `jules-task` issue to Jules as written.

    Inputs: the task issue; its body may name "Repository: owner/repo".
    Outputs: a Jules session that opens a pull request, label jules-working and a
    comment holding the session record.
    Errors: a Jules refusal goes to problem().
    """
    num = issue["number"]
    text = issue.get("body") or ""
    found = re.search(r"Repository:\s*`?([\w.-]+/[\w.-]+)", text)
    target = found.group(1) if found else REPO
    closes = f'\n- Put the line "Closes {REPO}#{num}" in the pull request description.' if target == REPO else ""
    prompt = f"""Do the task below for the Owner, exactly as written. Target repository: {target} (this repository). Task issue: {REPO}#{num}.

Rules that override anything else:
- Read AGENTS.md in this repository first and follow it.
- Never touch .github/, tools/, AGENTS.md, CLAUDE.md, BUILDER_RUNBOOK.md or PROJECTS.md. Never change existing plan text: add only.
- Made-up data only. No keys, passwords or personal details. Never say something was checked unless you checked it.
- Always finish with one pull request against main. If the task is a check, audit or report, add it as a new file audit/JULES_<short-name>.md in plain English, with every finding tied to a file and line.{closes}

=== Task: {issue["title"]} ===
{text[:MAX_TEXT]}
"""
    if SOURCES and f"sources/github/{target}" not in SOURCES:
        problem(issue, [f"Jules can't see {target}.",
                        "You need to do: open https://github.com/settings/installations, tap Configure next to Google Labs Jules, add " + target.split("/")[1] + " under Repository access, and tap Save; then remove the label jules-stuck."])
        return
    body = {"prompt": prompt, "title": issue["title"][:120],
            "sourceContext": {"source": f"sources/github/{target}", "githubRepoContext": {"startingBranch": "main"}},
            "automationMode": "AUTO_CREATE_PR"}
    code, data = jules("sessions", "POST", body)
    if code != 200:
        problem(issue, [f"Jules refused task #{num} for {target} (answer {code}).",
                        "You need to do: nothing yet; Claude reads the answer in the run log."])
        print(str(data)[:300])
        return
    session = data.get("name") or ("sessions/" + str(data.get("id", "")))
    add_label(num, BUSY)
    comment(num, f"Sent to Jules for {target}.\n{SESSION_MARK}{session} target={target} -->")
    print(f"#{num}: task sent to Jules for {target}.")


def run_tasks(issues: list[dict], now: datetime) -> None:
    """Follow the task in progress, or send the next `jules-task` issue.

    Inputs: open issues and the current time.
    Outputs: at most one new Jules session.
    Errors: none raised.
    """
    # github-actions[bot] is this repository's own workflows (the Owner's email commands).
    tasks = sorted((i for i in issues if TASK in labels(i) and i["user"]["login"] in (OWNER, "github-actions[bot]")
                    and not labels(i) & HOLD and STUCK not in labels(i)), key=lambda i: i["number"])
    running = 0
    for issue in tasks:
        tags = labels(issue)
        if BUSY in tags:
            if not follow_busy(issue, now):
                running += 1
            continue
        if SENT in tags:
            continue
        if running >= MAX_TASKS:
            break
        send_task(issue)
        running += 1
    print(f"Tasks with Jules now: {running}.")


def main() -> None:
    """Run both lanes: directed batches, then the task inbox.

    Inputs: none beyond the environment and the repository.
    Outputs: one line of text per lane, plus the actions above.
    Errors: none raised for GitHub or Jules refusals.
    """
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
    global SOURCES
    SOURCES, last = choose_key()
    if not KEY:
        print(f"No saved Jules key was accepted (last answer {last}), so nothing was sent.")
        title = "Jules key not accepted"
        if last and not any(i["title"] == title for i in issues):
            gh(f"repos/{REPO}/issues", "POST", {"title": title, "body": (
                f"Jules refused every saved key (answer {last}). The key must be the long code from the "
                "API key section of https://jules.google.com/settings#api, saved at "
                f"https://github.com/{REPO}/settings/secrets/actions/new as JULES_API_KEY. "
                "Close this issue once it's saved; the Jules builder checks again on its next run.")})
        return
    now = datetime.now(timezone.utc)
    run_batches(issues, now)
    run_tasks(issues, now)


def run_batches(issues: list[dict], now: datetime) -> None:
    """Follow the batch in progress, or send the next directed batch.

    Inputs: open issues and the current time.
    Outputs: at most one new Jules session.
    Errors: none raised.
    """
    directed = sorted((i for i in issues
                       if "directed" in labels(i) and i["user"]["login"] == OWNER
                       and re.match(r"Directed:\s*(?!OG-)\S+", i["title"]) and not labels(i) & HOLD),
                      key=order_key)
    busy_repos: set[str] = set()
    for issue in directed:
        tags = labels(issue)
        if STUCK in tags:
            continue
        if BUSY in tags or SENT in tags:
            value, _ = marker(issue["number"], SESSION_MARK)
            target = (value or "").partition(" target=")[2] or REPO
        if BUSY in tags:
            if not follow_busy(issue, now):
                busy_repos.add(target)
            continue
        if SENT in tags:
            _, opened_at = marker(issue["number"], PR_MARK)
            if opened_at and now - opened_at > timedelta(hours=MERGE_HOURS):
                problem(issue, [f"Jules's pull request for #{issue['number']} isn't merged after {MERGE_HOURS} hours.",
                                "You need to do: nothing if Jules is fixing its checks; otherwise Claude looks at it after the reset."])
                continue
            busy_repos.add(target)
            continue
        batch = re.match(r"Directed:\s*(\S+)", issue["title"]).group(1)
        _, want = batch_text(batch, issue.get("body") or "")
        if (want or REPO) in busy_repos:
            continue
        send(issue)
        busy_repos.add(want or REPO)
    print(f"Repositories with a batch in progress: {len(busy_repos)}.")


if __name__ == "__main__":
    main()
