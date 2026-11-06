# Open Standards Readability Gate — APCCS A7 Proposal

**Status:** Owner-approved A-batch wording for queue promotion in this plan PR.  
**Purpose:** Make code and data readable by a competent person using standard tools, without this software or AI.  
**Queue position:** A7 follows A6. The 2026-11-04 Whole Product Plan Part 6 assigns A7 to the Readability Gate; this wording implements that slot. The separate Shaper Generator proposal is not queue authorization and has no A-batch number until its order is resolved through a later plan change.

## Proposed A7 queue wording

**Batch A7: Open Standards Readability Gate.**  
**Build only after:** Batch A6 is merged.  
**Target:** new `code/apccs_readability_gate.py`; tests in `code/test_apccs_readability_gate.py`, class `ApccsBatchA7ReadabilityTests`. The checker applies to files changed after A7; pre-existing files are listed in `audit/OPEN_STANDARDS_TODO.md` and never failed by this batch.  
**Dependencies:** Python 3.11 standard library only; use `ast` for source inspection. No network calls. Tests use made-up data and write only under temporary folders.  
**Canary:** `Canary check: STANDARD = OPEN -> readable`.

### A701: CHECK_MODULE_AND_PUBLIC_FUNCTION_DOCSTRINGS (source: Owner-approved Addendum 6, section 3)
Function: `check_docstrings_from_ast(source_text, filename) -> dict`
Does: 1. Parse the module with `ast`. 2. Require a module docstring and a docstring on every public function/method, each stating `Inputs:`, `Outputs:`, and `Errors:`. 3. Require parameter and return type hints on public functions. 4. Return source locations for violations.
Refuses: Syntax errors, absent sections, or missing type hints produce a failed check, never a pass.  
Tests: `test_a701_01_accepts_documented_module_and_function` (normal) and `test_a701_02_fails_missing_io_docstring_or_type_hint` (bad input).  
Done means: Every changed module and public function explains inputs, outputs and errors.  
Not checked: Whether prose accurately describes behavior still needs review.

### A702: CHECK_PEP8_IDENTIFIER_NAMES (source: Owner-approved Addendum 6, section 3)
Function: `check_pep8_names_from_ast(source_text, filename) -> dict`
Does: 1. Inspect module, class, function, method, argument, variable and constant names from the AST. 2. Enforce PEP 8 naming forms: lowercase module names, `snake_case` functions/variables, `CapWords` classes, and `UPPER_CASE` constants; preserve leading underscores for private names and exempt required Python special names. 3. Return each violation with its source location.
Refuses: Any name outside these forms fails the check.  
Tests: `test_a702_01_accepts_pep8_identifier_forms` (normal) and `test_a702_02_rejects_misnamed_public_symbols` (bad input).  
Done means: Changed code uses the stated PEP 8 identifier conventions.  
Not checked: This instruction checks names, not every PEP 8 formatting rule.

### A703: ALLOW_ONLY_OPEN_DATA_FORMATS (source: Owner-approved Addendum 6, section 3)
Function: `check_open_data_writes_from_ast(source_text, filename) -> dict`
Does: 1. Allow data persisted as JSON, JSON Lines, CSV, SQLite, or UTF-8 text/Markdown. 2. Reject imports or calls for `pickle`, `marshal`, `shelve`, `struct`, binary file-write modes, and byte-write APIs. 3. Fail closed on an unrecognized or dynamic file writer so it requires review instead of being presumed safe.
Refuses: Any detected binary or unrecognized writer fails the check.  
Tests: `test_a703_01_accepts_open_text_json_csv_and_sqlite_writers` (normal) and `test_a703_02_rejects_pickle_and_binary_writer_patterns` (bad input).  
Done means: Changed files use only the listed open formats; pickle and custom-binary indicators fail.  
Not checked: Static AST analysis cannot prove the behavior of arbitrary indirect code; unknown writer paths must fail closed and be reviewed.

