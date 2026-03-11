# CLAUDE.md — Agent Quick Start

## "Run Startup" — Do This First

When Alex says **"run startup"**, execute the full onboarding sequence:

```bash
python3 tools/iecc_startup.py
```

This script automatically:
1. Inventories all project documentation (9 files, ~2900 lines)
2. Verifies database health (proposals, actions, meetings, circ forms)
3. Starts the web server and tests all key routes
4. Reports a comprehensive status summary

After the script runs, **you must still read the documentation yourself**. The script verifies it exists — you need to internalize it. Follow the reading order below.

For docs-only (no server test): `python3 tools/iecc_startup.py --quick`

## Mandatory Reading Order

Read these files IN THIS ORDER. Do not skip any.

1. **This file** (`CLAUDE.md`) — you're here, hard rules and structure
2. **`docs/AGENT_GUIDE.md`** — database schema, domain knowledge, ICC lifecycle, document chain, naming conventions. This is the most important file. It tells you who Alex is, what the ICC process is, how proposals flow, and what every table/column means.
3. **`docs/PROJECT_MEMORY.md`** — full session history, decisions made, known issues. Read at least the last 3 session entries and the Known Issues sections.
4. **`docs/QUERY_COOKBOOK.md`** — ready-to-use SQL queries (reference — skim for patterns)
5. **`docs/PORTAL_ROADMAP.md`** — three-phase portal plan. Phase 1 mostly complete (Session 29).
6. **`web/LLM_HANDOFF.md`** — web app handoff: rules, patterns, what's built, what to build next
7. **`web/DEVELOPMENT.md`** — what's done, what's NOT done, current priorities
8. **`web/README.md`** + **`web/ARCHITECTURE.md`** — setup, file structure, request lifecycle

After reading all docs, tell Alex: **"I've completed startup and read all project docs. Ready to work."**

## Testing — USE THE TEST DATABASE

A test copy of the production database exists at `iecc_test.db`. **Use this for ALL testing.**

- To run the web app against the test DB: `IECC_DB_PATH=iecc_test.db` (set the env var before starting uvicorn)
- Create meetings, stage actions, send to secretariat, export docs — do whatever you want in the test DB
- **NEVER create fake meetings, test proposals, or dummy data in `iecc.db`.** That is production data with 510 real proposals and real meeting history. If you need to test, use `iecc_test.db`.
- To refresh the test DB from production: `cp iecc.db iecc_test.db`
- The test DB was created on 2026-03-09 from a known-good production state

## Hard Rules

- **The database is the SOLE source of truth for all IECC data.** Documentation teaches you how to query correctly — it is NOT a data source. Never cite numbers from docs without verifying against the DB first. Never tell Alex something about proposal status, meeting state, or row counts based on what you read in a doc. Query the DB.
- Database is `iecc.db` (unified, track column on all tables). Run `python3 tools/iecc_preflight.py` for current counts.
- Never use `computed_status` — the column is `status`
- Never use prefix `REC` — use `RECP` for residential proposals
- **Never use canonical_id as proposal_uid** — `proposal_uid` is a SHA1 hash (e.g., `006f2bc379947e12`), NOT the canonical_id string. Always look up the hash first: `SELECT proposal_uid FROM proposals WHERE canonical_id = 'REPC34-25'`. Session 31 created 10 duplicate SG actions from this mistake.
- The web app has TWO COMPLETELY SEPARATE portals (chair vs secretariat) — never combine them
- Don't rebuild what exists — enhance it
- Ask before making architectural changes
- Understand the ICC document chain BEFORE touching proposals (see docs/AGENT_GUIDE.md)
- **WAL checkpoint after every DB write** — `conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')` before `conn.close()`. VM can crash without warning.
- **No sqlite3 CLI** — use `python3 -c "import sqlite3; ..."` for all DB operations
- **If you can't do something Alex asked, ASK before substituting an alternative.** Do NOT silently switch approaches. Alex gives specific instructions for a reason — if you can't follow them exactly, stop and explain why, then ask what he wants you to do instead. This is critical.
- **If you can't find a file, ASK rather than assume it's not there.** Alex has the complete file structure on his machine. Never conclude a file doesn't exist or needs to be downloaded from an external source — ask Alex where it is first.
- **Browser preview: the server MUST run on Alex's Windows machine.** The Chrome browser is on the Windows host. The VM's network (172.16.10.x) is unreachable from the browser. Do NOT start uvicorn in the VM and try to browse to it — it will never work. Instead: (1) ask Alex to run `start.bat` in `IECC/web/`, (2) navigate to `http://127.0.0.1:8080`. The VM CAN use `curl` for route testing but CANNOT serve pages to the browser. This is a hard networking constraint, not a configuration issue. Do not waste time trying to fix it. See the `iecc-browser-preview` skill for full details.

