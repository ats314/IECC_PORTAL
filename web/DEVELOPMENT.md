# Web App Development Guide

> **Last updated:** 2026-03-10, Session 34
> **This is the single reference for web app development.** For database schema and ICC domain knowledge, see `AGENT_GUIDE.md` in the parent directory.

---

## Critical Rules

### 1. TWO SEPARATE PORTALS
The chair portal and secretariat portal are **completely different applications** sharing a FastAPI backend. They have different base templates, different navbars, different everything.

**Do not:**
- Combine them into one view
- Add secretariat links to the chair nav
- Add chair-specific features to the secretariat dashboard

### 2. DON'T REBUILD — ENHANCE
Everything listed in "What's DONE" below is built and working. If asked to "improve" something, enhance what exists — don't build from scratch.

### 3. ASK BEFORE BIG CHANGES
Stop and ask before refactoring architecture, changing the database schema, or restructuring templates.

### 4. BODY-TO-SUBGROUP MAPPING
Residential meeting body names don't match proposal subgroup names. The mapping in `config.BODY_TO_SUBGROUP` is the bridge. If this breaks, agenda auto-populate returns zero proposals.

```
Meeting body name → config.BODY_TO_SUBGROUP → Proposal subgroup name
Proposal subgroup name → config.SUBGROUP_TO_SP_FOLDER → SharePoint folder name
```
Example: `"Residential Modeling Subgroup"` → `"Modeling (SG2)"` → `"Modeling Subgroup"`

**If you add new meeting bodies, you MUST update `config.BODY_TO_SUBGROUP`** or the portal will silently show empty agendas.

### 5. USE `render()`, NOT `TemplateResponse`
Always use `render(request, "template.html", {context})` from `routes.helpers` for full pages. Direct `TemplateResponse` is OK only for HTMX partials.

### 6. DOCUMENT CHAIN
Read `AGENT_GUIDE.md → The IECC Code Development Lifecycle` before touching proposals. Every proposal modifies the Public Comment Draft (PCD). Proposals use underline (additions) and strikethrough (deletions) markup.

---

## Architecture Quick Reference

```
User clicks login → sets cookie → middleware reads cookie on every request
    → Chair? → /home shows their meetings → /meeting/{id}/portal runs meeting
    → Secretariat? → / shows dashboard → /proposals /meetings manage everything
    → No cookie? → redirect to /login
```

**Route access:**
| Route | Secretariat | Chair | No Login |
|-------|-------------|-------|----------|
| `/login`, `/health`, `/static` | Yes | Yes | Yes |
| `/` (dashboard) | Yes | → `/home` | → `/login` |
| `/proposals*`, `/meetings*`, `/circ-forms` | Yes | → `/home` | → `/login` |
| `/home` | → `/` | Yes | → `/login` |
| `/meeting/*/portal`, `/meeting/*/go-live` | Yes | Yes | → `/login` |
| `/meeting/*/review`, `/meeting/*/export-*` | Yes | Yes | → `/login` |
| `/meeting/*/documents/*`, `/meeting/*/stage` | Yes | Yes | → `/login` |

**Template decision tree:**
- Chair → `chair_base.html` (nav: My Meetings + name + Sign Out)
- Secretariat → `base.html` (nav: Dashboard + Proposals + Meetings + Circ Forms + name + Sign Out)
- Portal/review pages → `{% extends base_template|default("base.html") %}` adapts to role

---

## Key Files

| File | What It Does |
|------|-------------|
| `main.py` | App setup, middleware (auth enforcement, route guards) |
| `config.py` | Constants, BODY_TO_SUBGROUP, SUBGROUP_TO_SP_FOLDER, SharePoint config, recommendations list |
| `routes/auth.py` | 17 user accounts (USERS dict), login/logout, chair home page |
| `routes/helpers.py` | `render()` — injects user + base_template into all responses |
| `routes/subgroup_portal.py` | Chair meeting workflow: agenda, staging, review, send → auto-generates circ form. Also Go Live mode. |
| `routes/meeting_docs.py` | Document upload/delete/rename/view for Go Live display |
| `routes/circforms.py` | Circ form review queue (secretariat-only): list, preview, approve, reject |
| `routes/dashboard.py` | Secretariat dashboard (in-progress meetings, pending circ forms, pending by subgroup, recent actions) |
| `routes/meetings.py` | Meeting list, create, delete |
| `routes/proposals.py` | Proposal list with filters, proposal detail |
| `routes/exports.py` | Word document generation endpoints |
| `services/doc_generator.py` | Word document generators (agenda, circform, modifications) — shells out to Node.js |
| `services/pdf_generator.py` | DOCX→PDF via LibreOffice, DOCX fallback |
| `services/sharepoint.py` | SharePoint Graph API upload (dormant until Azure AD configured) |
| `db/queries.py` | Every SQL query as named constants |
| `db/connection.py` | SQLite connection manager (WAL mode, row factory, schema init) |

