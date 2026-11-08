# Batches MCP-A1 and MCP-U1 — Phase 1 batch wording (audited)

Source: `AUDITED_MCP_PHASE1_RESEARCH_AND_WORDING_2026-11-07` in Drive › Claude 2 (micahkoivumaki@gmail.com), Drive file id `1ywBuKS8sUawj6-pzr5z-V6IFv86palDx`. Wording by Gemini (Section 10, Step 1); inspected by Muse (Step 2), verdict PASS WITH CORRECTIONS, corrections C1–C7 applied in place and marked [C#]. Parts 2 and 3 are copied below word for word. Part 1 (research R-M1 to R-M7) and the audit header stay in the Drive document.

Approval: the Owner's Step 3 packet of 2026-11-08 01:08 America/Vancouver ("Execute Section 10, Step 3 of MCP_TOOL_SERVER_PROPOSAL_v1_2026-11-07 (+ ADDENDUM_1_API_DOOR): build BATCH MCP-A1 (apccs) first, then BATCH MCP-U1 (uclrcde), one batch per PR").

Muse's naming ruling C6 (no body change): the test class names in this document (ApccsBatchMCPA1Tests, UclrcdeBatchMCPU1Tests) govern; the receipts table is mcp_tool_receipts.

## PART 2 — PHASE 1 BATCH PLAN 1: BUILDER BOT CONTROL PANEL (APCCS)

BATCH MCP-A1: Read-only MCP tool core, plain /api JSON door, and receipt logger for APCCS (get_rulebook, get_canonical_file, queue_status, check_batch_ready, verify_fingerprint, question_ledger, and unified /mcp + /api dispatcher). Target repository: someonee12345678-hue/apccs. Canary: Canary check: MCP_APCCS = RECEIPT -> gatekeeper.

- Build only after: The Owner approves Phase 1 of MCP_TOOL_SERVER_PROPOSAL_v1_2026-11-07 and ADDENDUM_1_API_DOOR_2026-11-07, and Batch A4 is merged (it is: main @ 0232493e).
- Files: new code/apccs_mcp.py, standard library only (sys.stdlib_module_names). Tests go in code/test_apccs_mcp.py, class ApccsBatchMCPA1Tests. All tests use made-up data only, in a temporary repository folder; no real ledger rows, queue entries, or secrets. [C3] Frozen files (apccs_core.py, test_apccs_core.py) stay untouched.
- Reuse: sha256 and verify_safe_path from code/apccs_core.py; read_batch_status_cards and check_batch_needs_and_format_status_card from code/apccs_status.py; build_eight_line_log_v2_record and append_and_verify_log_v2_chain from code/apccs_logs.py. Nothing else.
- Constants: MCP_PROTOCOL_VERSIONS = ("2026-07-28", "2025-11-25", "2025-03-26"); CANONICAL_FILE_MAP = {"RULEBOOK": "plan/RULEBOOK.md", "AGENTS": "AGENTS.md", "QUEUE": "plan/QUEUE.md", "QUESTION_LEDGER": "plan/QUESTION_LEDGER.csv"}; API_RATE_LIMIT_MAX_REQUESTS = 60; APCCS_MCP_TOOLS (the 6 read-only tool definitions).

MCP-A101: GET_RULEBOOK (MCP_TOOL_SERVER_PROPOSAL_v1_2026-11-07 section 4)
- Function: get_rulebook(repo_root, commit_sha, code_version) -> dict
- Does: 1. Validate plan/RULEBOOK.md inside repo_root with verify_safe_path. 2. Read the file text and compute its digest with sha256. 3. Build a receipt containing tool name, inputs, result, UTC timestamp, code_version, and data fingerprint. 4. Return {"status": "OK", "path": "plan/RULEBOOK.md", "commit_sha": commit_sha, "fingerprint": <sha256>, "text": <text>, "receipt": <receipt>}.
- Refuses: A missing or unsafe path, or an empty commit_sha, returns {"status": "BLOCKED", "reason": "rulebook missing or invalid commit_sha", "receipt": <receipt>}.
- Tests: test_mcpa1_01_get_rulebook_returns_text_and_receipt (normal) and test_mcpa1_01_get_rulebook_blocks_missing_file (bad input).
- Done means: Any agent can reload the exact plan/RULEBOOK.md text with its verified fingerprint, commit, and receipt.
- Not checked: None.

MCP-A102: GET_CANONICAL_FILE (MCP_TOOL_SERVER_PROPOSAL_v1_2026-11-07 section 4)
- Function: get_canonical_file(repo_root, name, commit_sha, code_version) -> dict
- Does: 1. Look up name in CANONICAL_FILE_MAP. 2. Verify the target path inside repo_root with verify_safe_path. 3. Read the file bytes unchanged, compute sha256, and attach a tool receipt. 4. Return {"status": "OK", "name": name, "path": <rel_path>, "commit_sha": commit_sha, "fingerprint": <sha256>, "text": <text>, "receipt": <receipt>}.
- Refuses: Any name not in CANONICAL_FILE_MAP or missing on disk returns {"status": "BLOCKED", "reason": "unknown or missing canonical file", "allowed_names": sorted(CANONICAL_FILE_MAP), "receipt": <receipt>}.
- Tests: test_mcpa1_02_get_canonical_file_returns_unchanged_text (normal) and test_mcpa1_02_get_canonical_file_rejects_unlisted_name (bad input).
- Done means: Named canonical files are returned byte-for-byte with their fingerprint, preventing "dirty engine" rewrites.
- Not checked: Additional canonical files outside the repo tree until added to CANONICAL_FILE_MAP. The proposal's example canonical files (prompt engine, AGENT_RULES_CARD, code maps) are not in the map: their canonical repository paths are not pinned, and get_canonical_file cannot serve files outside repo_root; they join the map only when the Owner pins repo paths for them. [C7]

MCP-A103: QUEUE_STATUS (MCP_TOOL_SERVER_PROPOSAL_v1_2026-11-07 section 4)
- Function: queue_status(repo_root, status_path, open_prs, code_version) -> dict
- Does: 1. Read plan/QUEUE.md and check for any STOP file or stop flag in repo_root. 2. Read status cards via read_batch_status_cards(status_path) when present to find the next ready batch. 3. Record open_prs (a list of open PR dicts). 4. Return {"status": "OK", "next_ready_batch": <id_or_none>, "stop_flag": <bool>, "open_prs": open_prs, "fingerprint": <queue_sha256>, "receipt": <receipt>}.
- Refuses: Missing plan/QUEUE.md or non-list open_prs returns {"status": "BLOCKED", "reason": "queue missing or invalid open_prs", "receipt": <receipt>}.
- Tests: test_mcpa1_03_queue_status_reports_next_batch_and_stop_flag (normal) and test_mcpa1_03_queue_status_blocks_missing_queue (bad input).
- Done means: Next ready batch, STOP state, and open PRs are returned with a verified queue fingerprint.
- Not checked: Live GitHub network polling (handled by caller or cached adapter to respect the 60/hr limit).

MCP-A104: CHECK_BATCH_READY (MCP_TOOL_SERVER_PROPOSAL_v1_2026-11-07 section 4)
- Function: check_batch_ready(repo_root, status_path, batch_id, open_prs, code_version) -> dict
- Does: 1. Confirm batch_id appears in plan/QUEUE.md and no STOP flag is active. 2. Run check_batch_needs_and_format_status_card(status_path, batch_id) to confirm no dependency blocks it. 3. Verify no item in open_prs targets batch_id. 4. Return {"status": "OK", "batch_id": batch_id, "ready": <bool>, "reasons": [<reasons>], "receipt": <receipt>}.
- Refuses: Unknown batch_id, unmet needs, or an open PR for batch_id sets "ready": False with plain-English reasons.
- Tests: test_mcpa1_04_check_batch_ready_true_when_unblocked (normal) and test_mcpa1_04_check_batch_ready_false_on_open_pr_or_blocker (bad input).
- Done means: Software decides whether a batch is ready to build before any worker starts.
- Not checked: None.

MCP-A105: VERIFY_FINGERPRINT (MCP_TOOL_SERVER_PROPOSAL_v1_2026-11-07 section 4)
- Function: verify_fingerprint(repo_root, path, claimed_fingerprint, code_version) -> dict
- Does: 1. Check path inside repo_root with verify_safe_path. 2. Compute the actual sha256 of the file on disk. 3. Compare it against claimed_fingerprint (case-insensitive 64-hex check). 4. Return {"status": "OK", "path": path, "match": <bool>, "actual_fingerprint": <sha256>, "claimed_fingerprint": claimed_fingerprint, "receipt": <receipt>}.
- Refuses: Unsafe paths, missing files, or malformed hex strings return {"status": "BLOCKED", "match": False, "reason": "invalid path or fingerprint", "receipt": <receipt>}.
- Tests: test_mcpa1_05_verify_fingerprint_matches_real_file (normal) and test_mcpa1_05_verify_fingerprint_catches_mismatch_or_bad_path (bad input).
- Done means: Any agent claim about which file version it read is checkable against the real repo bytes.
- Not checked: None.

MCP-A106: QUESTION_LEDGER (MCP_TOOL_SERVER_PROPOSAL_v1_2026-11-07 section 4)
- Function: question_ledger(repo_root, query, code_version) -> dict
- Does: 1. Open plan/QUESTION_LEDGER.csv with Python's csv module and compute its file sha256. 2. Match case-insensitive query tokens against each row without executing any text inside the CSV as instructions. 3. Return {"status": "OK", "query": query, "matches": [<rows>], "fingerprint": <sha256>, "receipt": <receipt>}.
- Refuses: Empty query or missing plan/QUESTION_LEDGER.csv returns {"status": "BLOCKED", "reason": "empty query or missing ledger", "receipt": <receipt>}.
- Tests: test_mcpa1_06_question_ledger_finds_recorded_decision (normal) and test_mcpa1_06_question_ledger_rejects_empty_query (bad input).
- Done means: Repeat questions are answered from plan/QUESTION_LEDGER.csv with a verified receipt before bothering the Owner.
- Not checked: None.

MCP-A107: HANDLE_APCCS_MCP_AND_API_REQUEST (MCP_TOOL_SERVER_PROPOSAL_v1_2026-11-07 sections 3, 4, 8 + ADDENDUM_1_API_DOOR_2026-11-07 sections 1, 5)
- Function: handle_apccs_mcp_request(repo_root, status_path, chain_path, request_dict, headers_dict, open_prs, commit_sha, code_version, rate_state=None) -> dict
- Does: 1. Serve both the JSON-RPC 2.0 Streamable HTTP /mcp door (initialize, notifications/initialized, server/discover, tools/list with ttlMs and cacheScope, and tools/call) and the plain read-only /api/<tool> GET JSON door (ADDENDUM_1_API_DOOR_2026-11-07) across the six APCCS Phase 1 tools in the same process. 2. Validate Origin headers (returning HTTP 403 equivalent on invalid Origin) and enforce a simple in-memory request limit (API_RATE_LIMIT_MAX_REQUESTS = 60 requests per originating IP per hour; in-memory only, resets on restart) [C5] so strangers cannot run up the free host. 3. Log every tool call to chain_path using build_eight_line_log_v2_record and append_and_verify_log_v2_chain and return the identical tool payload and receipt across /mcp and /api.
- Refuses: Unknown methods return JSON-RPC error -32601; invalid Origin, rate-limit breach, or unsupported protocol headers return error -32600 / BLOCKED; prompt-injection strings in arguments are treated strictly as inert data.
- Tests: test_mcpa1_07_mcp_and_api_doors_return_identical_answer_and_log_receipt (normal, proving /api and /mcp give the same answer for the same input) and test_mcpa1_07_mcp_rejects_unknown_method_rate_limit_and_fences_injection (bad input).
- Done means: All three doors (local 127.0.0.1 page, /mcp, and /api) call the exact same standard-library functions and log full A2 hash-chain receipts.
- Not checked: Public hosting deployment until the Owner approves a host.

## PART 3 — PHASE 1 BATCH PLAN 2: LEGAL ENGINE (UCLRCDE)

BATCH MCP-U1: Read-only MCP tool core, plain /api JSON door, and receipt logger for UCLRCDE (check_rule_quote, check_citation_format, check_case_quote, list_sources, and unified /mcp + /api dispatcher). Target repository: someonee12345678-hue/uclrcde. Canary: Canary check: MCP_UCLRCDE = VERIFIED_QUOTE -> gavel.

- Build only after: The Owner approves Phase 1 of MCP_TOOL_SERVER_PROPOSAL_v1_2026-11-07 and ADDENDUM_1_API_DOOR_2026-11-07, and Batch LS-I is merged (it is: PR #15, main @ 201f0319).
- Files: new code/uclrcde_mcp.py, standard library only (sys.stdlib_module_names). Tests go in code/test_uclrcde_mcp.py, class UclrcdeBatchMCPU1Tests. All tests use made-up data only, in a temporary database; no real case data. [C3]
- Reuse: open_uclrcde_db from code/uclrcde_core.py; PUBLIC_LAW, CASE_FILE, and MADE_UP from code/uclrcde_decisions.py; find_canadian_citations and KNOWN_COURT_CODES from code/uclrcde_oracle.py; [C4] verify_quote_in_passage, verify_quote_in_locked_document, and check_section_in_force_on from code/uclrcde_sources.py. Nothing else.
- Tables, created with CREATE TABLE IF NOT EXISTS through open_uclrcde_db only: mcp_tool_receipts (id INTEGER PRIMARY KEY AUTOINCREMENT, receipt_sha256 TEXT, tool_name TEXT, inputs_json TEXT, result_json TEXT, code_version TEXT, data_sha256 TEXT, called_at TEXT). Add-only: no function updates or deletes a row.
- Constants: MCP_PROTOCOL_VERSIONS = ("2026-07-28", "2025-11-25", "2025-03-26"); NEUTRAL_CITATION_RE; API_RATE_LIMIT_MAX_REQUESTS = 60; UCLRCDE_MCP_TOOLS (the 4 read-only public-law tool definitions).

MCP-U101: CHECK_RULE_QUOTE (MCP_TOOL_SERVER_PROPOSAL_v1_2026-11-07 section 4)
- Function: check_rule_quote(db_path, rule_id, section_ref, quote, material_date, code_version) -> dict
- Does: 1. Open the database with open_uclrcde_db and confirm rule_id is a PUBLIC_LAW source (never a CASE_FILE record or document_cards row with private_flag != 0). 2. Run verify_quote_in_locked_document(db_path, rule_id, quote) for word-for-word verification. 3. Run check_section_in_force_on(db_path, rule_id, section_ref, material_date). 4. Log and return the verdict and receipt in mcp_tool_receipts.
- Refuses: Any mismatched quote, section not in force on material_date, or private CASE_FILE document returns {"status": "REJECTED", "verified": False, "reason": <reason>, "receipt": <receipt>}.
- Tests: test_mcpu1_01_check_rule_quote_passes_exact_in_force_rule (normal) and test_mcpu1_01_check_rule_quote_rejects_wrong_quote_or_out_of_force_date (bad input).
- Done means: Rule quotes pass only when they match the stored official copy word-for-word and were in force on the material date.
- Not checked: None.

MCP-U102: CHECK_CITATION_FORMAT (MCP_TOOL_SERVER_PROPOSAL_v1_2026-11-07 section 4)
- Function: check_citation_format(db_path, citation, code_version) -> dict
- Does: 1. Strip whitespace and check citation against NEUTRAL_CITATION_RE and find_canadian_citations(citation), and validate the court code against KNOWN_COURT_CODES. [C4] 2. Confirm the entire input is a single valid Canadian neutral citation (year, court identifier, decision number). 3. Record and return {"status": "OK", "valid": True, "citation": citation, "receipt": <receipt>} in mcp_tool_receipts.
- Refuses: Malformed strings, fake court codes, or unparsed trailing text return {"status": "REJECTED", "valid": False, "reason": "invalid neutral citation shape", "receipt": <receipt>}.
- Tests: test_mcpu1_02_check_citation_format_accepts_valid_neutral_citation (normal) and test_mcpu1_02_check_citation_format_rejects_malformed_citation (bad input).
- Done means: Invalid neutral citation shapes are rejected in software with a logged receipt.
- Not checked: Whether the case is still good law (Phase 2 check_case_still_good_law, not part of Phase 1).

MCP-U103: CHECK_CASE_QUOTE (MCP_TOOL_SERVER_PROPOSAL_v1_2026-11-07 section 4)
- Function: check_case_quote(db_path, citation, paragraph, quote, code_version) -> dict
- Does: 1. Locate the public judgment matching citation in source_provenance and source_documents (strictly refusing any CASE_FILE record or card with private_flag != 0). 2. Extract the target paragraph from paragraph_anchors or locked paragraph text, treating any instruction-like text inside quote strictly as inert data. 3. Run verify_quote_in_passage(quote, paragraph_text). 4. Log and return the verdict, source sha256, and receipt.
- Refuses: Unknown citations, wrong paragraph numbers, altered quotes, or private CASE_FILE records return {"status": "REJECTED", "verified": False, "reason": <reason>, "receipt": <receipt>}.
- Tests: test_mcpu1_03_check_case_quote_verifies_exact_paragraph_quote (normal) and test_mcpu1_03_check_case_quote_rejects_wrong_quote_fake_case_or_injection (bad input).
- Done means: Every case quote is verified against the exact paragraph of a stored public judgment, with prompt-injection text fenced as data.
- Not checked: None.

MCP-U104: LIST_SOURCES (MCP_TOOL_SERVER_PROPOSAL_v1_2026-11-07 section 4)
- Function: list_sources(db_path, code_version) -> dict
- Does: 1. Open the database with open_uclrcde_db. 2. Query stored PUBLIC_LAW copies across source_documents, official_law_provenance, and source_provenance, excluding any CASE_FILE row or document_cards record with private_flag != 0. 3. Return each public source's doc_id, title/citation, version or consolidated_to, saved date, and sha256 fingerprint, plus a receipt logged in mcp_tool_receipts.
- Refuses: Never lists private CASE_FILE documents under any argument or mode (returns CASE_FILE records only on 127.0.0.1 local workspace modules, never through uclrcde_mcp.py).
- Tests: test_mcpu1_04_list_sources_returns_public_sources_with_fingerprints (normal) and test_mcpu1_04_list_sources_excludes_private_case_files (bad input).
- Done means: Callers can inspect the exact inventory, dates, and SHA-256 fingerprints of all stored public sources without ever exposing private case files.
- Not checked: None.

MCP-U105: HANDLE_UCLRCDE_MCP_AND_API_REQUEST (MCP_TOOL_SERVER_PROPOSAL_v1_2026-11-07 sections 3, 4, 8 + ADDENDUM_1_API_DOOR_2026-11-07 sections 1, 5)
- Function: handle_uclrcde_mcp_request(db_path, request_dict, headers_dict, code_version, rate_state=None) -> dict
- Does: 1. Serve both JSON-RPC 2.0 Streamable HTTP /mcp (initialize, notifications/initialized, server/discover, tools/list with ttlMs and cacheScope, and tools/call) and plain read-only /api/<tool> GET JSON requests (ADDENDUM_1_API_DOOR_2026-11-07) across the four UCLRCDE Phase 1 tools in the same process. 2. Validate Origin headers, enforce API_RATE_LIMIT_MAX_REQUESTS (60 requests per originating IP per hour, in-memory, resets on restart) [C5], and ensure every call writes an add-only row in mcp_tool_receipts and returns the identical answer and receipt across /mcp and /api. 3. Treat all quote inputs strictly as inert data.
- Refuses: Unknown methods return JSON-RPC error -32601; invalid Origin, rate-limit breach, malformed requests, or unsupported protocol versions return error -32600 / REJECTED.
- Tests: test_mcpu1_05_mcp_and_api_doors_return_identical_answer_with_receipts (normal, proving /api and /mcp give the same answer for the same input) and test_mcpu1_05_mcp_dispatcher_rejects_unknown_tool_rate_limit_and_logs_receipt (bad input).
- Done means: All three doors (local 127.0.0.1 page, /mcp, and /api) run the exact same UCLRCDE public-law verification functions and log every receipt while keeping CASE_FILE data strictly on 127.0.0.1.
- Not checked: Public hosting deployment until the Owner approves a host.
