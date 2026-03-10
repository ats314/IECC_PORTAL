# Changelog

All notable changes to the IECC Portal project, organized by development session.

> For detailed session logs with exact DB changes and file lists, see [`PROJECT_MEMORY.md`](PROJECT_MEMORY.md).

---

## Session 34 — 2026-03-10

### Changed
- Merged `web/LLM_HANDOFF.md` into `web/DEVELOPMENT.md` — eliminated doc redundancy
- Comprehensive documentation overhaul (8 files updated for current state)
- Root `README.md` rewritten for GitHub presentation

### Fixed
- `meeting_docs.py`: `user.get("username")` → `user.get("name")` (empty `uploaded_by` field)

### Removed
- `web/LLM_HANDOFF.md` (content merged into `DEVELOPMENT.md`)

---

## Session 33 — 2026-03-06

### Changed
- Established "DB is the sole source of truth" as #1 hard rule across all docs
- Stripped hardcoded row counts from `AGENT_GUIDE.md`, `ARCHITECTURE.md`, `DEVELOPMENT.md`
- `iecc_startup.py` — added Phase 2B cross-check (stale meetings, orphaned staging, DQ summary)

---

## Session 32 — 2026-03-06

### Fixed
- All 6 IECC skills: corrected SG# mappings in staging-flow.md, stale claims, missing commercial mappings
- `iecc_startup.py`: DQ flag query used nonexistent column `resolved=0` → `needs_review=1`

### Changed
- Aligned documentation lists across CLAUDE.md, iecc_startup.py, and all skills
- Added Skill Routing Guide table to CLAUDE.md

---

## Session 31 — 2026-03-05

### Added
- Governance reference files saved to `reference/` directory

### Fixed
- 10 duplicate SG actions from canonical_id/proposal_uid confusion — merged and deleted
- Vote breakdowns corrected on RECP8-25, REPC23-25, REPC43-25

---

## Session 30 — 2026-03-05

### Added
- 10 SG actions from Brian Shanks SG2 meeting results (03/03)
- Extended document scan: 1,578 → 5,780 files in `documents` table
- Proposal text coverage: 133 → 178 proposals
- Modifications: 6 → 98 records

### Fixed
- Resolved 21 of 27 open DQ flags (6 remaining)
- Resolved 11 past-date SCHEDULED meetings (4 → COMPLETED, 7 → CANCELLED)

---

## Session 29 — 2026-03-05

### Added
- **Centralized content database** — 5 new tables: `proposal_text`, `modifications`, `proposal_links`, `documents`, `meeting_events`
- `populate_content.py` — content extraction pipeline (DOCX → DB with ICC markup preservation)
- `PORTAL_ROADMAP.md` — three-phase development plan from transcript analysis
- `migrations/002_centralized_content.sql`
- Portal now pre-loads proposal text, modifications, and cross-reference chips
- "Load into Editor" buttons for Quill rich text editor

---

## Sessions 27/28 — 2026-03-05

### Added
- **6 IECC-specific Cowork skills**: iecc-startup, iecc-session-close, iecc-query, iecc-web-dev, iecc-doc-gen, iecc-meeting-workflow
- `SKILLS_DEVELOPMENT.md` — master skills reference (542 lines)

---

## Session 26 — 2026-03-05

### Added
- **Quill.js rich text editor** with ICC markup conventions (underline = additions, strikethrough = deletions)
- Rich text HTML → Word formatting in document generators

### Changed
- Major `AGENT_GUIDE.md` overhaul — added document chain, lifecycle, markup conventions

---

## Session 25 — 2026-03-05

### Added
- **Circulation form pipeline**: auto-generates DOCX/PDF on "Send to Secretariat"
- `circ_forms` DB table with lifecycle tracking (`pending_review` → `approved` → `rejected`)
- `services/pdf_generator.py` — LibreOffice PDF conversion with DOCX fallback
- `services/sharepoint.py` — SharePoint Graph API upload (dormant until Azure AD configured)
- `routes/circforms.py` — secretariat review queue (Preview/Approve/Reject)
- `IECC_SHAREPOINT_STRUCTURE.md` — SharePoint folder audit

---

## Sessions 23/24 — 2026-03-05

### Added
- **Accordion action forms** — staged actions collapse to summary cards
- **HTMX inline edit** — Edit button on staged cards with pre-filled forms, OOB progress bar updates
- **Chair home improvements** — sorted meetings, agenda count badges, color-coded progress
- **Review page** — breadcrumbs, partial-completion warning, inline edit buttons
- **Dashboard** — in-progress meetings section, vote counts in recent actions
- **Proposals page** — subgroup dropdown filter, live search with 350ms debounce
- **Meeting management** — delete button, notes tooltip, form validation
- SVG favicon, shared CSS utility classes

---

## Session 22 — 2026-03-05

### Changed
- Verified DB against original JSON source files and Jason Toves' tracking spreadsheets
- Backfilled 15 proponent emails from ballot roster CSVs
- Email coverage: residential 33% → 92%, commercial 97% → 99%

---

## Sessions 20/21 — 2026-03-04

### Fixed
- CEPC2-25/CECP2-25 withdrawal swap corrected
- Resolved REPC3-25 AS vs AM discrepancy (confirmed AM 5-4)
- Added REPC65-25 SG action (AM 8-0-0)
- Reconciled against Alex's master spreadsheet

---

## Session 19 — 2026-03-03

### Changed
- **Merged two databases into one unified `iecc.db`** — 510 proposals (264 commercial + 246 residential)
- Added `track` column to all tables
- Rewrote all 6 Python tools for single DB

---

## Sessions 17/18 — 2026-03-03

### Added
- 37 residential CA reason statements mined from meeting minutes (coverage: 51% → 77.7%)

### Fixed
- Moved 29 residential meetings from commercial DB to residential DB
- Resolved 20 DQ flags (open: commercial 23 → 9, residential 25 → 19)
- REPC34-25 subgroup corrected from HVACR to Modeling SG2

---

## Sessions 14–16 — 2026-03-02/03

### Added
- `iecc_preflight.py` — session-start DB briefing tool
- `iecc_verify.py` — doc-vs-DB consistency checker

### Fixed
- Deleted 4 unsourced SG actions from Gayathri email
- Marked 4 proposals withdrawn (RECP1-25, REPC5-25, REPC9-25, REPC44-25)
- Source priority rules rewritten — emails banned as SG/CA action source

---

## Sessions 9–13 — 2026-03-02

### Added
- **Residential database** built from scratch (211 proposals, 194 SG actions)
- Unified query layer (`iecc_query.py`), change detection (`iecc_snapshot.py`)
- Combined XLSX report generator

### Fixed
- REC → RECP prefix correction (root cause of 18 phantom proposals)
- 86 residential SA dates normalized to YYYY-MM-DD
- v_current_status view fixed for phase-aware status

---

## Sessions 1–8 — 2026-02-14 to 2026-03-02

### Added
- **Initial commercial database** from 6 JSON source files (226 proposals)
- Web dashboard prototype
- `data_quality_flags` table for tracking data issues
- Governance tables (4 documents, 480 clauses)
- Cross-referenced Excel sheets, PDF mining, vote backfill
- **Commercial coverage:** 91% votes, 78% reasons
