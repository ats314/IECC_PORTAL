# LLM Handoff Document

> **You are a new AI agent continuing development of the ICC Code Development Platform.**
> **Read this ENTIRE file before doing anything.** Then read the files it references.

## Mandatory First Steps

1. Read `web/README.md` — what the app is, how to run it, file structure
2. Read `web/ARCHITECTURE.md` — request lifecycle, auth system, template inheritance, DB tables
3. Read `web/DEVELOPMENT.md` — what's built, what's NOT built, known issues, code patterns
4. Read `docs/AGENT_GUIDE.md` (parent dir) — database schema, domain knowledge, naming traps
5. Read `docs/PROJECT_MEMORY.md` (parent dir) — full session history, decisions made
6. Run the server: `cd web && python main.py` (or user double-clicks `start.bat`)
7. Tell the user: "I've read the project docs. Ready to continue."

**DO NOT** explore the codebase blindly. Everything is documented. If you need to understand a file, read the specific file — don't do broad searches.

---

## Who You're Working For

**Alex Smith** — Director of Energy Programs, ICC (International Code Council). He manages the secretariat process for the IECC 2027 code development cycle. He is technical, opinionated, and direct. He will curse at you if you waste his time. He values:

- **Common sense** — don't overcomplicate things
- **Precision** — use correct terminology (proposals, recommendations, subgroups)
- **Separation of concerns** — the two portals are COMPLETELY SEPARATE
- **Iteration** — build, test, improve, repeat
- **Don't reinvent** — enhance what exists, don't rebuild

---

## Critical Rules (Learned the Hard Way)

### 1. TWO SEPARATE PORTALS
The subgroup chair portal and the secretariat portal are **completely different applications** that happen to share a FastAPI backend. A chair should NEVER see secretariat features. A secretariat user should NEVER see the chair home page. They have different base templates, different navbars, different everything.

**Do not:**
- Combine them into one view
- Add secretariat links to the chair nav
- Add chair-specific features to the secretariat dashboard
- Talk about them as if they're one thing

### 2. DON'T REINVENT THE WHEEL
The chair portal at `/meeting/{id}/portal` is BUILT AND WORKING. The secretariat pages (dashboard, proposals, meetings) are BUILT AND WORKING. If Alex asks you to "improve" or "complete" something, he means enhance what exists — not build a new version from scratch.

### 3. ASK BEFORE BIG CHANGES
If you're about to refactor architecture, change the database schema, or restructure templates — stop and ask Alex first. He's had bad experiences with AI agents making sweeping changes without checking.

### 4. TEST IN THE BROWSER
The app runs on Alex's Windows machine at localhost:8080. After making changes, verify they work in the browser. If you have Claude in Chrome access, take screenshots and check that pages render correctly.

### 5. BODY-TO-SUBGROUP MAPPING IS CRITICAL
Residential meeting body names don't match proposal subgroup names in the database. The mapping in `config.BODY_TO_SUBGROUP` is the bridge. If this breaks, agenda auto-populate returns zero proposals and the portal is useless.

### 6. UNDERSTAND THE DOCUMENT CHAIN BEFORE TOUCHING PROPOSALS
Read `docs/AGENT_GUIDE.md → The IECC Code Development Lifecycle` and `The Document Chain` sections. Every proposal modifies the Public Comment Draft (PCD) — the base code text for all active proposals. Proposals show code sections with underline (additions) and strikethrough (deletions) against the PCD. Subgroups may further modify the proposal language. If you don't understand this chain, you will build the wrong thing.

---

## Architecture Quick Reference

```
User clicks login → sets cookie → middleware reads cookie on every request
    → Chair? → /home shows their meetings → /meeting/{id}/portal runs meeting
    → Secretariat? → / shows dashboard → /proposals /meetings manage everything
    → No cookie? → redirect to /login
```

**Key files to understand:**
| File | What It Does |
|------|-------------|
| `main.py` | App setup, middleware (auth enforcement, route guards) |
| `config.py` | Constants, BODY_TO_SUBGROUP mapping, SUBGROUP_TO_SP_FOLDER, SharePoint config, recommendations list |
| `routes/auth.py` | User accounts (USERS dict), login/logout, chair home page |
| `routes/helpers.py` | `render()` function — use this, not TemplateResponse directly |
| `routes/subgroup_portal.py` | The entire chair meeting workflow (agenda, staging, review, send → auto-generates circ form) |
| `routes/circforms.py` | Circ form review queue (secretariat-only): list, preview, download, approve, reject |
| `routes/dashboard.py` | Secretariat dashboard (in-progress meetings, pending circ forms, pending by subgroup, recent actions) |
| `routes/meetings.py` | Meeting list, create, delete |
| `routes/proposals.py` | Proposal list with filters, proposal detail |
| `services/pdf_generator.py` | Circ form document generation (DOCX→PDF via LibreOffice, or DOCX fallback) |
| `services/sharepoint.py` | SharePoint Graph API upload (dormant until Azure AD credentials configured) |
| `services/doc_generator.py` | Word document generators (agenda, circform DOCX, modifications) |
| `db/queries.py` | Every SQL query used by the app (including circ_forms CRUD) |

