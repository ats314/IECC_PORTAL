# Development Guide — Current State & Next Steps

> **Last updated:** 2026-03-12, Session 36

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

### Approved Circ Forms Auto-Copy + SharePoint Pipeline (Session 36)
- [x] On approve, circ form docs are copied to `approved_circforms/{subgroup_folder}/{YY-MM-DD Meeting}/`
- [x] Folder names match SharePoint structure (`config.SUBGROUP_TO_SP_FOLDER` mapping)
- [x] Default output: OneDrive for Business sync folder (`~/OneDrive - International Code Council/IECC_Approved_CircForms/`)
- [x] Power Automate flow configured: OneDrive trigger → Create file in SharePoint Portal_TEST → Delete from OneDrive → Mobile notification
- [x] Fallback: if OneDrive folder doesn't exist, uses local `approved_circforms/` for manual browser upload
- [x] Configured via `APPROVED_CIRCFORMS_DIR` in `config.py` (env var `IECC_APPROVED_DIR` overrides)

### Authentication & Role Separation
- [x] Login page with user selection (grouped by role)
- [x] Cookie-based session (`icc_user` cookie, 7-day expiry)
- [x] Middleware enforces login on all routes except /login, /health, /static
- [x] Route guards: chairs can't see secretariat pages, secretariat can't see chair home
- [x] Two separate base templates (chair_base.html vs base.html)
- [x] Dynamic template inheritance (portal/review adapt to logged-in role)
- [x] User name + Sign Out in navbar for both portals
- [x] SVG favicon for both portals

### "Go Live" Meeting Mode (Session 34)
- [x] Full-viewport presentation view at `/meeting/{id}/go-live` — designed for Teams screen sharing
- [x] Current proposal prominently displayed (large text for code section, proponent)
- [x] Quick-action buttons for common recommendations
- [x] Large vote counter inputs
- [x] Auto-advance to next proposal after recording action (POST `/meeting/{id}/go-live/stage`)
- [x] Timer/clock visible in top bar
- [x] Minimal chrome — maximizes content visibility
- [x] Progress bar showing agenda completion count
- [x] Keyboard shortcuts for recommendations (1-5, U for unanimous, arrow keys for nav)
- [x] Modification panel loading with source tracking
- [x] Cross-reference chips showing related proposals
- [x] Meeting prep coverage stats and readiness badges

### Testing Mode (Session 34)
- [x] Toggle testing flag on proposals — secretariat-only route at `POST /proposals/{canonical_id}/toggle-testing`
- [x] `proposals.testing` column (binary flag) — proposals marked Testing appear in chair portals for demo without affecting real data
- [x] UI buttons on proposal detail page: "Mark as Testing" / "Remove Testing"

### Modification Approval Workflow (Session 34)
- [x] Secretariat approval of modifications before chairs see them — `POST /proposals/{canonical_id}/toggle-mod-approval/{mod_id}`
- [x] `modifications.secretariat_approved` column (binary flag)
- [x] Approve/Unapprove toggle buttons on proposal detail page (secretariat-only)
- [x] Unapproved modifications shown with 0.6 opacity in chair portal

### Chair Accounts — All Subgroups (Session 34)
- [x] 16 user accounts in `routes/auth.py` USERS dict:
  - 2 secretariat: Alex Smith, Jason Toves
  - 8 residential chairs: Brian Shanks + Rob Howard (SG2 Modeling), Rick Madrid (SG6 HVAC), plus SG1 Admin, SG3 EPLR, SG4 Envelope, SG5 Existing Buildings, Residential Consensus
  - 6 commercial chairs: Admin, Envelope & Embodied Energy, EPLR, HVACR & Water Heating, Modeling, Duane Jonlin (Consensus Committee)

### UI Polish (Session 23/24 + 34)
- [x] Shared CSS utility classes in main.css (btn-group, btn-mods, btn-xs, btn-sm, text-sm, text-muted, breadcrumb, notes-tooltip) — removed duplication from individual template `<style>` blocks
- [x] Breadcrumb navigation on review page
- [x] Phase name formatting throughout (`CODE_PROPOSAL` → `Code Proposal`)
- [x] ICC brand theme with CSS variables (`--icc-blue`, `--icc-green`, `--icc-dark`, etc.) — Session 33/34

---

## What's NOT Built Yet

### ~~Priority 1: SharePoint Integration~~ — RESOLVED (Session 36)
Azure AD app registration is permanently blocked — Alex has no admin access. The Graph API upload service (`services/sharepoint.py`) remains dormant. **Full pipeline built:** Portal approve → auto-copy to OneDrive sync folder → Power Automate flow moves to SharePoint `Portal_TEST` folder → mobile notification. No manual upload needed.

### Priority 2: Phase 2 Step 6 — Meeting Action Capture Redesign
The current action staging handles simple cases (Approve/Disapprove/Approve as Modified) but not the complex reality of real meetings:
- **"Approve as Further Modified"** — original modification rejected, new one crafted live during meeting
- **Withdrawal** — proposal withdrawn by proponent (no vote needed)
- **Combined consideration** — two or more proposals heard together, linked in the record
- **Superseded** — proposal disapproved because another proposal's modification covered it (e.g., REPC49 → REPC34)
See `docs/PORTAL_ROADMAP.md` Phase 2 Step 6 for full spec.

### Priority 3: Transcript Extraction Pipeline (Phase 3 Step 9)
Upload meeting DOCX transcripts, LLM extracts structured data (votes, reason statements, modifications, who moved/seconded). Present to Alex for review before importing. The `meeting_events` table schema exists but is empty.

### Priority 4: cdpACCESS Integration
cdpACCESS is ICC's official code development platform. Currently the modification document export is a Word doc that staff manually reference when entering data into cdpACCESS. Direct API integration was discussed but deferred until Alex talks to the CDP team.

**Short-term bridge (built):** Word document export that staff use as reference while entering into cdpACCESS manually.

### Priority 5: Proposal Text Coverage Gap
Not all proposals have extracted text. PUBLIC_INPUT phase proposals mostly lack DOCX files. Monograph PDF extraction covers 39 proposals. 2 proposals (CEPC30-25, CECP1-25) have unfixable source PDF encoding issues. Query `SELECT COUNT(*) FROM proposal_text` for current coverage.

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
