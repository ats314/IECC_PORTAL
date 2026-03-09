# Development Guide — Current State & Next Steps

> **Last updated:** 2026-03-05, Session 29

## What's DONE and Working

### Secretariat Portal (admin view)
- [x] Dashboard at `/` — proposal counts by track, pending by subgroup (clickable), upcoming meetings, recent actions with vote counts (F-A-NV), DQ flags
- [x] Dashboard in-progress meetings section — shows meetings with staged actions, progress count, direct portal link
- [x] Proposal list at `/proposals` — HTMX filtering by track, status, subgroup dropdown, phase, live search with 350ms debounce
- [x] Proposal detail at `/proposals/{canonical_id}` — full info with action timeline
- [x] Meeting list at `/meetings` — track filter, 12h time formatting, create meeting form with validation, delete scheduled meetings, notes tooltip, phase formatting
- [x] Meeting detail at `/meetings/{id}` — pending proposals for that body

### Subgroup Chair Portal (meeting management)
- [x] Chair home at `/home` — stats cards, upcoming meetings sorted ascending (nearest first) with agenda count badges and color-coded progress, completed meetings with export links
- [x] Meeting portal at `/meeting/{id}/portal` — the core feature:
  - [x] Auto-populate agenda from pending proposals
  - [x] Manual add/remove individual proposals
  - [x] Reorder agenda (drag-and-drop ready, API exists at `/meeting/{id}/agenda/reorder`)
  - [x] Clear entire agenda
  - [x] Accordion action forms — staged actions collapse to a summary card, click to expand
  - [x] Action entry form per proposal (recommendation, votes, reason, modification text)
  - [x] Modification text field shows/hides based on recommendation selection
  - [x] HTMX staging — form submits without page reload, progress bar updates via OOB swap
  - [x] HTMX inline edit — Edit button on staged actions returns pre-filled form (previous values preserved)
  - [x] Finalize bar with remaining count + export buttons
- [x] Review page at `/meeting/{id}/review` — summary table with breadcrumbs, inline edit buttons, partial-completion warning
- [x] Send to secretariat — commits staging to `subgroup_actions`, marks meeting COMPLETED, auto-generates circ form document
- [x] Completed meeting view — shows committed actions in read-only mode

### Document Exports
- [x] Agenda export (Word) — `/meeting/{id}/export-agenda`
- [x] Circulation form export (Word) — `/meeting/{id}/export-circform`
- [x] Modification document export (Word) — `/meeting/{id}/export-modifications`
  - Per-proposal pages with metadata tables
  - Modification language in Courier New
  - cdpACCESS entry checklist
  - Purple button in finalize bar and on completed meetings

### Circulation Form Pipeline (Session 25)
- [x] Auto-generation of circ form documents when chair clicks "Send to Secretariat"
- [x] PDF generation via LibreOffice headless with DOCX fallback (Windows compatibility)
- [x] `circ_forms` DB table tracking lifecycle: pending_review → approved/uploaded → rejected
- [x] Secretariat review queue on dashboard — "Pending Circ Forms" section with Preview/Approve/Reject
- [x] Full circ forms page at `/circ-forms` — pending and reviewed sections
- [x] HTMX inline approve/reject with status badge swap
- [x] Document preview (inline PDF or attachment DOCX) and download routes
- [x] SharePoint Graph API upload service (dormant until Azure AD credentials configured)
  - OAuth2 client credentials via `msal`
  - Auto-files to correct subgroup meeting folder
  - Three-layer name mapping: meeting body → proposal subgroup → SharePoint folder
- [x] Graceful degradation — works fully without SharePoint, LibreOffice, or any external dependencies

### Authentication & Role Separation
- [x] Login page with user selection (grouped by role)
- [x] Cookie-based session (`icc_user` cookie, 7-day expiry)
- [x] Middleware enforces login on all routes except /login, /health, /static
- [x] Route guards: chairs can't see secretariat pages, secretariat can't see chair home
- [x] Two separate base templates (chair_base.html vs base.html)
- [x] Dynamic template inheritance (portal/review adapt to logged-in role)
- [x] User name + Sign Out in navbar for both portals
- [x] SVG favicon for both portals

### UI Polish (Session 23/24)
- [x] Shared CSS utility classes in main.css (btn-group, btn-mods, btn-xs, btn-sm, text-sm, text-muted, breadcrumb, notes-tooltip) — removed duplication from individual template `<style>` blocks
- [x] Breadcrumb navigation on review page
- [x] Phase name formatting throughout (`CODE_PROPOSAL` → `Code Proposal`)

---

## What's NOT Built Yet

### Priority 1: SharePoint Azure AD Setup
The SharePoint upload service is built but dormant. Alex needs to register an Azure AD app with `Sites.ReadWrite.All` permission and set `SP_TENANT_ID`, `SP_CLIENT_ID`, `SP_CLIENT_SECRET` environment variables. See `services/sharepoint.py` for details.

### Priority 2: "Go Live" Meeting Mode
Alex wants a presentation-friendly view for when the chair shares their screen on Teams during the meeting. Think of it as a simplified, focused view of the portal designed for visibility on a screen share.

**Requirements discussed:**
- Current proposal prominently displayed (large text for code section, proponent)
- Quick-action buttons for common recommendations
- Big vote counter inputs
- Auto-advance to next proposal after recording action
- Timer/clock visible
- Minimal chrome — maximize content visibility

### Priority 3: Rich Text Modification Editor + Proposal Content — MOSTLY COMPLETE (Session 26 + 29)
The Quill.js rich text editor is integrated into the portal. Chairs can use underline (additions) and strikethrough (deletions) when entering modification text, matching ICC markup conventions. HTML is stored in modification_text and renders properly in review pages, proposal detail, and Word document exports.

