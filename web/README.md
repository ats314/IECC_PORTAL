# ICC Code Development Platform — Web Application

A FastAPI + HTMX + Jinja2 web application for managing IECC 2027 code development. Built for Alex Smith, Director of Energy Programs at ICC.

**This app runs on Alex's Windows machine at `localhost:8080`.** It is NOT deployed to any server.

## Quick Start

```
cd web
start.bat          # Windows — double-click or run from terminal
# OR
python main.py     # Direct Python launch
# OR
./run.sh           # Linux/Mac (for development)
```

The server starts at **http://localhost:8080**. It uses `--reload` so file changes auto-restart.

## What This App Does

Two completely separate portals served from one FastAPI app:

### 1. Subgroup Chair Portal
Chairs (e.g., Brian Shanks) log in and see ONLY their subgroup's meetings. They click into a meeting portal to run their subgroup meeting while screen-sharing on Microsoft Teams.

**Flow:** Login → `/home` (my meetings) → `/meeting/{id}/portal` (run meeting) → `/meeting/{id}/review` (verify) → Send to Secretariat

**What the chair does in the portal:**
- Auto-populates agenda with pending proposals for their subgroup
- Steps through each proposal during the meeting
- Records recommendation, vote counts, reason statement
- For "Approved as Modified" — enters modification language
- Reviews all actions, then sends to secretariat (commits to DB)
- Exports: agenda (Word), circulation form (Word), modification document (Word)

### 2. Secretariat Portal
Alex and his staff log in and see everything across both tracks (Commercial + Residential). Full admin view with dashboard, proposal list with filtering, meeting management, and access to all portals.

**Flow:** Login → `/` (dashboard) → `/proposals` or `/meetings` → manage everything

### Authentication
Fake cookie-based auth with preset user accounts (will be replaced with real auth later). Users select their name on a login page, get a cookie, and are routed to the appropriate portal based on role.

**Route guards enforce separation:**
- Chairs cannot access `/`, `/proposals`, `/meetings` — redirected to `/home`
- Secretariat cannot access `/home` — redirected to `/`
- Unauthenticated users — redirected to `/login`

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI (Python) with Jinja2 templates |
| Frontend | Server-rendered HTML + HTMX for dynamic updates |
| Database | SQLite with WAL mode (`iecc.db` — one directory up) |
| Styling | Custom CSS dark theme (no framework) |
| Documents | Node.js `docx` library via subprocess for Word generation |
| Server | Uvicorn with `--reload` |

## File Structure

```
web/
├── main.py                 # FastAPI app, middleware, auth enforcement
├── config.py               # DB path, port, domain constants, body-to-subgroup mapping
├── start.bat               # Windows launcher
├── run.sh                  # Linux launcher
├── requirements.txt        # Python dependencies
│
├── db/
│   ├── connection.py       # SQLite connection manager (WAL mode, row factory)
│   └── queries.py          # All SQL queries as named constants
│
├── routes/
│   ├── auth.py             # Login/logout, user accounts, session management
│   ├── helpers.py          # render() helper — injects user + base_template into all responses
│   ├── dashboard.py        # Secretariat dashboard (GET /)
│   ├── proposals.py        # Proposal list + detail (GET /proposals, /proposals/{id})
│   ├── meetings.py         # Meeting list + detail + create (GET/POST /meetings)
│   ├── subgroup_portal.py  # Chair meeting portal + Go Live presentation mode
│   ├── meeting_docs.py     # Meeting document upload/view for Go Live display
│   ├── exports.py          # Word document generation endpoints
│   └── circforms.py        # Circ form review queue (secretariat-only)
│
├── services/
│   ├── doc_generator.py    # Agenda, circ form, modification doc generators (Node.js)
│   ├── pdf_generator.py    # DOCX→PDF conversion with LibreOffice, DOCX fallback
│   └── sharepoint.py       # SharePoint Graph API upload (dormant until Azure AD configured)
│
├── templates/
│   ├── base.html           # Secretariat base template (Dashboard/Proposals/Meetings nav)
│   ├── chair_base.html     # Chair base template (My Meetings nav, no admin links)
│   ├── login.html          # Standalone login page (no base template)
│   ├── chair_home.html     # Chair's landing page — their meetings + stats
│   ├── dashboard.html      # Secretariat dashboard — counts, pending, upcoming
│   ├── proposal_list.html  # Filterable proposal table
│   ├── proposal_detail.html # Single proposal with timeline
│   ├── meetings.html       # Meeting list with track filter + create form
│   ├── meeting_detail.html # Single meeting with its proposals
│   ├── meeting_portal.html # THE CORE — chair's live meeting management
│   ├── meeting_go_live.html # Go Live — full-screen presentation mode for Teams
│   ├── meeting_review.html # Review staged actions before sending
│   ├── circ_forms.html     # Circ form review queue (secretariat)
│   └── partials/
│       ├── action_saved.html    # HTMX partial — returned after staging an action
│       ├── action_unstaged.html # HTMX partial — inline edit form with pre-filled values
│       ├── action_error.html    # HTMX partial — validation error on action
│       ├── circform_row.html    # HTMX partial — circ form row after approve/reject
│       ├── go_live_staged.html   # HTMX partial — Go Live action card after staging
│       ├── go_live_unstaged.html # HTMX partial — Go Live inline edit form
│       └── proposal_rows.html   # HTMX partial — filtered proposal table rows
│
└── static/
    ├── css/main.css        # All styles (dark theme, cards, tables, portal, badges)
    ├── css/go-live.css     # Go Live presentation mode styles (big text, vote counters)
    ├── js/htmx.min.js      # HTMX library
    └── favicon.svg         # ICC-themed SVG favicon
```

## Dependencies

**Python** (in `requirements.txt`):
- fastapi
- uvicorn
- jinja2
- python-multipart (form handling)

**Node.js** (global):
- docx (`npm install -g docx`) — for Word document generation

**Database:**
- `iecc.db` must exist one directory up (`../iecc.db` relative to `web/`)
- Contains commercial + residential proposals (run `python3 iecc_preflight.py` from parent dir for live counts)
- See `AGENT_GUIDE.md` in parent directory for full schema

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `IECC_DB_PATH` | `../iecc.db` | Path to SQLite database |
| `IECC_PORT` | `8080` | Server port |
| `SP_TENANT_ID` | (none) | Azure AD tenant ID for SharePoint upload |
| `SP_CLIENT_ID` | (none) | Azure AD app client ID |
| `SP_CLIENT_SECRET` | (none) | Azure AD app client secret |

## Preset User Accounts

Defined in `routes/auth.py` USERS dict. 17 accounts total:

| Role | Count | Examples |
|------|-------|---------|
| Secretariat | 3 | Alex Smith, Jason Toves, Kevin Rose |
| Residential Chairs | 8 | Brian Shanks (SG2), Rick Madrid (SG6), Envelope/EPLR/Admin/EB chairs, Consensus chair |
| Commercial Chairs | 5 | Admin, Envelope, EPLR, HVACR, Modeling chairs |
| Consensus Chair | 1 | Duane Jonlin (both tracks) |

See `routes/auth.py` for the full USERS dict with names, bodies, and tracks.

## Key Domain Concept: Body-to-Subgroup Mapping

Meeting bodies and proposal subgroup names don't always match. The residential side uses abbreviated names in the proposals table (e.g., "Modeling (SG2)") but full names in the meetings table (e.g., "Residential Modeling Subgroup"). The `config.BODY_TO_SUBGROUP` mapping handles this translation. `config.resolve_subgroup()` converts meeting body names to proposal subgroup names for correct SQL joins.
