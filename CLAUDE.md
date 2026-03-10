# CLAUDE.md — Agent Quick Start

## ⚡ "Run Startup" — Do This First

When Alex says **"run startup"**, execute the full onboarding sequence:

```bash
python3 iecc_startup.py
```

This script automatically:
1. Inventories all project documentation (8 files, ~2600 lines)
2. Verifies database health (proposals, actions, meetings, circ forms)
3. Starts the web server and tests all key routes
4. Reports a comprehensive status summary

After the script runs, **you must still read the documentation yourself**. The script verifies it exists — you need to internalize it. Follow the reading order below.

For docs-only (no server test): `python3 iecc_startup.py --quick`

## Mandatory Reading Order

Read these files IN THIS ORDER. Do not skip any.

1. **This file** (`CLAUDE.md`) — you're here, hard rules and structure
2. **`AGENT_GUIDE.md`** — database schema, domain knowledge, ICC lifecycle, document chain, naming conventions. This is the most important file. It tells you who Alex is, what the ICC process is, how proposals flow, and what every table/column means.
3. **`PROJECT_MEMORY.md`** — full session history, decisions made, known issues. Read at least the last 3 session entries and the Known Issues sections.
4. **`QUERY_COOKBOOK.md`** — ready-to-use SQL queries (reference — skim for patterns)
5. **`PORTAL_ROADMAP.md`** — three-phase portal plan. Phase 1 mostly complete (Session 29).
6. **`web/DEVELOPMENT.md`** — web app: rules, architecture, what's built, what's next, testing checklist, code patterns
7. **`web/README.md`** + **`web/ARCHITECTURE.md`** — setup, file structure, request lifecycle

After reading all docs, tell Alex: **"I've completed startup and read all project docs. Ready to work."**

## Hard Rules

- **The database is the SOLE source of truth for all IECC data.** Documentation teaches you how to query correctly — it is NOT a data source. Never cite numbers from docs without verifying against the DB first. Never tell Alex something about proposal status, meeting state, or row counts based on what you read in a doc. Query the DB.
- Database is `iecc.db` (unified, track column on all tables). Run `python3 iecc_preflight.py` for current counts.
- Never use `computed_status` — the column is `status`
- Never use prefix `REC` — use `RECP` for residential proposals
- **Never use canonical_id as proposal_uid** — `proposal_uid` is a SHA1 hash (e.g., `006f2bc379947e12`), NOT the canonical_id string. Always look up the hash first: `SELECT proposal_uid FROM proposals WHERE canonical_id = 'REPC34-25'`. Session 31 created 10 duplicate SG actions from this mistake.
- The web app has TWO COMPLETELY SEPARATE portals (chair vs secretariat) — never combine them
- Don't rebuild what exists — enhance it
- Ask before making architectural changes
- Understand the ICC document chain BEFORE touching proposals (see AGENT_GUIDE.md)
- **WAL checkpoint after every DB write** — `conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')` before `conn.close()`. VM can crash without warning.
- **No sqlite3 CLI** — use `python3 -c "import sqlite3; ..."` for all DB operations
- **If you can't do something Alex asked, ASK before substituting an alternative.** Do NOT silently switch approaches. Alex gives specific instructions for a reason — if you can't follow them exactly, stop and explain why, then ask what he wants you to do instead. This is critical.

## Project Structure

```
IECC/
├── iecc.db                    # THE database (SQLite, WAL mode)
├── AGENT_GUIDE.md             # Schema, domain knowledge (READ THIS)
├── PROJECT_MEMORY.md          # Session history (READ THIS)
├── CLAUDE.md                  # THIS FILE — hard rules and structure
├── QUERY_COOKBOOK.md           # Ready SQL queries
├── PORTAL_ROADMAP.md          # Three-phase portal improvement plan
│
├── iecc_preflight.py          # DB health check (quick)
├── iecc_startup.py            # FULL startup script (docs + DB + server)
├── iecc_query.py              # CLI query tool
├── iecc_snapshot.py           # Change detection (save/compare)
├── iecc_verify.py             # Auto-check docs against DB
├── build_combined_report.py   # XLSX report generator
├── populate_content.py        # Content extraction pipeline (DOCX→DB)
│
├── reference/                 # Governance reference files (JSON)
├── skills-update/             # Updated skill files (copy to Windows between sessions)
├── migrations/                # SQL migration files
│
├── ARCHIVES/                  # Commercial source data, backups, JSON files
├── 2027_RESIDENTIAL/          # Residential source data (circ forms, minutes, agendas)
├── IECC standard/             # ICC process docs, forms, presentations
│
└── web/                       # FastAPI web application
    ├── DEVELOPMENT.md         # Web app: rules, architecture, what's built, what's next
    ├── README.md              # Setup, file structure
    ├── ARCHITECTURE.md        # Technical deep dive
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

Six IECC-specific skills exist. They form a knowledge layer — use the right one for the task:

| If you're doing... | Use skill | It knows about... |
|---------------------|-----------|-------------------|
| Querying DB, checking status, data questions | **iecc-query** | Schema, naming traps, SQL patterns, CLI tool, hash UIDs |
| Web routes, templates, HTMX, CSS, portal UI | **iecc-web-dev** | Two-portal rule, route map, HTMX patterns, body-to-subgroup mapping |
| Meeting portal flow, staging, finalization | **iecc-meeting-workflow** | Full pipeline (agenda → stage → review → send), Round 3, Go Live spec |
| Word/PDF exports, circ form docs, docx-js | **iecc-doc-gen** | JS-inside-Python pattern, HTML→Word parser, LibreOffice fallback |
| Starting a new session | **iecc-startup** | Onboarding sequence, critical rules, process state |
| Ending a session | **iecc-session-close** | Doc update checklist, session template, skills-update workflow |

Skills cross-reference each other: meeting-workflow delegates data questions to iecc-query, route questions to iecc-web-dev, and doc questions to iecc-doc-gen. When in doubt, start with the skill closest to the user's task.
