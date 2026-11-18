# Phase 0 architecture index

Plain Markdown with relative links; it opens in Obsidian or any text viewer. No plugin is needed.
The builder `code/apccs_p0_architecture.py` (`build_p0_architecture_map`) produces the catalog below from saved facts; this page is the human entry point.

## Parts of the foundation

| Batch | What it is | Where |
| --- | --- | --- |
| P0-1 | Controller | `code/apccs_p0_controller.py` |
| P0-2 | Inbox | `code/apccs_p0_inbox.py` |
| P0-3 | Phone dashboard | `code/apccs_p0_dashboard.py`, [DASHBOARD_PHONE.md](DASHBOARD_PHONE.md) |
| P0-4 | Offline (Termux) | `code/apccs_p0_offline.py`, [TERMUX_OFFLINE.md](TERMUX_OFFLINE.md) |
| P0-5 | GitHub proof | `code/apccs_p0_proof.py`, [GITHUB_PROOF.md](GITHUB_PROOF.md) |
| P0-6 | Local snapshot restore | in the UCLRCDE repository |
| P0-7 | PostgreSQL recovery | `code/apccs_p0_recovery.py`, [POSTGRES_RECOVERY.md](POSTGRES_RECOVERY.md) |
| P0-8 | Decisions, map, search, exit | `code/apccs_p0_architecture.py`, [PHASE0_EXIT.md](PHASE0_EXIT.md), [ADR_TEMPLATE.md](ADR_TEMPLATE.md) |

Mission Control, OmniGuide and Oracle are separate existing systems; they are referenced, never replaced.