## Project Structure

```
IECC/
├── iecc.db                    # THE database (SQLite, WAL mode, tracked via Git LFS)
├── iecc_test.db               # Test copy — use IECC_DB_PATH=iecc_test.db for all testing
├── CLAUDE.md                  # THIS FILE — hard rules and structure
├── README.md                  # Public-facing project description
│
├── docs/                      # Project documentation
│   ├── AGENT_GUIDE.md         # Schema, domain knowledge (READ THIS)
│   ├── PROJECT_MEMORY.md      # Session history (READ THIS)
│   ├── QUERY_COOKBOOK.md       # Ready SQL queries
│   ├── PORTAL_ROADMAP.md      # Three-phase portal improvement plan
│   ├── IECC_STATUS_REPORT.md  # Current status summary
│   └── ...                    # Other reference docs
│
├── tools/                     # Python utility scripts
│   ├── iecc_preflight.py      # DB health check (quick)
│   ├── iecc_startup.py        # FULL startup script (docs + DB + server)
│   ├── iecc_query.py          # CLI query tool
│   ├── iecc_snapshot.py       # Change detection (save/compare)
│   ├── iecc_verify.py         # Auto-check docs against DB
│   ├── build_combined_report.py  # XLSX report generator
│   ├── populate_content.py    # Content extraction pipeline (DOCX→DB)
│   └── extract_monograph_markup.py  # Monograph PDF text extraction
│
├── reference/                 # Governance reference files (JSON)
├── migrations/                # SQL migration files
│
└── web/                       # FastAPI web application
    ├── LLM_HANDOFF.md         # START HERE for web work
    ├── README.md              # Setup, file structure
    ├── ARCHITECTURE.md        # Technical deep dive
    ├── DEVELOPMENT.md         # What's built, what's next
    ├── main.py                # App entry point
    ├── config.py              # Constants + SharePoint config
    ├── start.bat              # Windows launcher (port 8080)
    ├── routes/                # Route handlers (incl. circforms.py)
    ├── templates/             # Jinja2 templates
    ├── static/                # CSS + HTMX
    ├── services/              # Doc generators, PDF gen, SharePoint upload
    └── db/                    # Connection + queries
```

## Skill Routing Guide

Seven IECC-specific skills exist. They form a knowledge layer — use the right one for the task:

| If you're doing... | Use skill | It knows about... |
|---------------------|-----------|-------------------|
| Querying DB, checking status, data questions | **iecc-query** | Schema, naming traps, SQL patterns, CLI tool, hash UIDs |
| Web routes, templates, HTMX, CSS, portal UI | **iecc-web-dev** | Two-portal rule, route map, HTMX patterns, body-to-subgroup mapping |
| Meeting portal flow, staging, finalization | **iecc-meeting-workflow** | Full pipeline (agenda → stage → review → send), Round 3, Go Live spec |
| Word/PDF exports, circ form docs, docx-js | **iecc-doc-gen** | JS-inside-Python pattern, HTML→Word parser, LibreOffice fallback |
| Viewing the portal in the browser | **iecc-browser-preview** | VM networking constraint, 127.0.0.1:8080, start.bat workflow, what NOT to try |
| Starting a new session | **iecc-startup** | Onboarding sequence, critical rules, process state |
| Ending a session | **iecc-session-close** | Doc update checklist, session template, skills-update workflow |

Skills cross-reference each other: meeting-workflow delegates data questions to iecc-query, route questions to iecc-web-dev, and doc questions to iecc-doc-gen. When in doubt, start with the skill closest to the user's task.
