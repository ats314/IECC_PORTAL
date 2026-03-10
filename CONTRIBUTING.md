# Contributing to IECC Portal

This project is primarily developed by AI agents working with the ICC Secretariat. This guide ensures every contributor — human or agent — follows the same rules.

---

## Getting Started

### First-Time Setup

```bash
# 1. Clone and install
cd web && pip install -r requirements.txt

# 2. Verify everything works
python3 iecc_startup.py

# 3. Start the server
cd web && python main.py
```

The app runs at **http://localhost:8080**. Log in with any preset account (see `web/routes/auth.py`).

### For AI Agents

Run the startup script, then read the documentation in this order:

1. `CLAUDE.md` — Hard rules and project structure
2. `AGENT_GUIDE.md` — Database schema, ICC domain knowledge, naming conventions
3. `PROJECT_MEMORY.md` — Session history and known issues (read last 3 sessions)
4. `docs/QUERY_COOKBOOK.md` — SQL query patterns (skim)
5. `docs/PORTAL_ROADMAP.md` — Development roadmap
6. `web/DEVELOPMENT.md` — What's built, what's next, testing checklist
7. `web/README.md` + `web/ARCHITECTURE.md` — Setup and request lifecycle

---

## Hard Rules

These apply to every change. No exceptions.

### Database

- **The database is the sole source of truth.** Never cite numbers from docs without querying the DB first.
- **WAL checkpoint after every write:** `conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')` before `conn.close()`.
- **No sqlite3 CLI** — use `python3 -c "import sqlite3; ..."` for all DB operations.
- **Never use `computed_status`** — the column is `status`.
- **Never use prefix `REC`** — use `RECP` for residential proposals.
- **Never use `canonical_id` as `proposal_uid`** — `proposal_uid` is a SHA1 hash. Always look it up: `SELECT proposal_uid FROM proposals WHERE canonical_id = 'REPC34-25'`.

### Architecture

- **Two completely separate portals** (Chair and Secretariat) — never combine them.
- **Don't rebuild what exists** — enhance it.
- **Ask before architectural changes** — schema changes, template restructuring, etc.
- **Use `render()`, not `TemplateResponse`** — from `routes.helpers` for all full pages.

### Naming & Conventions

- Body-to-subgroup mapping in `config.BODY_TO_SUBGROUP` is critical. If you add meeting bodies, update this mapping or agendas will silently show zero proposals.
- Understand the ICC document chain before touching proposals (see `AGENT_GUIDE.md`).

---

## Development Workflow

### Making Changes

1. **Read before editing.** Understand existing code before suggesting modifications.
2. **Enhance, don't rebuild.** Everything in "What's DONE" in `web/DEVELOPMENT.md` is working. Build on it.
3. **Test your changes.** Follow the 19-point testing checklist in `web/DEVELOPMENT.md`.
4. **Keep it simple.** Don't add features, refactor code, or make improvements beyond what was asked.

### Code Patterns

See `web/DEVELOPMENT.md` for patterns on:
- Adding a new route
- Adding a new user
- Adding a new page
- Adding a new document export
- Template variables available via `render()`

### Commit Messages

Use clear, descriptive messages. Format:
```
<verb> <what changed> — <why>

Examples:
  Fix uploaded_by field to use correct user dict key
  Add meeting documents feature for Go Live display
  Update DEVELOPMENT.md with current feature status
```

---

## Project Structure

```
IECC_PORTAL/
├── CLAUDE.md                 # Agent rules and project structure
├── AGENT_GUIDE.md            # Database schema, ICC domain knowledge
├── PROJECT_MEMORY.md         # Session history, decisions, known issues
├── CONTRIBUTING.md           # THIS FILE
├── CHANGELOG.md              # Version history by session
├── LICENSE                   # MIT license
│
├── docs/                     # Reference documentation
│   ├── QUERY_COOKBOOK.md      # Ready-to-use SQL queries
│   ├── PORTAL_ROADMAP.md     # Three-phase development plan
│   ├── PROPOSAL_LANGUAGE_EXTRACTION.md
│   ├── IECC_SHAREPOINT_STRUCTURE.md
│   └── SKILLS_DEVELOPMENT.md
│
├── web/                      # FastAPI web application
│   ├── DEVELOPMENT.md        # What's built, what's next, testing checklist
│   ├── README.md             # Setup and file structure
│   ├── ARCHITECTURE.md       # Request lifecycle, auth, templates
│   └── ...
│
├── iecc.db                   # SQLite database (source of truth)
├── iecc_startup.py           # Full startup: docs + DB + server test
├── iecc_preflight.py         # Quick DB health check
└── ...
```

---

## Testing

There is no automated test suite. After changes, manually verify using the testing checklist in `web/DEVELOPMENT.md`. At minimum:

1. **Login** — Both roles work
2. **Route guards** — Chair can't access secretariat routes and vice versa
3. **Your changes** — The specific feature you modified works
4. **Adjacent features** — Nothing nearby broke

For database changes, run:
```bash
python3 iecc_preflight.py
```

---

## Updating Documentation

After making changes, update the relevant docs:

| What changed | Update |
|---|---|
| New route or feature | `web/DEVELOPMENT.md` ("What's DONE" section) |
| Schema change | `AGENT_GUIDE.md` (schema section) |
| Bug fix or decision | `PROJECT_MEMORY.md` (current session entry) |
| New query pattern | `docs/QUERY_COOKBOOK.md` |
| Roadmap progress | `docs/PORTAL_ROADMAP.md` (phase status) |

**Do not** update documentation with hardcoded counts from the database — they go stale immediately.
