#!/bin/sh
# Start Mission Control on the Owner's phone (Termux). Run it from the apccs folder:
#   sh scripts/termux_start_mission.sh
# It keeps the screen's server running on 127.0.0.1 only, pulls the newest files every 60 seconds
# and, when a read-only GitHub token is saved in ~/.apccs_env, refreshes the GitHub cache.
# The token is only ever read from the environment: this script never prints, logs or saves it.
# Settings (paths) come from ~/.apccs_mission.json, the same file the server reads.

REPO_DIR=$(cd "$(dirname "$0")/.." && pwd)
REPO_SLUG="someonee12345678-hue/apccs"
API="https://api.github.com/repos/$REPO_SLUG"

cd "$REPO_DIR" || exit 1

if command -v termux-wake-lock >/dev/null 2>&1; then
  termux-wake-lock
fi

if [ -f "$HOME/.apccs_env" ]; then
  . "$HOME/.apccs_env"
fi

python3 code/apccs_mission_server.py &
SERVER_PID=$!
trap 'kill "$SERVER_PID" 2>/dev/null' EXIT INT TERM

refresh_cache() {
  work=$(mktemp -d) || return 1
  if curl --fail --silent --show-error -H "Authorization: Bearer $APCCS_GITHUB_READ_TOKEN" -H "Accept: application/vnd.github+json" -o "$work/pulls.json" "$API/pulls?state=all&per_page=30&sort=created&direction=desc"; then
    for number in $(python3 -c 'import sys; sys.path.insert(0, "code"); from apccs_mission_server import list_open_pr_numbers; print(*list_open_pr_numbers(open(sys.argv[1], encoding="utf-8").read()))' "$work/pulls.json"); do
      curl --fail --silent --show-error -H "Authorization: Bearer $APCCS_GITHUB_READ_TOKEN" -H "Accept: application/vnd.github+json" -o "$work/reviews_$number.json" "$API/pulls/$number/reviews" || true
    done
    python3 - "$work" <<'PY' || echo "GitHub cache not updated; the server keeps the last cache"
import json, os, pathlib, sys
from datetime import datetime, timezone
sys.path.insert(0, "code")
from apccs_mission_server import build_github_cache
work = pathlib.Path(sys.argv[1])
settings = json.loads((pathlib.Path.home() / ".apccs_mission.json").read_text(encoding="utf-8"))
reviews = {}
for saved in work.glob("reviews_*.json"):
    reviews[int(saved.stem.split("_")[1])] = saved.read_text(encoding="utf-8")
cache = build_github_cache((work / "pulls.json").read_text(encoding="utf-8"), reviews, datetime.now(timezone.utc))
target = pathlib.Path(settings["github_cache_path"])
temporary = target.with_name(target.name + ".new")
temporary.write_text(json.dumps(cache), encoding="utf-8")
os.replace(temporary, target)
PY
  else
    echo "GitHub did not answer; the server keeps the last cache"
  fi
  rm -rf "$work"
}

while true; do
  git pull --ff-only >/dev/null 2>&1 || echo "git pull did not update; keeping the current files"
  if [ -n "$APCCS_GITHUB_READ_TOKEN" ]; then
    refresh_cache
  fi
  sleep 60
done