**HTMX Partials:**
| File | What It Does |
|------|-------------|
| `partials/action_saved.html` | Staged action collapsed card with Edit button |
| `partials/action_unstaged.html` | Inline edit form with pre-filled values |
| `partials/go_live_staged.html` | Go Live version of action_saved |
| `partials/go_live_unstaged.html` | Go Live version of action_unstaged |
| `partials/circform_row.html` | Circ form row after approve/reject |
| `partials/proposal_rows.html` | Filtered proposal table rows |

---

## What's DONE and Working

### Secretariat Portal
- [x] Dashboard at `/` — proposal counts, pending by subgroup, upcoming meetings, recent actions with vote counts, DQ flags, in-progress meetings section
- [x] Proposal list at `/proposals` — HTMX filtering by track, status, subgroup, phase, live search with 350ms debounce
- [x] Proposal detail at `/proposals/{canonical_id}` — full info with action timeline
- [x] Meeting list at `/meetings` — track filter, create, delete, notes tooltip
- [x] Meeting detail at `/meetings/{id}` — pending proposals for that body

### Chair Portal
- [x] Chair home at `/home` — upcoming meetings sorted by date, agenda count badges, color-coded progress, completed meetings with export links
- [x] Meeting portal at `/meeting/{id}/portal` — auto-populate agenda, manual add/remove, accordion action forms, HTMX staging with OOB progress bar updates, inline edit, finalize bar
- [x] Review page at `/meeting/{id}/review` — summary table, breadcrumbs, inline edit, partial-completion warning
- [x] Send to secretariat — commits to `subgroup_actions`, marks COMPLETED, auto-generates circ form
- [x] Completed meeting view — read-only committed actions

### Go Live Presentation Mode
- [x] Full-screen view at `/meeting/{id}/go-live` for Teams screen sharing
- [x] Big text, vote counters with +/- buttons, quick-action recommendation buttons
- [x] Auto-advance, keyboard navigation, timer/clock
- [x] Proposal text and modification panels with ICC legislative markup
- [x] Dedicated CSS (`go-live.css`) and HTMX partials

### Meeting Documents
- [x] Upload at `/meeting/{id}/documents/upload` — PDFs and images for Go Live display
- [x] Manage — rename, delete, reorder. View inline at `/meeting/{id}/documents/{id}/view`
- [x] `meeting_documents` DB table, file validation, safe filename generation

### Centralized Content
- [x] `proposal_text` table — extracted code language with ICC markup (`<ins>`/`<del>`)
- [x] `modifications` table — pre-submitted modifications with "Load into Editor" buttons
- [x] `proposal_links` table — auto-detected cross-references, rendered as chips
- [x] Batch content loading in portal via `_load_portal_data()`

### Document Exports
- [x] Agenda (Word), Circulation form (Word), Modification document (Word)
- [x] Rich text HTML→Word formatting (underline, strikethrough, bold)

### Circulation Form Pipeline
- [x] Auto-generation on "Send to Secretariat" (PDF via LibreOffice or DOCX fallback)
- [x] `circ_forms` table: `pending_review` → `approved`/`uploaded` → `rejected`
- [x] Secretariat review queue with Preview/Approve/Reject
- [x] SharePoint upload service (dormant until Azure AD credentials set)

### Auth & UI
- [x] 17 preset user accounts (3 secretariat + 14 chairs across all subgroups)
- [x] Cookie-based sessions, middleware route guards, two separate base templates
- [x] Quill.js rich text editor with ICC markup conventions
- [x] SVG favicon, shared CSS utility classes, dark theme

---

## What's NOT Built Yet

### Priority 1: SharePoint Azure AD Setup
Upload service is built but dormant. Requires Azure AD app with `Sites.ReadWrite.All` and env vars `SP_TENANT_ID`, `SP_CLIENT_ID`, `SP_CLIENT_SECRET`. See `services/sharepoint.py`.

### Priority 2: "Further Modified" / Combined Consideration
Portal can't capture: further modifications (mod rejected, new one crafted live), combined consideration, superseded proposals, mid-meeting withdrawals. See `PORTAL_ROADMAP.md` Phase 2, Step 6.

### Priority 3: Transcript Extraction
`meeting_events` table exists but is empty. Plan: upload DOCX transcript → LLM extracts structured data → review → import. See `PORTAL_ROADMAP.md` Phase 3, Step 9.

### Priority 4: Meeting Prep Dashboard
Pre-meeting view showing content readiness per proposal. Not yet built.

### Priority 5: cdpACCESS Integration
Direct API integration deferred. Word document export serves as manual bridge.

### Priority 6: Consensus Committee Chair Portal
Third role type for consensus chairs. Not designed.

### Future: Real Authentication
Replace fake login with Microsoft SSO. Middleware pattern is ready.

### Future: Drag & Drop Agenda Reorder
API endpoint exists (`/meeting/{id}/agenda/reorder`) but no UI yet.