**Key partials (HTMX):**
| File | What It Does |
|------|-------------|
| `partials/action_saved.html` | Shown after staging an action — collapsed card with HTMX Edit button |
| `partials/action_unstaged.html` | Shown after clicking Edit — pre-filled form for re-staging |
| `partials/circform_row.html` | Circ form row after approve/reject — status badge swap |
| `partials/proposal_rows.html` | Proposal table rows (HTMX target for filter updates) |

**Template decision tree:**
- Chair logged in → `chair_base.html` (nav: My Meetings + name + Sign Out)
- Secretariat logged in → `base.html` (nav: Dashboard + Proposals + Meetings + name + Sign Out)
- Portal/review pages → use `base_template` variable (set by `render()`) to pick correct base

---

## Circulation Form Pipeline (Session 25 — NEW)

### How It Works
1. Chair completes a meeting via the portal → clicks "Send to Secretariat"
2. Actions are committed to `subgroup_actions` and a circ form document is auto-generated
3. Circ form appears on the secretariat dashboard under "Pending Circ Forms"
4. Secretariat can **Preview**, **Approve**, or **Reject** the circ form
5. If SharePoint credentials are configured, "Approve" also uploads to the correct SharePoint folder

### Key Details
- **Document format:** PDF if LibreOffice is installed, DOCX fallback if not. Alex's Windows machine likely uses DOCX fallback.
- **DB table:** `circ_forms` — tracks lifecycle (pending_review → approved/uploaded → rejected)
- **SharePoint upload:** Dormant by default. Requires Azure AD app registration with `Sites.ReadWrite.All`. Set env vars: `SP_TENANT_ID`, `SP_CLIENT_ID`, `SP_CLIENT_SECRET`.
- **Folder mapping:** `config.SUBGROUP_TO_SP_FOLDER` maps DB subgroup names to SharePoint folder names. Target path: `Shared Documents/.../Residential Subgroups/{subgroup folder}/{YY-MM-DD Meeting}/`
- **Routes:** All under `/circ-forms/*` — registered in `main.py`, guarded by secretariat middleware

### Name Mapping Chain (3 layers)
```
Meeting body name → config.BODY_TO_SUBGROUP → Proposal subgroup name
Proposal subgroup name → config.SUBGROUP_TO_SP_FOLDER → SharePoint folder name
```
Example: "Residential Modeling Subgroup" → "Modeling (SG2)" → "Modeling Subgroup"

---

## What's Been Built Since Session 29

### "Go Live" Meeting Mode — DONE (Session 34)
Full-viewport presentation view at `/meeting/{id}/go-live` designed for Teams screen sharing. Features: large proposal text, quick-action buttons, big vote counters, auto-advance after staging, timer/clock, keyboard shortcuts (1-5, U, arrow keys), modification panels, cross-reference chips, readiness badges. Route: `GET /meeting/{id}/go-live`, `POST /meeting/{id}/go-live/stage`.

### Testing Mode — DONE (Session 34)
Secretariat can toggle `proposals.testing` flag via `POST /proposals/{canonical_id}/toggle-testing`. Proposals marked Testing appear in chair portal agendas for demo purposes without affecting real data. UI buttons on proposal detail page.

### Modification Approval Workflow — DONE (Session 34)
Secretariat approves modifications before chairs see them. `POST /proposals/{canonical_id}/toggle-mod-approval/{mod_id}` toggles `modifications.secretariat_approved`. Unapproved mods shown with 0.6 opacity in chair portal.

### All Chair Accounts — DONE (Session 34)
16 users total in `routes/auth.py`: 2 secretariat, 8 residential chairs (all subgroups + consensus), 6 commercial chairs (all subgroups + Duane Jonlin consensus chair).

### ICC Brand Theme — DONE (Session 33/34)
CSS variables (`--icc-blue`, `--icc-green`, `--icc-dark`, etc.) applied across all templates. Fixed stale `--icc-light` references in 6 templates.

---

## What Alex Will Likely Ask You To Build Next

Based on current state (see docs/PROJECT_MEMORY.md and docs/PORTAL_ROADMAP.md):

### SharePoint Azure AD Setup
Alex needs to register an Azure AD app with `Sites.ReadWrite.All` permission to enable SharePoint upload. The upload service is built and dormant. See `services/sharepoint.py`.