### A704: CHECK_TIME_AND_HASH_REPRESENTATIONS (source: Owner-approved Addendum 6, section 3)
Function: `check_time_and_hash_values(timestamp_text, hash_text) -> dict`
Does: 1. Accept timestamps only when they parse as ISO 8601 and include an explicit UTC offset. 2. Accept hashes only as 64-character SHA-256 hexadecimal values. 3. Return the validation result without altering either value.
Refuses: Missing offsets, invalid dates, wrong hash length, or non-hex characters fail.  
Tests: `test_a704_01_accepts_offset_timestamp_and_sha256_hex` (normal) and `test_a704_02_rejects_naive_time_or_non_sha256_hash` (bad input).  
Done means: Stored times carry an offset and hashes use SHA-256 hex.  
Not checked: The checker validates representation, not the truth of a timestamp or the provenance of a digest.

### A705: LIMIT_CHECKS_TO_CHANGED_FILES_AND_TRACK_LEGACY (source: Owner-approved Addendum 6, section 3)
Function: `classify_readability_scope(changed_paths, existing_paths) -> dict`
Does: 1. Mark only paths changed after A7 as required checks. 2. Put pre-existing paths that fail a rule on an append-only legacy to-do list. 3. Never fail the batch because of an unmodified legacy file.
Refuses: Paths outside the repository or inconsistent changed-file inputs fail closed.  
Tests: `test_a705_01_checks_changed_files_and_lists_legacy` (normal) and `test_a705_02_rejects_outside_or_inconsistent_paths` (bad input).  
Done means: New work is checked immediately and existing files are tracked without retroactive failure.  
Not checked: The first implementation must inventory the actual main-branch files when built.

## Ordering and acceptance

The A7 assignment follows Whole Product Plan v1 Part 6. The merged `SHAPER_GENERATOR_2026-11-05.md` labels its concept as an A7 proposal, but it is not in the queue; its batch number and order remain unresolved. Do not build it as A7. A later plan change must resolve its position without rewriting this queue or the merged source document.

This is wording for a future batch, not build authorization. The checker must fail closed on unsupported write patterns, use only the standard library, and keep its tests in temporary folders. If the AST approach cannot reliably enforce a requirement, report the limitation and stop rather than claiming full coverage.

## Canonical queue-format correction (2026-11-05)

This appended full wording supplies an explicit Batch A7 heading and its A6 prerequisite. It preserves the approved Open Standards scope and supersedes proposal-only status where inconsistent.

## Batch A7: Open Standards Readability Gate

Status: Fully worded; ready only after Batch A6 is merged. The Owner's 14:03 Addendum 6 supplies this A7 scope. The separate Shaper Generator proposal has no approved queue position and is not this batch.

**Batch A7: Open Standards Readability Gate.**  
**Build only after:** Batch A6 is merged.  
**Target:** new `code/apccs_readability_gate.py`; tests in `code/test_apccs_readability_gate.py`, class `ApccsBatchA7ReadabilityTests`. The checker applies to files changed after A7; pre-existing files are listed in `audit/OPEN_STANDARDS_TODO.md` and never failed by this batch.  
**Dependencies:** Python 3.11 standard library only; use `ast` for source inspection. No network calls. Tests use made-up data and write only under temporary folders.  
**Canary:** `Canary check: STANDARD = OPEN -> readable`.

### A701: CHECK_MODULE_AND_PUBLIC_FUNCTION_DOCSTRINGS (source: Owner-approved Addendum 6, section 3)
Function: `check_docstrings_from_ast(source_text, filename) -> dict`
Does: 1. Parse the module with `ast`. 2. Require a module docstring and a docstring on every public function/method, each stating `Inputs:`, `Outputs:`, and `Errors:`. 3. Require parameter and return type hints on public functions. 4. Return source locations for violations.
Refuses: Syntax errors, absent sections, or missing type hints produce a failed check, never a pass.  
Tests: `test_a701_01_accepts_documented_module_and_function` (normal) and `test_a701_02_fails_missing_io_docstring_or_type_hint` (bad input).  
Done means: Every changed module and public function explains inputs, outputs and errors.  
Not checked: Whether prose accurately describes behavior still needs review.