---

## Testing Checklist

After making changes, verify:

1. **Login** — `/login` shows user selection, both roles visible
2. **Chair login** — Brian Shanks → `/home` with sorted meetings, agenda/progress columns
3. **Chair route guard** — navigate to `/` → redirects to `/home`
4. **Portal** — "Open Portal" → loads with correct proposals for the chair's subgroup
5. **Action staging** — enter recommendation → accordion collapses, progress bar updates via OOB swap
6. **Inline edit** — Edit button → form with previous values pre-filled
7. **Review page** — "Review & Finalize" → staged actions, breadcrumbs, partial-completion warning
8. **Secretariat login** — Alex Smith → `/` dashboard
9. **Dashboard** — in-progress meetings section, vote counts in recent actions
10. **Secretariat route guard** — navigate to `/home` → redirects to `/`
11. **Proposals** — subgroup dropdown filter, live search with debounce
12. **Meetings** — delete button, notes tooltip, phase formatting
13. **Portal from secretariat** — `/meeting/{id}/portal` → works with secretariat nav
14. **Exports** — download .docx files
15. **Circ form pipeline** — complete meeting as chair → sign in as secretariat → circ form on dashboard → Preview/Approve/Reject
16. **Circ forms page** — `/circ-forms` with pending/reviewed sections
17. **Go Live** — `/meeting/{id}/go-live` with big text, vote counters, auto-advance
18. **Document upload** — upload PDF → appears in Go Live document viewer
19. **Go Live staging** — stage action → card collapses, progress updates, auto-advances

---

## Known Issues

| Issue | Details |
|-------|---------|
| **HTMX + Chrome Extension** | After HTMX submissions, Chrome extension screenshots fail. Workaround: reload page. |
| **Body-to-Subgroup Mismatch** | Residential body names ≠ proposal subgroup names. `config.BODY_TO_SUBGROUP` bridges them. |
| **Staging Cleanup** | Abandoned meetings leave `sg_action_staging` rows. No auto-cleanup. "Clear" button removes them. |
| **Meeting Status** | Only SCHEDULED/COMPLETED/CANCELLED. No "in progress". COMPLETED is irreversible from UI. |
| **Node.js Required** | Document exports shell out to `node`. Must have Node.js + `npm install -g docx`. |
| **LibreOffice Optional** | Circ forms use LibreOffice for PDF. Falls back to DOCX if not installed. |
| **Generated Files Dir** | `web/generated/circforms/` — falls back to system temp if not writable. |
| **Port 8080** | Change with `IECC_PORT` env var or edit `config.py`. |

---

## Code Patterns

### Adding a New Route
1. Create or edit a file in `routes/`
2. Use `render(request, "template.html", {context})` from `routes.helpers`
3. Register the router in `main.py` with `app.include_router()`
4. If secretariat-only, add path to `secretariat_paths` in the middleware

### Adding a New User
Edit `routes/auth.py` USERS dict:
```python
"username.here": {
    "name": "Full Name",
    "role": "chair",  # or "secretariat"
    "title": "Their Title",
    "body": "Meeting Body Name",  # must match meetings table, None for secretariat
    "track": "residential",       # or "commercial", None for secretariat
},
```

### Adding a New Page
1. Create template extending `base_template|default("base.html")`
2. Add route using `render()` (NOT `TemplateResponse`)
3. Register router in `main.py` if new file
4. Add route guard in middleware if secretariat-only

### Adding a New Document Export
1. Add generator function in `services/doc_generator.py`
2. Add route in `routes/exports.py`
3. Add button in the relevant template(s)

### Debugging a Query
All queries are in `db/queries.py`. Test directly:
```python
from db.connection import get_db
with get_db() as conn:
    rows = conn.execute("SELECT ...", params).fetchall()
    for r in rows:
        print(dict(r))
```

### Template Variables (via render())
- `request` — the FastAPI Request object
- `user` — logged-in user dict (or None)
- `base_template` — `"chair_base.html"` or `"base.html"` based on role

### Content Loading Pattern
The meeting portal batch-loads content for all agenda items:
```python
# In subgroup_portal.py _load_portal_data():
uids = [item["proposal_uid"] for item in agenda]
placeholders = ",".join("?" * len(uids))
sql = queries.PROPOSAL_TEXT_FOR_MEETING.format(placeholders=placeholders)
sql = queries.MODIFICATIONS_FOR_PROPOSALS.format(placeholders=placeholders)
sql = queries.PROPOSAL_LINKS_FOR_PROPOSALS.format(placeholders=placeholders)
```
Each item gets `item["content"]`, `item["modifications"]`, and `item["links"]` dicts.

### Circ Form Status Values
`circ_forms.status`: `pending_review` → `approved`/`uploaded` → `rejected`. If adding a new status, update: `db/queries.py`, `routes/circforms.py`, `templates/circ_forms.html`, `partials/circform_row.html`.