### Meeting Action Capture Redesign (Phase 2 Step 6)
Current staging handles simple cases but not: "Approve as Further Modified," withdrawals, combined consideration, or superseded actions. See `docs/PORTAL_ROADMAP.md` Phase 2 Step 6.

### Transcript Extraction Pipeline (Phase 3 Step 9)
Upload meeting DOCX transcripts → LLM extracts votes, reason statements, modifications → present for review → import. The `meeting_events` table schema exists but is empty.

### cdpACCESS Integration
ICC's official code platform. Currently we export Word docs that staff use as reference for manual data entry. Direct API integration deferred until Alex talks to the CDP team.

### Reorder Agenda via Drag & Drop
The API endpoint exists (`/meeting/{id}/agenda/reorder`) but there's no drag-and-drop UI yet. Currently agenda items are ordered by the order they were added.

---

## Key Architectural Pattern: Content Loading in Meeting Portal

The meeting portal batch-loads content from three tables for all agenda items:
```python
# In subgroup_portal.py meeting_portal():
uids = [item["proposal_uid"] for item in agenda]
placeholders = ",".join("?" * len(uids))
# Load proposal text
sql = queries.PROPOSAL_TEXT_FOR_MEETING.format(placeholders=placeholders)
# Load modifications
sql = queries.MODIFICATIONS_FOR_PROPOSALS.format(placeholders=placeholders)
# Load cross-references (needs uids twice for both FK columns)
sql = queries.PROPOSAL_LINKS_FOR_PROPOSALS.format(placeholders=placeholders)
```
Each agenda item gets annotated with `item["content"]`, `item["modifications"]`, and `item["links"]` dicts. The template renders these as collapsible panels, badges, and interactive buttons. CSS classes: `.badge-content`, `.badge-mod-available`, `.proposal-text-panel`, `.cross-refs`, `.cross-ref-chip`.

---

## Testing Checklist

After making changes, verify:

1. **Login page** — `/login` shows user selection, both roles visible
2. **Chair login** — select Brian Shanks → lands on `/home` with sorted meetings, agenda/progress columns
3. **Chair route guard** — navigate to `/` → should redirect to `/home`
4. **Portal access** — click "Open Portal" → portal loads with correct proposals
5. **Action staging** — enter a recommendation → accordion collapses, progress bar updates via OOB swap
6. **HTMX inline edit** — click Edit on a staged action → form re-opens with previous values pre-filled
7. **Review page** — click "Review & Finalize" → shows staged actions, breadcrumbs, partial-completion warning if applicable
8. **Secretariat login** — sign out, sign in as Alex Smith → lands on `/` dashboard
9. **Dashboard** — shows in-progress meetings section (if any), vote counts in recent actions
10. **Secretariat route guard** — navigate to `/home` → should redirect to `/`
11. **Proposals page** — subgroup dropdown filter works, live search with debounce works
12. **Meetings page** — delete button on scheduled meetings, notes tooltip, phase formatting
13. **Portal from secretariat** — navigate to `/meeting/{id}/portal` → works with secretariat nav
14. **Exports** — click any export button → downloads a .docx file
15. **Circ form pipeline** — complete a meeting as chair → sign in as secretariat → circ form appears on dashboard → Preview/Approve/Reject work
16. **Circ forms page** — `/circ-forms` shows all forms with pending/reviewed sections
17. **Go Live mode** — click "Go Live" on meeting portal → full-viewport presentation view, keyboard shortcuts (1-5, U, arrows), auto-advance after staging
18. **Testing mode** — as secretariat on proposal detail, toggle "Mark as Testing" → proposal appears in chair portal agendas for demo
19. **Modification approval** — as secretariat on proposal detail, toggle "Approve" on a modification → unapproved mods show with 0.6 opacity in chair portal

---

## Common Tasks

### Restart the server
Close the terminal window and double-click `start.bat` (Windows). Or `Ctrl+C` then `python main.py`.

### Add a new page
1. Create template in `templates/` extending `base_template|default("base.html")`
2. Add route in `routes/` using `render()` from `routes.helpers`
3. Register router in `main.py` if new file
4. Add route guard in middleware if secretariat-only

### Change the database
The DB is `../iecc.db` (one dir up from `web/`). The web app creates `sg_action_staging`, `meeting_agenda_items`, and `circ_forms` tables. Don't modify other tables without understanding the CLI tools that also use them.

### Debug a query
All queries are in `db/queries.py`. You can test them directly:
```python
from db.connection import get_db
with get_db() as conn:
    rows = conn.execute("SELECT ...", params).fetchall()
    for r in rows:
        print(dict(r))
```
