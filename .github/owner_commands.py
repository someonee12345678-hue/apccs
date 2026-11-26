"""Owner commands by email reply: plain code, no AI.

Owner, 2026-11-25 23:41 America/Vancouver: "You have email options ... Don't hand the
work back to me." Every Daily status and problem email is a GitHub notification, and
replying to it posts the reply as a comment. This reads the first lines of a comment
written by the Owner and, when they start with a command word, does it:

  stop            open a STOP issue, so every builder and the auto-merge gate stop
  go              close every open STOP issue, so work carries on
  task: <text>    open a jules-task issue with <text>; Jules (Gemini) does it and
                  opens a pull request. A line "Repository: owner/repo" picks the repo.
  status          reply with what is waiting, with Jules, stuck, or stopped
  help            reply with this list

Any other comment is left alone, so Claude's Progress comments are never commands.

Inputs: the comment text and author from the environment (COMMENT_BODY, COMMENT_AUTHOR,
ISSUE_NUMBER), GITHUB_REPOSITORY and GH_TOKEN.
Outputs: at most one new issue or closed STOP issue, and one reply comment.
Errors: GitHub refusals are reported in the reply comment, never raised.
"""
import json
import os
import re
import urllib.error
import urllib.request

REPO = os.environ.get("GITHUB_REPOSITORY", "someonee12345678-hue/apccs")
OWNER = REPO.split("/")[0]
GH_TOKEN = os.environ.get("GH_TOKEN", "")
HELP = ("Reply to any of these emails with one of these on the first line:\n"
        "- `stop`: everything stops (a STOP issue)\n"
        "- `go`: everything carries on (STOP issues closed)\n"
        "- `task: <what you want done>`: Jules (Gemini) does it and opens a pull request; "
        "add a line `Repository: someonee12345678-hue/<repo>` for another repo\n"
        "- `status`: what is waiting, with Jules, stuck or stopped\n"
        "- `help`: this list")


def gh(path: str, method: str = "GET", body: dict | None = None) -> tuple[int, object]:
    """Call the GitHub REST API with this run's own short-lived token.

    Inputs: API path after https://api.github.com/, method, optional JSON body.
    Outputs: (status code, parsed JSON or an {"error": text} dict).
    Errors: HTTP errors are returned as their code, not raised.
    """
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request("https://api.github.com/" + path, data=data, method=method,
                                 headers={"Authorization": "Bearer " + GH_TOKEN,
                                          "Accept": "application/vnd.github+json",
                                          "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
            return resp.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as err:
        return err.code, {"error": err.read().decode("utf-8", "replace")[:300]}


def own_words(body: str) -> str:
    """Keep only what the Owner typed, dropping the quoted email below it.

    Inputs: the raw comment text.
    Outputs: the text above the first quoted line, signature or "On ... wrote:" line.
    Errors: none; empty text gives "".
    """
    kept = []
    for line in (body or "").replace("\r", "").split("\n"):
        if line.startswith(">") or line.strip() == "--" or re.match(r"^On .+ wrote:\s*$", line.strip()):
            break
        kept.append(line)
    return "\n".join(kept).strip()


def parse_command(text: str) -> tuple[str, str]:
    """Find the command word and its text.

    Inputs: the Owner's own words.
    Outputs: (command, rest): stop, go, status or help only when the first line is
    that word alone; task when the text starts "task:" or "jules:"; else ("", "").
    Errors: none.
    """
    first = text.split("\n", 1)[0].strip()
    alone = re.fullmatch(r"(stop|go|resume|status|help)[.!]?", first, re.I)
    if alone:
        word = alone.group(1).lower()
        return ("go" if word == "resume" else word), ""
    task = re.match(r"\s*(?:task|jules)\s*:\s*(.*)$", text, re.I | re.S)
    if task:
        return "task", task.group(1).strip()
    return "", ""


def open_issues() -> list[dict]:
    """List open issues (not pull requests).

    Inputs: none.
    Outputs: issue records; empty on a GitHub refusal.
    Errors: none raised.
    """
    code, items = gh(f"repos/{REPO}/issues?state=open&per_page=100")
    return [i for i in items if "pull_request" not in i] if code == 200 else []


def names(issue: dict) -> set[str]:
    """Return an issue's label names in lower case.

    Inputs: a GitHub issue record.
    Outputs: set of label names.
    Errors: none.
    """
    return {lab.get("name", "").lower() for lab in issue.get("labels", [])}


def status_text() -> str:
    """Build the plain status reply.

    Inputs: none beyond the open issues.
    Outputs: a few plain lines.
    Errors: none raised.
    """
    issues = open_issues()
    stops = [i for i in issues if i["title"].strip().upper().startswith("STOP")]
    work = [i for i in issues if names(i) & {"directed", "jules-task"}]
    lines = ["Status:", "- Stopped: " + ("yes (#%s)" % ", #".join(str(i["number"]) for i in stops) if stops else "no")]
    for label, words in (("jules-working", "With Jules now"), ("jules-pr-open", "Pull request open, waiting to merge"),
                         ("jules-stuck", "Stuck, needs a look")):
        found = [i for i in work if label in names(i)]
        if found:
            lines.append(f"- {words}: " + "; ".join(f"#{i['number']} {i['title'][:60]}" for i in found))
    waiting = [i for i in work if not names(i) & {"jules-working", "jules-pr-open", "jules-stuck"}]
    lines.append("- Waiting to be sent: " + (str(len(waiting)) if waiting else "none"))
    return "\n".join(lines)


def run(body: str, author: str, number: str) -> str:
    """Carry out one comment's command.

    Inputs: comment text, its author's login, and the issue it was posted on.
    Outputs: the reply text posted back, or "" when the comment is not a command.
    Errors: GitHub refusals are described in the reply.
    """
    if author.lower() != OWNER.lower():
        return ""
    command, rest = parse_command(own_words(body))
    if not command:
        return ""
    if command == "help":
        reply = HELP
    elif command == "status":
        reply = status_text()
    elif command == "stop":
        code, made = gh(f"repos/{REPO}/issues", "POST", {"title": "STOP (from your email reply)",
                                                         "body": "Opened from your reply on #%s. Reply `go` to carry on." % number})
        reply = (f"Stopped: #{made['number']} is open, so builders and the auto-merge gate stop. Reply `go` to carry on."
                 if code == 201 else f"Couldn't open the STOP issue (GitHub answered {code}).")
    elif command == "go":
        stops = [i for i in open_issues() if i["title"].strip().upper().startswith("STOP")]
        for issue in stops:
            gh(f"repos/{REPO}/issues/{issue['number']}", "PATCH", {"state": "closed"})
        reply = (f"Carrying on: closed {len(stops)} STOP issue(s)." if stops else "Nothing was stopped.")
    else:
        if not rest:
            return "Write what you want done after `task:`."
        title = "Task: " + re.sub(r"\s+", " ", rest.split("\n", 1)[0])[:90]
        code, made = gh(f"repos/{REPO}/issues", "POST",
                        {"title": title, "labels": ["jules-task"],
                         "body": rest + f"\n\n(From the Owner's email reply on #{number}.)"})
        reply = (f"Sent to Jules as #{made['number']}. You'll get the pull request link there."
                 if code == 201 else f"Couldn't open the task (GitHub answered {code}).")
    gh(f"repos/{REPO}/issues/{number}/comments", "POST", {"body": reply})
    return reply


if __name__ == "__main__":
    print(run(os.environ.get("COMMENT_BODY", ""), os.environ.get("COMMENT_AUTHOR", ""),
              os.environ.get("ISSUE_NUMBER", "")) or "Not a command.")
