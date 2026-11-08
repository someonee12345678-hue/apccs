# Mission Control Phase 1 — Owner approvals, autonomy rule and batch wording (2026-11-08)

Status: Owner-approved. Architect: Claude. Proposal: `MISSION_CONTROL_APP_PROPOSAL_v1_2026-11-08` in Drive › Claude 2 (Drive file id `1C7PC-wbgIL3-TPDJq4kUpvT8aWLot7wvrZ4uRdqyo74`). Research: `TOOLBOX_ADDITIONS_2026-11-08_HERDR` in Drive › Claude 2.

## Owner words (verbatim, America/Vancouver)

- 09:07: "We can make a server and we can borrow ideas. We have components to meet the requirements. We just need to put it all together in one place. It also visually shows how the agents talk to each other. Let some take over create things. Gives you the workflow. These are useful features. Can we make this into an Android application or browser."
- 09:12: "Yes to all." (answer to decisions D1 to D4 below)
- 09:12: "I want the bot to solve their own problems find a way to come up with an answer without needing intervention."

## Decisions approved

- D1: The proposal is approved: a web app first, served by our own server and installed from Chrome; an Android app later.
- D2: GitHub read access for Phase 1 is a fine-grained, read-only token that the Owner stores only on his phone. The repository is private, so a token is needed. No agent ever sees it.
- D3: The three ideas taken from Herdr: W1 four job states (`working`, `blocked`, `done`, `idle`); W2 the next batch starts when the last one reports done, not on a timer; W3 every screen reads one owned snapshot.
- D4: A lease (an agent's claim on a batch) lasts 30 minutes by default.

## Autonomy rule (ledger Q024)

Agents work problems out themselves. Before asking the Owner they check the ledger and plan, read the code and earlier pull requests, and try up to three allowed ways. When it is still a judgment call that can be undone, they take the safest choice that can be undone, write `DECIDED BY AGENT` with the reason and UNDO, and carry on; the checker reviews it after the merge. They stop only for "needs your OK" items: anything that cannot be undone, money, keys or accounts, protected files and the RULEBOOK hard limits.

## How this wording was made (ledger Q025)

The RULEBOOK names Gemini as the main wording agent. Reaching Gemini needs the Owner to carry a script, which Q023 and Q024 rule out, so the architect wrote this wording here. A different agent checks it: the Codex review on this pull request, and Muse after the merge (Q002, Q022). UNDO: revert the plan pull request.

## Phase 2 and 3 (not worded yet)

Phase 2: leases and a role table, then Approve, Pause and Reassign as logged, reversible actions. It waits for the open Phase 2 credential decision. Phase 3 (optional): an Android app wrapper and an always-on cloud host.

## Batch wording (copied word for word into `plan/QUEUE.md`)

**Batch MC-A1: Mission Control event feed and agent states.**
**Build only after:** the plan pull request that adds this wording is merged.
**Builder:** the next free builder: Claude (Owner OK 2026-11-08, ledger Q025) or the ChatGPT/Codex task. Never the agent that audits it (Q022).
**Target:** new `code/apccs_events.py`; tests in new `code/test_apccs_events.py`, class `ApccsBatchMCA1Tests`.
**Dependencies:** Python standard library only; may import public functions from `apccs_logs` and `apccs_status`. No network calls. The functions write no files; tests write only inside temporary folders.
**Canary:** `Canary check: MISSION = EVENT -> radar`.
**Standards:** Batch A7 Open Standards applies to every new Python file. Pilot P-SG1 applies: write the arm actually used.

### MC-A101: COLLECT_ALL_EVENTS (source: Owner 2026-11-08 09:07, "put it all together in one place")

Function: `collect_mission_events(chain_path, status_path, github_cache_path, agent_map) -> dict`

Does:
1. Read the Log v2 chain at `chain_path` with the same integrity check `apccs_logs` uses. Each record becomes one event: `time` from the record ID (`YYYYMMDD-HHMM`, America/Vancouver, stored as UTC ISO 8601), `from_agent` from its agent code (`GE` Gemini, `MU` Muse, `CG` ChatGPT/Codex, `CL` Claude, `MI` Owner), `kind` `log`, `ref` the record ID, `summary` its ASK line.
2. Read batch status cards with `read_batch_status_cards(status_path)` and the job records in the same file. Each becomes an event with `kind` `batch_state` or `job_state`, `ref` the batch or job ID, and its state and holder.
3. Read the GitHub cache at `github_cache_path`: a JSON object `{"fetched_at": "<UTC ISO 8601>", "pulls": [{"number", "title", "author", "state", "created_at", "merged_at", "head_ref", "reviews": [{"reviewer", "state", "submitted_at"}]}]}`. Each pull gives one `pr_opened` event, one `pr_merged` event when `merged_at` is set, and one `pr_review` event per review. `agent_map` maps GitHub logins to agent names; an unknown login becomes `unknown`.
4. Return `{"status": "OK" | "PARTIAL", "events": [...], "warnings": [...]}`, events oldest first. If one source is missing or fails its check, keep the other sources' events, set `PARTIAL` and name the failed source in `warnings`.

Refuses a chain that fails the Log v2 integrity check (reported as a warning, never repaired or partly used), malformed cache JSON, off-shape pull entries, and any event without a source `ref`.
Tests: `test_mca101_01_collects_events_from_three_sources` (normal) and `test_mca101_02_bad_source_gives_partial_with_warning` (bad input).
Done means: One sorted event list shows everything the three sources hold, and a broken source is named, not hidden.
Not checked: Real GitHub data; the cache file is written by Batch MC-A3's phone script.

### MC-A102: FIND_THE_HANDOFFS (source: Owner 2026-11-08 09:07, "visually shows how the agents talk to each other")

Function: `derive_handoffs(events) -> list`

Does:
1. Apply fixed rules, no AI: `pr_opened` is author to `Gate`; `pr_review` is reviewer to the pull's author; `pr_merged` is `Gate` to `Muse` (post-merge audit, RULEBOOK); a `job_state` of `claimed` is `Gate` to the claiming agent.
2. Each handoff is `{time, from_agent, to_agent, kind, ref}`, copied from its event.
3. Return the handoffs oldest first, plus a count of events skipped because no rule matched.

Refuses events missing `time`, `kind` or `ref`. Kinds without a rule are skipped and counted, never guessed.
Tests: `test_mca102_01_handoffs_follow_fixed_rules` (normal) and `test_mca102_02_rejects_incomplete_events` (bad input).
Done means: Every line on the map comes from one fixed rule and one source event.
Not checked: Handoffs that happen only inside chat apps.

### MC-A103: FOUR_AGENT_STATES (source: Owner 2026-11-08 approval of W1 and D4; ledger Q025)

Function: `derive_agent_states(events, now, lease_minutes=30) -> dict`

Does:
1. For each agent seen in the events, return exactly one of `working`, `blocked`, `done` or `idle`, with the `ref` of the event that decided it.
2. `working`: it holds a job `claimed` or `started` less than `lease_minutes` ago.
3. `blocked`: it holds a job `claimed` or `started` more than `lease_minutes` ago with no `done`; or its latest job is `blocked` or `failed`; or the batch it holds is `BLOCKED`, `CHECKS_RED` or `WAITING_FOR_MICAH`.
4. `done`: its latest job is `done` and it holds no other job. `idle`: anything else.

Refuses a `now` without a time zone, a `lease_minutes` below 1, and events that do not have the MC-A101 shape.
Tests: `test_mca103_01_four_states_from_jobs_and_leases` (normal) and `test_mca103_02_rejects_naive_time_and_bad_lease` (bad input).
Done means: Each agent has one of four states, and the reason is a source `ref`.
Not checked: Agents that never write job records always show as `idle`.

### MC-A104: FOUR_TIMELINE_VIEWS (source: the Owner's drop-down log views: summary, full view, milestones, chronological)

Function: `timeline_view(events, view) -> list`

Does:
1. `full`: every event, newest first. `chronological`: every event, oldest first.
2. `milestones`: only `pr_merged`, batch `DONE` or `BLOCKED`, and Log v2 records from `MI` (Owner decisions), newest first.
3. `summary`: one line per batch with its latest state, holder and time.

Refuses any other view name.
Tests: `test_mca104_01_four_views_from_one_event_list` (normal) and `test_mca104_02_rejects_unknown_view` (bad input).
Done means: The four views come from the same events and never disagree.
Not checked: How many events fit on a phone screen.

### MC-A105: ONE_SNAPSHOT_FOR_EVERY_SCREEN (source: W3, "every screen is just a client")

Function: `build_mission_snapshot(chain_path, status_path, github_cache_path, agent_map, now, lease_minutes=30) -> dict`

Does:
1. Call MC-A101 to MC-A104 and return one JSON-ready dict with `generated_at`, `sources` (status and warnings), `agents`, `handoffs`, `timeline` (all four views) and `jobs`.
2. Add `snapshot_sha256`: the SHA-256 of the canonical JSON (sorted keys, no spaces) of everything else.
3. Write nothing; the caller decides where the snapshot goes.

Refuses anything MC-A101 to MC-A104 refuse, passed through with the same error.
Tests: `test_mca105_01_snapshot_is_complete_and_fingerprinted` (normal) and `test_mca105_02_passes_errors_through` (bad input).
Done means: The web app, the MCP door and any later screen read the same snapshot.
Not checked: Snapshot size with a long history.

End of Batch MC-A1.

**Batch MC-A2: Mission Control web app.**
**Build only after:** Batch MC-A1 is merged.
**Builder:** as Batch MC-A1.
**Target:** new folder `web/mission/` with `index.html`, `app.js`, `style.css`, `manifest.webmanifest`, `sw.js` and `icon.svg`; new checker `code/apccs_mission_web.py`; tests in new `code/test_apccs_mission_web.py`, class `ApccsBatchMCA2Tests`.
**Dependencies:** plain HTML, CSS and JavaScript; no framework, no build step, and nothing loaded from another website. The checker uses the Python standard library only.
**Canary:** `Canary check: MISSION = SCREEN -> map`.
**Standards:** as Batch MC-A1.

### MC-A201: ONE_PAGE_THREE_SECTIONS (source: proposal section 4)

Does:
1. `index.html` (`lang="en"`) has sections with ids `map`, `timeline` and `jobs`, the heading "Mission control", and a view selector with exactly `summary`, `full`, `milestones` and `chronological`.
2. Phase 1 is read-only: the page has no buttons or forms that change anything.
3. It fits a 360-pixel-wide phone screen without sideways scrolling: a viewport meta tag, and no fixed width over 360 px in `style.css`.

Tests: `test_mca201_01_page_has_three_sections_and_four_views` (normal) and `test_mca201_02_checker_refuses_write_controls` (bad input: a temporary copy with a form fails).

### MC-A202: DRAW_FROM_THE_SNAPSHOT (source: Owner 2026-11-08 09:07; W3)

Does:
1. `app.js` fetches only the relative URL `/api/mission/snapshot`, when the page opens and every 30 seconds.
2. It draws the map as SVG: one node per agent showing its state word and colour, and one line per handoff from the last 24 hours, labelled with its `kind` and `ref`.
3. It fills the timeline from the chosen view and the jobs list from `jobs`.
4. It puts data into the page only with `textContent` or SVG attributes, never `innerHTML`, `eval` or `new Function`.

Tests: `test_mca202_01_script_reads_only_the_snapshot_url` (normal) and `test_mca202_02_checker_refuses_unsafe_script` (bad input: a temporary copy with `innerHTML`, `eval(` or an `http` URL fails).

### MC-A203: INSTALL_AND_WORK_OFFLINE (source: Owner's offline-backup requirement)

Does:
1. `manifest.webmanifest` is valid JSON with `name` "Mission control", `start_url` ".", `display` "standalone" and `icon.svg` as its icon.
2. `sw.js` caches the six app files and the last snapshot. Offline, the page shows the last snapshot with its `generated_at` time and the word "offline".

Tests: `test_mca203_01_manifest_and_offline_cache_are_valid` (normal) and `test_mca203_02_checker_refuses_bad_manifest` (bad input).

### MC-A204: STATES_READABLE_WITHOUT_COLOUR (source: proposal section 4; accessibility)

Does:
1. The page shows a legend with the four words `working`, `blocked`, `done` and `idle`.
2. Every state colour appears with its word, never colour alone, and no text is smaller than 14 px in `style.css`.

Tests: `test_mca204_01_legend_has_four_state_words` (normal) and `test_mca204_02_checker_refuses_colour_only_state` (bad input).

### MC-A205: ONE_CHECKER_FOR_THE_WEB_FILES (source: RULEBOOK open standards; Q022 separation)

Function: `check_mission_web_files(web_dir) -> dict`

Does:
1. Apply every rule in MC-A201 to MC-A204 to the files in `web_dir`.
2. Return `{"status": "PASS" | "FAIL", "problems": [...]}`, one plain-language line per broken rule, naming the file.

Refuses a missing folder, a missing app file, a symlink, and files outside `web_dir`.
Tests: `test_mca205_01_real_web_folder_passes` (normal) and `test_mca205_02_missing_or_symlinked_file_fails` (bad input).
Done means: Anyone can run one function to prove the web app keeps the Phase 1 rules.
Not checked: How the page looks in Chrome on the Owner's phone; the checker reads files, it does not render them.

End of Batch MC-A2.

**Batch MC-A3: Mission Control local server and phone start.**
**Build only after:** Batch MC-A2 is merged.
**Builder:** as Batch MC-A1.
**Target:** new `code/apccs_mission_server.py` and new `scripts/termux_start_mission.sh`; tests in new `code/test_apccs_mission_server.py`, class `ApccsBatchMCA3Tests`.
**Dependencies:** Python standard library only (`http.server`, `json`, `threading`); imports `apccs_events`, `apccs_mission_web` and `apccs_mcp`. The Python code makes no network calls and only listens on `127.0.0.1`. The phone script uses `git` and `curl` from Termux.
**Canary:** `Canary check: MISSION = LOCALHOST -> phone`.
**Standards:** as Batch MC-A1.

### MC-A301: ONE_HANDLER (source: W3; same door shape as Batch MCP-A1)

Function: `handle_mission_request(config, request_dict, now=None) -> dict`

Does:
1. Use the request and response shapes of `handle_apccs_mcp_request`: request `{path, method, client_ip, headers}`, response `{http_status, headers, body}`.
2. `GET /` and `GET /<file>` serve only the six files in `web/mission/`, with the right content type.
3. `GET /api/mission/snapshot` returns `build_mission_snapshot(...)` with the paths in `config` and the cache age from MC-A304 added to its warnings.
4. Pass `/mcp` and `/api/<tool>` requests unchanged to `handle_apccs_mcp_request`.
5. Any other path gives 404. Any method other than GET, or POST to `/mcp`, gives 405. Nothing in Phase 1 changes a file.

Refuses paths with `..`, absolute paths, symlinks and files outside `web/mission/`.
Tests: `test_mca301_01_serves_page_snapshot_and_mcp_door` (normal) and `test_mca301_02_refuses_unsafe_paths_and_write_methods` (bad input).

### MC-A302: LISTEN_ONLY_ON_THE_PHONE (source: proposal section 7; AGENTS rule 6)

Function: `run_mission_server(config, host="127.0.0.1", port=8765, ready_event=None) -> None`

Does:
1. Run a `ThreadingHTTPServer` bound to `host` and pass every request to MC-A301.
2. Refuse any host other than `127.0.0.1` or `localhost`, so it never listens on a network.
3. Stop cleanly on shutdown or keyboard interrupt.
4. The module's `if __name__ == "__main__":` block reads paths from `~/.apccs_mission.json` and calls this function.

Tests: `test_mca302_01_serves_snapshot_on_localhost` (normal: start on `127.0.0.1` port 0 in a thread, request the snapshot over `127.0.0.1`, shut down) and `test_mca302_02_refuses_network_host` (bad input: `0.0.0.0` is refused).

### MC-A303: TURN_SAVED_GITHUB_REPLIES_INTO_THE_CACHE (source: Owner D2, ledger Q025)

Functions: `list_open_pr_numbers(pulls_json_text) -> list` and `build_github_cache(pulls_json_text, reviews_by_pr, fetched_at) -> dict`

Does:
1. Read GitHub REST replies already saved on disk (the pulls list, and the reviews of each open pull) and produce the cache format of MC-A101.
2. Keep only the fields MC-A101 names; never store headers, tokens or anything else.

Refuses malformed JSON, missing fields and a `fetched_at` without a time zone.
Tests: `test_mca303_01_builds_cache_from_saved_replies` (normal) and `test_mca303_02_refuses_malformed_replies` (bad input).

### MC-A304: SAY_HOW_OLD_THE_GITHUB_DATA_IS (source: proposal section 12, polling delay)

Function: `check_github_cache(cache_path, now, max_age_minutes=10) -> dict`

Does: return `{"status": "FRESH" | "STALE" | "MISSING" | "BAD", "age_minutes": <int or None>}` so the screen can say how old the GitHub data is.
Refuses a `now` without a time zone and a `max_age_minutes` below 1.
Tests: `test_mca304_01_fresh_and_stale_cache` (normal) and `test_mca304_02_missing_or_bad_cache` (bad input).

### MC-A305: PHONE_START_SCRIPT (source: proposal section 7; ledger Q025)

File: `scripts/termux_start_mission.sh` (POSIX `sh`). Function: `check_phone_script(script_text) -> dict` in `code/apccs_mission_server.py`.

Does:
1. The script takes a Termux wake lock when `termux-wake-lock` exists, then starts the server from MC-A302 in the background.
2. Every 60 seconds it runs `git pull --ff-only`. When `APCCS_GITHUB_READ_TOKEN` is set, it uses `curl --fail` to save the last 30 pulls and the reviews of open pulls into a temporary folder, then calls MC-A303 to write the cache. When the token is not set, the server keeps running on the last cache.
3. The script never prints, logs or writes the token, and never uses `set -x`.
4. `check_phone_script` returns `{"status": "PASS" | "FAIL", "problems": [...]}` for rule 3, a token-looking literal, or a missing `--fail`.

Tests: `test_mca305_01_real_script_passes_checks` (normal; also `sh -n` when `sh` exists) and `test_mca305_02_checker_refuses_echoed_token_or_trace` (bad input).
Done means: The Owner can start Mission Control on his phone with one command, and it keeps working offline on the last data.
Not checked: Termux on the Owner's Nothing Phone; Android stopping background apps; GitHub rate limits.
Owner install step (needs his OK; ledger Q025): he creates a fine-grained, read-only GitHub token for apccs only and stores it on his phone in `~/.apccs_env`. No agent ever sees, stores or asks for it.

End of Batch MC-A3.
