# IECC Portal — ICC Code Development Platform

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com)
[![SQLite](https://img.shields.io/badge/SQLite-WAL_mode-003B57.svg)](https://sqlite.org)
[![HTMX](https://img.shields.io/badge/HTMX-dynamic_UI-3366CC.svg)](https://htmx.org)
A web-based platform for managing the **2027 International Energy Conservation Code (IECC)** development process. Built for the ICC Secretariat to track **510 code change proposals** across commercial and residential tracks — from submission through subgroup review, consensus committee voting, and final disposition.

> **Status:** Active internal tool. 34 development sessions completed.

---

## The Problem

The ICC code development cycle generates hundreds of proposals across multiple subgroups. Before this platform, tracking required:

- Manually cross-referencing spreadsheets, Word documents, and PDFs
- Chairs juggling cdpACCESS, SharePoint, and email during live meetings
- Secretariat staff hand-typing circulation forms after every meeting
- No single view of proposal status across subgroups

## The Solution

Two separate portals, one application:

### Secretariat Portal
Full admin dashboard with visibility across both tracks (commercial + residential). Filter and search proposals by track, status, subgroup, or phase. Manage meetings, review auto-generated circulation forms, export Word documents.

### Chair Portal
Meeting-focused interface designed for screen-sharing on Microsoft Teams. Chairs log in and see only their subgroup's meetings.

**Meeting workflow:**
1. Open meeting portal — agenda auto-populates with pending proposals
2. **Go Live** — full-screen presentation mode with big text, vote counters, keyboard navigation
3. Step through proposals — record recommendations, vote tallies, reason statements
4. Upload and display reference documents (PDFs, images) during the meeting
5. Review all staged actions, then send to secretariat
6. System commits actions to DB and auto-generates circulation form documents

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Python / FastAPI with Jinja2 server-side templates |
| **Frontend** | HTMX for dynamic updates — no JavaScript framework needed |
| **Database** | SQLite with WAL mode — single-file, zero-config |
| **Styling** | Custom CSS dark theme with ICC blue accents |
| **Documents** | Node.js `docx` library for Word generation, LibreOffice for PDF |
| **Rich Text** | Quill.js editor with ICC markup conventions (underline=additions, strikethrough=deletions) |
| **Server** | Uvicorn with hot reload |

## Quick Start

**Prerequisites:** Python 3.10+, Node.js 18+ (for document generation)

```bash
# Install Python dependencies
cd web && pip install -r requirements.txt

# Start the server
python main.py          # Any platform
# or
start.bat               # Windows — double-click to launch
```

The app runs at **http://localhost:8080**. Log in with any preset user account (17 accounts: 3 secretariat, 14 chairs).

---

## Project Structure

```
IECC_PORTAL/
├── web/                            # FastAPI web application
│   ├── main.py                     # App entry, middleware, auth enforcement
│   ├── config.py                   # Constants, body-to-subgroup mapping, SharePoint config
│   ├── routes/
│   │   ├── auth.py                 # 17 preset user accounts, login/logout
│   │   ├── dashboard.py            # Secretariat dashboard
│   │   ├── proposals.py            # Proposal list + detail with HTMX filtering
│   │   ├── meetings.py             # Meeting CRUD
│   │   ├── subgroup_portal.py      # Chair meeting portal + Go Live mode
│   │   ├── meeting_docs.py         # Document upload/view for Go Live
│   │   ├── circforms.py            # Circ form review queue
│   │   └── exports.py              # Word document generation
│   ├── services/                   # Doc generators, PDF conversion, SharePoint upload
│   ├── templates/                  # Jinja2 templates + HTMX partials
│   ├── static/                     # CSS (main + Go Live), HTMX, favicon
│   └── db/                         # Connection manager + all SQL queries
│
├── docs/                           # Reference documentation
│   ├── PORTAL_ROADMAP.md           # Three-phase development plan
│   ├── QUERY_COOKBOOK.md            # Ready-to-use SQL query patterns
│   ├── PROPOSAL_LANGUAGE_EXTRACTION.md
│   ├── IECC_SHAREPOINT_STRUCTURE.md
│   └── SKILLS_DEVELOPMENT.md
│
├── iecc_startup.py                 # Full startup: docs + DB health + server test
├── iecc_preflight.py               # Quick DB verification
├── iecc_query.py                   # CLI query tool
├── iecc_snapshot.py                # Change detection between sessions
├── iecc_verify.py                  # Doc-vs-DB consistency checker
├── build_combined_report.py        # XLSX report generator (11 sheets)
├── populate_content.py             # DOCX→DB proposal text extraction pipeline
│
├── reference/                      # ICC governance policies (JSON)
└── migrations/                     # SQL schema migrations
```

---

## Key Features

### Meeting Portal
- Auto-populate agenda from pending proposals for the chair's subgroup
- Accordion action forms — staged actions collapse to summary cards
- HTMX-powered staging with OOB progress bar updates (no page reload)
- Inline edit — click to modify a staged action with previous values pre-filled
- Finalize bar with document export buttons

### Go Live Presentation Mode
- Full-screen view optimized for Teams screen sharing
- Big text: proposal ID, code section, proponent clearly visible
- Large vote counter inputs with +/- buttons
- Quick-action buttons for common recommendations
- Auto-advance to next proposal after recording action
- Keyboard navigation between proposals
- Upload and display PDFs/images during the meeting

### Centralized Content
- Proposal code language extracted from cdpACCESS DOCX files with ICC legislative markup (`<ins>`/`<del>`)
- Pre-submitted modifications loaded into the portal
- Cross-reference chips linking related proposals (auto-detected from shared code sections)
- "Load into Editor" buttons that pre-populate the Quill rich text editor

### Circulation Form Pipeline
- Auto-generates DOCX/PDF circulation forms when chair sends meeting to secretariat
- Secretariat review queue with Preview/Approve/Reject workflow
- SharePoint Graph API upload service (dormant until Azure AD credentials configured)
- Three-layer name mapping: meeting body → proposal subgroup → SharePoint folder

### Document Exports
- Agenda (Word) — formatted meeting agenda with proposal table
- Circulation form (Word) — votes, recommendations, ICC-formatted markup
- Modification document (Word) — per-proposal pages with cdpACCESS entry checklist

---

## The ICC Code Development Process

The International Code Council develops model building codes used across the US. The 2027 IECC cycle:

1. **Public comments** submitted as code change proposals (510 total)
2. Proposals assigned to **subgroups** by topic (envelope, mechanical, lighting, etc.)
3. Subgroups hold **meetings** — recommend approve, disapprove, or approve as modified
4. Recommendations go to the **consensus committee** for final action
5. **Circulation forms** document each action with vote tallies and reason statements

This platform manages steps 2-5, replacing spreadsheets and manual document assembly with a database-driven workflow.

---

## Development Status

Three-phase roadmap (see [`docs/PORTAL_ROADMAP.md`](docs/PORTAL_ROADMAP.md)):

| Phase | Description | Status |
|-------|-------------|--------|
| **Phase 1** | Get proposal content into the portal | Done — text extraction pipeline built, portal pre-loads content |
| **Phase 2** | Meeting actions + modifications | Partial — action staging + Go Live done, "further modified" workflow not yet built |
| **Phase 3** | Post-meeting automation | Partial — circ form pipeline done, transcript extraction not yet built |

**Next priorities:**
1. SharePoint Azure AD setup (upload service is built, needs credentials)
2. "Further Modified" / combined consideration workflow
3. Transcript extraction pipeline (LLM-powered post-meeting data extraction)
4. Meeting prep dashboard

---

## Documentation

| Document | Purpose |
|----------|---------|
| [`CLAUDE.md`](CLAUDE.md) | AI agent operating instructions and hard rules |
| [`AGENT_GUIDE.md`](AGENT_GUIDE.md) | Full database schema, naming conventions, ICC lifecycle |
| [`PROJECT_MEMORY.md`](PROJECT_MEMORY.md) | Full 34-session development history |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | How to contribute — rules, workflow, patterns |
| [`CHANGELOG.md`](CHANGELOG.md) | Version history by development session |
| [`docs/PORTAL_ROADMAP.md`](docs/PORTAL_ROADMAP.md) | Three-phase development plan with current status |
| [`docs/QUERY_COOKBOOK.md`](docs/QUERY_COOKBOOK.md) | Ready-to-use SQL query patterns |
| [`web/DEVELOPMENT.md`](web/DEVELOPMENT.md) | Web app: rules, what's built, what's next, testing, code patterns |
| [`web/ARCHITECTURE.md`](web/ARCHITECTURE.md) | Technical deep dive: request lifecycle, auth, HTMX patterns |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `IECC_DB_PATH` | `../iecc.db` | Path to SQLite database |
| `IECC_PORT` | `8080` | Server port |
| `SP_TENANT_ID` | — | Azure AD tenant ID (SharePoint upload) |
| `SP_CLIENT_ID` | — | Azure AD app client ID |
| `SP_CLIENT_SECRET` | — | Azure AD app client secret |

## License

This project is proprietary to the International Code Council. All rights reserved.