### A702: CHECK_PEP8_IDENTIFIER_NAMES (source: Owner-approved Addendum 6, section 3)
Function: `check_pep8_names_from_ast(source_text, filename) -> dict`
Does: 1. Inspect module, class, function, method, argument, variable and constant names from the AST. 2. Enforce PEP 8 naming forms: lowercase module names, `snake_case` functions/variables, `CapWords` classes, and `UPPER_CASE` constants; preserve leading underscores for private names and exempt required Python special names. 3. Return each violation with its source location.
Refuses: Any name outside these forms fails the check.  
Tests: `test_a702_01_accepts_pep8_identifier_forms` (normal) and `test_a702_02_rejects_misnamed_public_symbols` (bad input).  
Done means: Changed code uses the stated PEP 8 identifier conventions.  
Not checked: This instruction checks names, not every PEP 8 formatting rule.

### A703: ALLOW_ONLY_OPEN_DATA_FORMATS (source: Owner-approved Addendum 6, section 3)
Function: `check_open_data_writes_from_ast(source_text, filename) -> dict`
Does: 1. Allow data persisted as JSON, JSON Lines, CSV, SQLite, or UTF-8 text/Markdown. 2. Reject imports or calls for `pickle`, `marshal`, `shelve`, `struct`, binary file-write modes, and byte-write APIs. 3. Fail closed on an unrecognized or dynamic file writer so it requires review instead of being presumed safe.
Refuses: Any detected binary or unrecognized writer fails the check.  
Tests: `test_a703_01_accepts_open_text_json_csv_and_sqlite_writers` (normal) and `test_a703_02_rejects_pickle_and_binary_writer_patterns` (bad input).  
Done means: Changed files use only the listed open formats; pickle and custom-binary indicators fail.  
Not checked: Static AST analysis cannot prove the behavior of arbitrary indirect code; unknown writer paths must fail closed and be reviewed.

### A704: CHECK_TIME_AND_HASH_REPRESENTATIONS (source: Owner-approved Addendum 6, section 3)
Function: `check_time_and_hash_values(timestamp_text, hash_text) -> dict`
Does: 1. Accept timestamps only when they parse as ISO 8601 and include an explicit UTC offset. 2. Accept hashes only as 64-character SHA-256 hexadecimal values. 3. Return the validation result without altering either value.
Refuses: Missing offsets, invalid dates, wrong hash length, or non-hex characters fail.  
Tests: `test_a704_01_accepts_offset_timestamp_and_sha256_hex` (normal) and `test_a704_02_rejects_naive_time_or_non_sha256_hash` (bad input).  
Done means: Stored times carry an offset and hashes use SHA-256 hex.  
Not checked: The checker validates representation, not the truth of a timestamp or the provenance of a digest.

### A705: LIMIT_CHECKS_TO_CHANGED_FILES_AND_TRACK_LEGACY (source: Owner-approved Addendum 6, section 3)
Function: `classify_readability_scope(changed_paths, existing_paths) -> dict`
Does: 1. Mark only paths changed after A7 as required checks. 2. Put pre-existing paths that fail a rule on an append-only legacy to-do list. 3. Never fail the batch because of an unmodified legacy file.
Refuses: Paths outside the repository or inconsistent changed-file inputs fail closed.  
Tests: `test_a705_01_checks_changed_files_and_lists_legacy` (normal) and `test_a705_02_rejects_outside_or_inconsistent_paths` (bad input).  
Done means: New work is checked immediately and existing files are tracked without retroactive failure.  
Not checked: The first implementation must inventory the actual main-branch files when built.

End of Batch A7.
