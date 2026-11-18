# Phase 0: server PostgreSQL native backup and recovery acceptance (Batch P0-7)

Made-up control data only. Nothing in `code/apccs_p0_recovery.py` connects to PostgreSQL, runs a command or reads a credential. It checks saved evidence and builds plans for an operator to review.

## What it does

1. **Scope check** (`check_p0_postgres_scope`): needs an observed server, supported PostgreSQL 15 to 18 with matching command-line tools, a public/control-only dataset, the approved existing free backup route and observed backup space. No server observed means `NOT_CHECKED`. Private data (CASE_FILE), paid routes and inline credentials are refused.
2. **Backup plan** (`build_p0_postgres_backup_plan`): WAL archiving, a `pg_basebackup` physical base backup, `pg_verifybackup`, and bounded retention, as argument arrays with no shell. A logical dump is only an extra, separate copy and can never be the base for WAL replay.
3. **Receipt check** (`check_p0_postgres_backup_receipts`): binds base-backup ID, system identifier, timeline, LSN range, manifest verification, operation logs, digests and a gap-free run of archived WAL to one cluster. A fixture can pass the checker but is never live proof.
4. **Restore plan** (`build_p0_postgres_restore_plan`): target time must be inside observed coverage; restore goes only to an empty, disposable, nonproduction sandbox on 127.0.0.1 (not port 5432), with a synthetic before/after marker test.
5. **Acceptance** (`check_p0_recovery_acceptance`): a live pass needs native recovery logs, exact target and timeline, marker rows, an integrity observation, artifact references and a verifier other than the one who did the work. Fixtures give `NOT_CHECKED`; failures give `FAIL` with remediation. The dashboard only receives outcome and duration.

## Decided here (reversible)

Supported majors 15 to 18; WAL segment size defaults to 16 MiB; field names follow the docstrings. A later add-only plan correction can change these.

## Not checked

The existing server's inventory and permissions (K4), native tool execution, storage reliability, archive completeness, and any live restore. Deployment acceptance stays NOT CHECKED until the Owner provisions access outside agent-visible files.

## Undo

No runtime changed. Revert the pull request to remove the three files. In a real run, delete only the disposable sandbox directory; never touch the original database or backups.
