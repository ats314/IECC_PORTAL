# IECC Portal — ICC Code Development Platform

A web-based platform for managing the 2027 International Energy Conservation Code (IECC) development process. Built for the ICC Secretariat to track 510 code change proposals across commercial and residential tracks — from submission through subgroup review, consensus committee, and final disposition.

## What It Does

The platform replaces manual document juggling with a unified system where subgroup chairs run meetings and the secretariat manages the full proposal lifecycle.

**Two separate portals, one application:**

- **Secretariat Portal** — Dashboard with full visibility across both tracks (263 commercial + 247 residential proposals). Filter and search proposals, manage meetings, review circulation forms, export documents.

- **Chair Portal** — Meeting-focused interface where subgroup chairs manage their meetings while screen-sharing on Teams. Auto-populated agendas, proposal staging with vote capture, one-click document generation.

**Core meeting workflow:**
1. Chair opens meeting portal with auto-populated agenda
2. Steps through proposals, recording recommendations and vote tallies
3. Reviews all staged actions
4. Sends to secretariat — commits actions to database and generates circulation forms

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python / FastAPI with Jinja2 server-side templates |
| Frontend | HTMX for dynamic updates, custom CSS dark theme |
| Database | SQLite (WAL mode) — single-file, zero-config |
| Documents | Node.js `docx` library for Word generation, LibreOffice for PDF |
| Server | Uvicorn with hot reload |

## Quick Start

**Prerequisites:** Python 3.10+, Node.js 18+ (for document generation)

```bash
# Install Python dependencies
cd web
pip install -r requirements.txt

# Start the server
start.bat          # Windows
# or
python main.py     # Any platform
```

The app runs at **http://localhost:8080**.

The SQLite database (`iecc.db`) is included via Git LFS — it contains the live proposal data (510 proposals across commercial and residential tracks).

## Project Structure

```
IECC/
├── web/                        # FastAPI web application
│   ├── main.py                 # App entry, middleware, auth
│   ├── config.py               # Constants, body-to-subgroup mapping
│   ├── routes/                 # Route handlers
│   │   ├── auth.py             # Login/logout, session management
│   │   ├── dashboard.py        # Secretariat dashboard
│   │   ├── proposals.py        # Proposal list + detail
│   │   ├── meetings.py         # Meeting management
│   │   ├── subgroup_portal.py  # Chair meeting portal (core feature)
│   │   ├── circforms.py        # Circulation form review queue
│   │   └── exports.py          # Document generation endpoints
│   ├── services/               # Doc generators, PDF, SharePoint
│   ├── templates/              # Jinja2 templates + HTMX partials
│   ├── static/                 # CSS + HTMX library
│   └── db/                     # Connection manager + SQL queries
│
├── tools/                      # Python utility scripts
│   ├── iecc_startup.py         # Full project startup/health check
│   ├── iecc_preflight.py       # Quick database verification
│   ├── iecc_query.py           # CLI query tool for the database
│   ├── iecc_snapshot.py        # Change detection between sessions
│   ├── iecc_verify.py          # Documentation-vs-DB consistency check
│   ├── build_combined_report.py # XLSX report generator
│   ├── populate_content.py     # DOCX proposal text extraction pipeline
│   └── extract_monograph_markup.py # Monograph PDF text extraction
│
├── docs/                       # Project documentation
│   ├── AGENT_GUIDE.md          # Database schema + domain knowledge
│   ├── PROJECT_MEMORY.md       # Development session history
│   ├── PORTAL_ROADMAP.md       # Three-phase development plan
│   └── QUERY_COOKBOOK.md        # Ready-to-use SQL query patterns
│
├── reference/                  # ICC governance reference data (JSON)
├── migrations/                 # SQL schema migrations
```

## The ICC Code Development Process

The International Code Council (ICC) develops model building codes used across the US. The 2027 IECC cycle works like this:

1. **Public comments** are submitted as code change proposals (510 total for IECC 2027)
2. Proposals are assigned to **subgroups** by topic area (envelope, mechanical, lighting, etc.)
3. Subgroups hold **meetings** to review proposals — recommend approve, disapprove, or approve as modified
4. Recommendations go to the **consensus committee** for final action
5. **Circulation forms** document each action with vote tallies, reason statements, and any modification language

This platform manages steps 2-5, replacing spreadsheets and manual document assembly with a database-driven workflow.

## Documentation

| Document | Purpose |
|----------|---------|
| [`docs/AGENT_GUIDE.md`](docs/AGENT_GUIDE.md) | Full database schema, naming conventions, ICC lifecycle |
| [`docs/PORTAL_ROADMAP.md`](docs/PORTAL_ROADMAP.md) | Three-phase development plan with current status |
| [`web/ARCHITECTURE.md`](web/ARCHITECTURE.md) | Technical deep dive: request lifecycle, auth, HTMX patterns |
| [`web/DEVELOPMENT.md`](web/DEVELOPMENT.md) | What's built, what's next, known issues |
| [`web/LLM_HANDOFF.md`](web/LLM_HANDOFF.md) | Web app rules and patterns for AI-assisted development |

## Development Status

This is an active internal tool. Current state:

- **Phase 1** (proposal content in portal): Mostly complete — 178/510 proposals have extracted text with ICC markup
- **Phase 2** (meeting actions + modifications): Partially complete — action staging, modification ingestion, cross-references built
- **Phase 3** (post-meeting automation): Circ form generation pipeline working, transcript extraction not yet built

See [`PORTAL_ROADMAP.md`](PORTAL_ROADMAP.md) for the full plan.

## License

This project is proprietary to the International Code Council's code development process.