**Session 29 additions:** Centralized content database built. Proposals now have extracted code language with ICC legislative markup (`<ins>`/`<del>` tags) in the `proposal_text` table. The meeting portal shows proposal language panels, pre-submitted modification panels, cross-reference chips, and "Load into Editor" buttons that pre-populate the Quill editor with the actual proposal text. Query `SELECT COUNT(*) FROM proposal_text` for current coverage.

**What's done:**
- [x] Quill.js editor with toolbar (bold, underline, strikethrough, lists, clean), dark theme, HTMX integration
- [x] HTML rendering in all display contexts, Word doc generators parse HTML into proper formatting
- [x] Code language extraction — `populate_content.py` extracts from cdpACCESS DOCX files into `proposal_text` table (query DB for current coverage)
- [x] Pre-loaded code language — "Load Original Proposal Text" button loads extracted text into Quill editor
- [x] Pre-submitted modifications — "Load into Editor" button loads modification text and auto-sets recommendation to "Approved as Modified"
- [x] Cross-reference chips — proposals modifying the same code section linked via `proposal_links` (auto-detected relationships)

**What's NOT done yet:**
1. **Coverage gap** — Not all proposals have extracted text. PUBLIC_INPUT phase proposals mostly lack DOCX files. Could backfill from monograph PDF.
2. **"Go Live" mode** — the editor needs to be optimized for Teams screen sharing with bigger fonts and clearer markup visibility

### Priority 4: cdpACCESS Integration
cdpACCESS is ICC's official code development platform. Currently the modification document export is a Word doc that staff manually reference when entering data into cdpACCESS. Direct API integration was discussed but deferred until Alex talks to the CDP team.

**Short-term bridge (built):** Word document export that staff use as reference while entering into cdpACCESS manually.

### Priority 5: More Chair Accounts
Currently only Residential Modeling SG2 chairs (Brian Shanks, Robert Howard) exist. Need to add chairs for all subgroups across both tracks. The USERS dict in `routes/auth.py` is the place to add them.

### Priority 6: Consensus Committee Chair Portal
A third role type for consensus committee chairs who manage the final hearing. Not yet designed.

### Future: Real Authentication
Replace fake login with Microsoft SSO (all ICC staff are on Microsoft). The middleware pattern is already in place — just need to swap the cookie-based auth for real OAuth tokens.

---

## Known Issues & Gotchas

### HTMX + Chrome Extension Screenshot Bug
After HTMX form submissions, the Chrome extension (Claude in Chrome) loses DOM handles and screenshots fail with "Detached while handling command." This is a browser extension limitation, not our bug. Workaround: navigate to a different page or reload.

### Body-to-Subgroup Name Mismatch
Residential meeting bodies don't match proposal subgroup names. "Residential Modeling Subgroup" in the meetings table maps to "Modeling (SG2)" in the proposals table. The `config.BODY_TO_SUBGROUP` dict handles this. **If you add new meeting bodies, you MUST add them to this mapping or agenda auto-populate will find zero proposals.**

### Staging Table Cleanup
If a meeting's staged actions are never sent (chair abandons the meeting), the `sg_action_staging` rows remain. There's no cleanup job. The "Clear" button on the agenda removes both agenda items and staged actions for that meeting.

### Meeting Status
Meetings are `SCHEDULED`, `COMPLETED`, or `CANCELLED`. There's no "in progress" state. Once "Send to Secretariat" is clicked, it's COMPLETED and cannot be undone from the UI. CANCELLED meetings (6 in the DB) were past-date meetings with no linked records, resolved in Session 30.

### Node.js Dependency for Docs
Document generation shells out to Node.js (`node` must be on PATH). If Node.js isn't installed, export buttons will fail with a subprocess error. The `docx` npm package must be globally installed (`npm install -g docx`).

### LibreOffice for PDF Conversion
The circ form pipeline tries to convert DOCX to PDF via LibreOffice headless. If LibreOffice isn't installed (likely on Alex's Windows machine), it falls back to DOCX. Circ forms will work either way — just the file format changes. To install: https://www.libreoffice.org/download/

### Generated Files Directory
Circ form documents are saved to `web/generated/circforms/`. If that directory isn't writable (e.g., sandboxed environments), they go to a system temp directory instead. The `circ_forms.pdf_path` column stores the absolute path.

### Port Conflict
The server runs on port 8080. If something else is using that port, change `IECC_PORT` env var or edit `config.py`.

---

## Code Patterns

### Adding a New Route
1. Create or edit a file in `routes/`
2. Import `render` from `routes.helpers`
3. Use `render(request, "template.html", {context})` — never use `templates.TemplateResponse` directly for full pages (partials are OK)
4. Register the router in `main.py` with `app.include_router()`
5. If the route should be secretariat-only, add the path to `secretariat_paths` in the middleware

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

### Adding a New Document Export
1. Add generator function in `services/doc_generator.py`
2. Add route in `routes/exports.py`
3. Add button in the relevant template(s)

### Adding a New Circ Form Status
The `circ_forms.status` column uses: `pending_review`, `approved`, `uploaded`, `rejected`. If adding a new status, update: `db/queries.py` queries, `routes/circforms.py` logic, `templates/circ_forms.html` and `partials/circform_row.html` badge rendering.

### Template Variables Available Everywhere (via render())
- `request` — the FastAPI Request object
- `user` — logged-in user dict (or None)
- `base_template` — "chair_base.html" or "base.html" based on role
