# IECC Secretariat Master System — Project Memory

> **Owner:** Alex Smith, Director of Energy Programs, ICC
> **Role:** Secretariat to the IECC (Commercial & Residential)
> **Created:** 2026-02-14
> **Last Updated:** 2026-03-06 (Session 33)

## Project Goal

Build a master system to automate the most time-consuming parts of Alex's secretariat work for the IECC consensus committee process. Current focus: structured database for proposal tracking with RAG indexing and LLM-assisted document production.

## Alex's Core Pain Points

1. **Tracking proposal status across subgroups** — many proposals, many subgroups, hard to know current status
2. **Collecting circulation forms** — forms come from subgroup chairs, must be organized per meeting
3. **Creating agendas** — agendas must list all proposals being discussed with their current status, circulation forms, and modifications
4. **Ensuring accurate information at consensus meetings** — data must be correct and up-to-date
5. **Handling modifications** — proposals get modified during the process, tracking versions is difficult
6. **Name convention confusion** — CEPC vs CECP one-letter difference causes errors even for committee chair

## Future Capabilities (Partially Available)

- **Email integration** — Alex wants to eventually share his email for automation
- **SharePoint upload** — Built in Session 25 (`services/sharepoint.py`). Uses Graph API with client credentials. Dormant until Azure AD app is registered. Upload targets: `Shared Documents/.../Residential Subgroups/{subgroup}/{meeting}/`. Currently only circ forms; can be extended to agendas and modifications.

---

## Two Parallel Tracks

| Track | Committee | Subgroups |
|-------|-----------|-----------|
| **Commercial (CECDC)** | Commercial Consensus Committee | Admin, Envelope, EPLR, HVACR & Water Heating, Modeling |
| **Residential (RECDC)** | Residential Consensus Committee | Admin, Envelope, EPLR, Existing Building, HVAC, Modeling |

## Document Naming Conventions

| Prefix | Meaning | Example |
|--------|---------|---------|
| `CE` | Commercial Energy (public input stage, CLOSED) | `CE114-24` |
| `CECP` | Commercial Energy Code Proposal | `CECP10-25` |
| `CEPC` | Commercial Energy Public Comment | `CEPC28-25` |
| `CECC` | Commercial Energy Consensus Committee | `CECC1-26` |
| `RE` | Residential Energy (public input stage, CLOSED) | `RE114-24` |
| `RECP` | Residential Energy Code Proposal | `RECP18-25` |
| `REPC` | Residential Energy Public Comment | `REPC45-25` |
| `RECC` | Residential Energy Consensus Committee | `RECC3-26` |
| `IRCE` | IRC Energy (Chapter 11, public input, CLOSED) | `IRCE3-24` |
| `IRCEPC` | IRC Energy Public Comment | `IRCEPC1-25` |

- Suffix `-24` = 2024 cycle, `-25` = 2025 cycle, `-26` = 2026 cycle
- **CEC was renamed to CECP** during Public Comment phase. Normalize CEC→CECP.
- **REC was renamed to RECP** during Public Comment phase. Normalize REC→RECP. **⚠️ CRITICAL: The correct prefix is RECP, NOT REC. This error caused major data issues in Session 10.**
- Modifications: `RE114-24-KAHRE-MP5` (proposal-author-modification#)

### Phase Model

| Phase Key | Commercial Prefixes | Residential Prefixes | Status |
|-----------|-------------------|---------------------|--------|
| `PUBLIC_INPUT` | CE | RE, IRCE | CLOSED — no longer being heard |
| `CODE_PROPOSAL` | CECP (was CEC) | RECP (was REC) | ACTIVE |
| `PUBLIC_COMMENT` | CEPC, CECC | REPC, RECC, IRCEPC | ACTIVE |

Proposals in PUBLIC_INPUT phase that received no consensus action are "Phase Closed" — NOT pending.

---

## Current Database State

> **⚠️ LIVE COUNTS:** Run `python3 iecc_preflight.py` for current counts. See `IECC_STATUS_REPORT.md` for human-readable summary. Do NOT hardcode counts in docs.
>
> Schema details (tables, views, columns) are in **AGENT_GUIDE.md → Database Schema**.

---

## Technical Decisions

- **Database:** SQLite — `iecc.db` (unified, 510 proposals). All tables have `track` column ('commercial'/'residential'). Original separate DBs archived in `ARCHIVES/backups/pre_merge_20260303/`.
- **Build scripts:** `build_commercial_db.py`, `build_residential_db.py` (archived, not needed with unified DB — DB modified directly since Session 10)
- **Reports:** `IECC_2027_Combined_Disposition.xlsx` (single master report, 11 sheets — regenerate via `build_combined_report.py`)
- **PDF extraction:** Project PDFs are ZIP archives containing JPEG images + OCR text. Use `unzip` not pypdf.
- **Source priority:** Circulation forms / approved minutes → JSON → Excel → derived data. Emails are not a primary source UNLESS Alex explicitly directs you to use them (see Session 30 email exception in AGENT_GUIDE.md).
- **ID normalization:** `canonical_id` normalized, `proposal_uid` is SHA1 hash for joins

---

## Key People

| Name | Role | Relevance |
|------|------|-----------|
| Alex Smith | Director of Energy Programs, ICC | Project owner, Secretariat |
| Jason Toves | Staff support | Secondary contact |
| Duane Jonlin | Committee Chair | Runs consensus meetings, sometimes uses wrong prefixes |
| Bryan Holland | Committee member | Proponent of CECC1-26 |
| Steven Rosenstock | Committee member | Proponent of CECP4-25, CECP9-25 |
| Greg Johnson | Committee member | Proponent of CEPC2-25, CECP5-25 |
| Bruce Swiecicki | Committee member | Proponent of CECP7-25 |
| Jay Crandell | Committee member | Proponent of CEPC57-25 |
| Rick Madrid | HVAC SG6 Chair (Residential) | Submits circ forms via codeapps batch |
| Brian Shanks | Modeling SG2 Chair (Residential) | Circ forms pending for REPC34-25 etc. |
| Nathan Kahre | Proponent, NAHB (Residential) | REPC53/56/58/59/60, files round 3 PCs |
| Gayathri Vijayakumar | Proponent (Residential) | RECP2-25, REPC34-25_MOD. UNVERIFIED_SOURCE flag on some records. |

> **Full residential key people table:** See AGENT_GUIDE.md → Key People (Residential)

---

## Session Log

### Session 1 — 2026-02-14 (Initial Build)
**Agent:** Claude (Anthropic)
**Actions:**
- Analyzed workspace structure and document hierarchy
- Created initial project plan
- Built web dashboard prototype
- Established document naming convention reference
- Created PROJECT_MEMORY.md

### Session 2 — 2026-02-15 (Database v1)
**Agent:** Claude (Anthropic)
**Actions:**
- Built SQLite DB from 6 JSON source files
- 226 proposals, 186 consensus actions, 213 subgroup actions
- Ingested governance policies (4 documents, 480 clauses)
- Created build_commercial_db.py
- Established schema with proposal_uid primary keys

### Session 3 — 2026-02-18 (Audit & Refinement)
**Agent:** Claude (Anthropic)
**Actions:**
- Cross-referenced Excel tracking sheets against database
- Added 38 new proposals from Excel (total: 264)
- Resolved source conflicts using multi-source corroboration
- Created data_quality_flags table
- Identified CEPC vs CECP naming confusion

### Session 4 — 2026-02-25 (Feb 25 Minutes Ingest)
**Agent:** Claude (Anthropic)
**Actions:**
- Ingested 25 consensus actions from Feb 25, 2026 preliminary minutes
- Resolved 2 source conflicts via multi-source corroboration
- Identified 28 proposals missing subgroup actions
- Updated meeting registry

### Session 5 — 2026-03-01 (Full PDF Mining)
**Agent:** Claude (Anthropic)
**Actions:**
- **Subgroup Assignments PDF (2/5/2026):** 5 withdrawals (CEPC35/53/54/59/63), 3 subgroup reassignments, 19 status flags
- **CE Committee Action Report:** 15 missing consensus actions created, 30 precision upgrades (Approved→As Submitted/Modified), 3 procedural sequence fixes, ~110 vote counts backfilled
- **Errata List:** 39 errata records ingested into new table
- **Commercial Updates + Public Comments PDFs:** SEHPCAC proponent data filled, CEPC68-72 verified
- **Flagged:** CE115-24 AM (alt motion), CEPC48-25 Part II (residential), CEPC50-25 (orphan stub)
- Created IECC_Commercial_Verification_Report.xlsx
- Final: 264 proposals, 243 decided, 277 CA, 199 SA, 88% vote coverage

### Session 6 — 2026-03-01 (Verification & Documentation)
**Agent:** Claude (Anthropic)
**Actions:**
- **Cross-referenced Duane Jonlin's March 4 consensus agenda** against database
  - Found CEPC11-25 already decided (should not be on agenda)
  - Identified prefix errors (CEPC7/CEPC5 vs CECP7/CECP5)
  - Found CECP4-25 missing from Duane's list
  - New data: CEPC57-25 Modeling SG vote (7-0-4 Disapprove), CECPXx (9-0-2 Disapprove)
- **Attempted ICC website verification** — public page confirmed, SharePoint blocked by robots.txt
- **Verified 7 genuinely pending proposals** (removed 3 artifacts from count)
- **Created comprehensive agent documentation:**
  - AGENT_GUIDE.md — zero-context onboarding for any agent
  - QUERY_COOKBOOK.md — ready-to-use SQL queries
  - Updated PROJECT_MEMORY.md (this file)
  - Updated STATUS_REPORT.md

### Session 7 — 2026-03-02 (Audit & Consistency Fixes)
**Agent:** Claude (Anthropic)
**Actions:**
- **Full project audit** — reviewed all files (DB, build script, docs, spreadsheet) for consistency
- **DB fixes:**
  - Normalized 4 bare "Approved" → "Approved as Submitted" (CE3-24, CE19-24, CE101-24, +1)
  - Created missing `v_full_disposition` view (documented but absent)
  - Added 3 artifact flags to `data_quality_flags` (CE115-24 AM, CEPC48-25 Part II, CEPC50-25)
- **Documentation fixes (6 discrepancies resolved):**
  - Fixed `meetings` row count: was "11", actual is 69 (11 completed + 58 scheduled)
  - Removed references to missing governance/reference/system tables (lost in rebuild)
  - Fixed `data_quality_flags` schema in docs: `severity`→`needs_review`, `source`→actual columns
  - Fixed view list: added `v_data_quality_review`, `v_multi_action_proposals`; removed `v_full_disposition` from "missing" (now created)
  - Fixed `consensus_actions` column name: `meeting_date`→`action_date` across all queries
  - Removed reference to non-existent `Procedural-Notes.txt`
- **Regenerated verification spreadsheet** with corrected data
- **Total data quality flags:** 65→68 (3 artifact flags added)

### Session 8 — 2026-03-02 (Gap Fill & Governance Restore)
**Agent:** Claude (Anthropic)
**Actions:**
- **New data sources added by Alex:**
  - `2027_COMMERCIAL/` — 591 files from ICC SharePoint (423 docx, 157 pdf, 5 xlsx, 3 pptx)
  - `2027_RESIDENTIAL/` — 1,115 files (553 pdf, 525 docx, 27 xlsx)
  - `ICC JSON FILES/` — original Session 2 source files including `icc_governance_policies.json`
- **Governance tables restored** from `icc_governance_policies.json`:
  - 4 documents: CP#49-21, CP#7-04, CP#28-05, CP#12C-25
  - 480 clauses with hierarchy, cross-references, and full text
- **Gap fill from meeting minutes and circulation forms:**
  - 12 vote counts filled from archived meeting minutes (Session 7 partial ingest)
  - 10 mover/seconder records added
  - 8 reason statements added from minutes
  - 6 additional proposals cross-referenced against circulation forms (CE124-24, CE142-24, CE164-24, CE5-24, CE78-24, CE86-24)
- **Vote coverage: 86% → 91%** (214→226 of 249 final actions)
- **Reason coverage: 74% → 78%** (185→194 of 249 final actions)
- **Remaining 23 missing votes broken down:**
  - 8 Withdrawn (no vote expected)
  - 5 Do Not Process (no vote recorded)
  - 1 Postponed (CECP2-25)
  - 9 CE-phase proposals with committee votes not in searchable minutes (some in scanned PDFs)

### Session 9 — 2026-03-02 (Residential Database Build)
**Agent:** Claude (Anthropic)
**Actions:**
- **Built `iecc_residential.db`** from scratch — parallel to commercial database
- **Data sources:**
  - Tracking spreadsheet (88 REPC/REC/IRCEPC proposals with full proponent data)
  - 316 Circulation Form DOCX files → 194 subgroup actions, 123 new RE-phase proposals
  - 10 Meeting Minutes DOCX files → 52 consensus actions, 7 meetings
- **Database schema mirrors commercial:** proposals, subgroup_actions, consensus_actions, subgroup_movements, meetings, data_quality_flags
- **Views created:** v_current_status, v_ready_for_consensus, v_full_disposition, v_data_quality_review, v_multi_action_proposals
- **Naming convention handling:**
  - RE (public input) → REC (code proposal) rename during public comment phase
  - IRCE (IRC Energy) prefix support
  - Part I/II/III suffixes
  - Modification variants (Mod, MP#, author names like Kahre/Schmidt)
  - Leading dash cleanup
- **Final counts:** 211 proposals, 194 SG actions, 52 consensus actions, 7 meetings, 141 DQ flags
- **Coverage:** 77% SG vote coverage, 73% SG reason coverage, 42% email coverage
- **Created:** `build_residential_db.py`, `IECC_Residential_Verification_Report.xlsx`, `RESIDENTIAL_STATUS_REPORT.md`

### Session 10 — 2026-03-02 (Cross-DB Tools, REC→RECP Fix, Documentation Overhaul)
**Agent:** Claude (Anthropic)
**Actions:**
- **Built unified query layer** (`iecc_query.py`) — cross-database status, crossover reports, search, pending lists, coverage stats
- **Built change-detection tool** (`iecc_snapshot.py`) — snapshot/compare for tracking DB changes between sessions
- **Generated combined disposition XLSX** (`IECC_2027_Combined_Disposition.xlsx`) — Dashboard, Commercial, Residential, Crossovers, Data Quality sheets
- **Set up automated rebuild scheduled task** (`iecc-rebuild`)
- **Mined 4 residential consensus meeting PDFs:**
  - 01-20 Meeting: 38 consensus actions
  - 01-21 Meeting: 18 consensus actions
  - 02-04 Meeting: 24 consensus actions
  - 02-11 Meeting: 10 consensus actions
- **Normalized residential recommendation labels** — collapsed 22 variant labels into 7 canonical forms (100+ CA, 13 SA updated)
- **Filled 2 remaining commercial vote gaps** — CE49-24 Part I (28-0-1), CE71-24 (27-2-0)
- **⚠️ CRITICAL FIX: REC→RECP prefix correction:**
  - Discovered `build_residential_db.py` was creating proposals with "REC" prefix
  - PROJECT_MEMORY.md line 45 clearly documented the correct prefix as "RECP"
  - Same pattern as commercial side: CEC→CECP, REC→RECP
  - Merged 8 duplicate REC/RECP pairs (kept RECP UIDs)
  - Renamed 12 remaining REC→RECP with new proposal_uids
  - This was the root cause of 18 "phantom" proposals that didn't match real-world naming
- **Added missing proposals from Gayathri's March 12 agenda:**
  - RECP20-25, RECP21-25, RECP22-25, RECC3-26, RECC4-26, RECC5-26, REPC67-25
- **Marked REPC58-25 as withdrawn** (per minutes item 4)
- **Added phase column** to both databases: PUBLIC_INPUT (closed), CODE_PROPOSAL (active), PUBLIC_COMMENT (active)
- **Recreated v_current_status views** with phase-aware logic: proposals in PUBLIC_INPUT without consensus action are "Phase Closed" not "Pending"
- **Cross-checked 59 pending proposals against all meeting minutes** — found 22 more decided, reduced to 37, then to 31 after Gayathri reconciliation
- **Updated all project documentation** (this file, AGENT_GUIDE.md, build scripts)

### Session 10b — 2026-03-02 (Build Script Fixes, CEC Prefix Fix, SG Vote Mining)
**Agent:** Claude (Anthropic)
**Actions:**
- **Fixed `build_residential_db.py` normalize_id()** — REC→RECP conversion now in build script (6 regex locations updated)
- **Fixed `build_residential_db.py` phase assignment** — circulation form ingest used stale 'CE' value; corrected to PUBLIC_INPUT/CODE_PROPOSAL/PUBLIC_COMMENT based on prefix
- **Fixed `build_residential_db.py` v_current_status view** — added PHASE_CLOSED status for PUBLIC_INPUT proposals, ROW_NUMBER for SA dedup
- **Fixed `build_commercial_db.py` return bug** — line 109 returned `original_prefix` instead of normalized `prefix`, causing CEC to persist in DB
- **Fixed 8 CEC→CECP prefix entries** in `iecc_commercial.db`
- **Fixed NULL prefix on CEPC56-25a** in `iecc_commercial.db`
- **Mined Envelope SG meeting minutes** — extracted 4 vote updates (RE115-24, RE29-24, RE39-24, RE50-24)
- **SG vote coverage: 77% → 95%** (207/217 SA with votes)
- **Regenerated both XLSX reports** with corrected data
- **Saved new snapshot baseline:** snap_20260302_072304.json

### Session 10c — 2026-03-02 (Bulk SA Ingest, Vote Gap Mining, Outlook & SharePoint Search)
**Agent:** Claude (Anthropic)
**Actions:**
- **Bulk-inserted 9 new SA records** from circ forms on disk: REPC29-25, REPC30-25, REPC31-25, REPC32-25, REPC35-25, REPC51-25 (Modeling SG2), REPC36-25 (Envelope SG4), REPC38-25 (Admin SG1), REPC10-25 (Withdrawn)
- **Updated 3 SA with missing recommendations** — REPC21-25, REPC22-25, REPC46-25 (all Approved as Modified, HVAC SG6)
- **Marked REPC10-25 as WITHDRAWN** — Glen Clapper, based on approval of REPC6-25
- **Filled 5 vote gaps from circ forms** — RE9-24 (10-0-0), RE150-24 (8-2-3 rehearing), RE156-24 (9-0-0), REPC58-25 (6-0-1), RE150-24 recommendation corrected to Approved as Modified
- **Corrected RE151-24** — was "Approved as Submitted" but circ form shows "No Motion" (no quorum)
- **Deleted duplicate RE156-24 SA record** (id=142)
- **Searched Outlook** via Chrome MCP — found REPC33-25 and REPC34-25 circ forms from CodeApps
- **Searched SharePoint** meeting minutes — found partial vote data from Existing Buildings SG5
- **Major data cleanup:** deleted 5 UNKNOWN-subgroup SA (duplicates), 7 malformed dates fixed, 33 Admin SG1 duplicate SA records deduplicated (kept best-scored), 2 other duplicates resolved (RE120-24, RE168-24)
- **Extracted 46 missing SA recommendations from source documents** — re-read 20 HVAC circ forms, 5 Envelope/Admin/EB5 circ forms, and 5 Modeling SG2 meeting minutes PDFs. All recommendations sourced from actual document text, not inferred.
- **SA count: 227 → 194** (net: 9 inserted, 33 duplicates removed). Zero missing recommendations. Zero UNKNOWN subgroups.
- **SG vote coverage: 96%** (186/194 SA with votes). 4 true vote gaps remain + 4 No Motion/Withdrawn (no votes applicable)
- **Pending → 30** (was 31), **Withdrawn → 6** (was 5)
- **Regenerated XLSX report** — 505 proposals, 96 data quality flags

### Session 11 — 2026-03-02 (Documentation Audit & Sync, March 4 Agenda, DB Fixes)
**Agent:** Claude (Anthropic)
**Actions:**
- **Generated March 4 consensus meeting agenda** in correct ICC format (cloned March 11 template XML)
- **Deep-mined source files** for all 9 pending proposals — read Modeling SG Jan 19 notes, Envelope SG Jan 15/22 notes, Feb 9 Modeling SG agenda
- **Inserted 3 missing SA records:** CECP5-25 (Disapproved 4-2-4), CECP7-25 (Approved as Modified 5-3-2), CEPC57-25 (Disapproved 7-0-4) — all from Feb 9 Modeling SG meeting
- **Corrected CECP2-25 Envelope SG rec:** "Approved as Submitted" → "Approved as Modified"
- **Added Feb 9 Modeling SG meeting** to meetings table
- **Resolved CEPC50-25 DQ flags** (ARTIFACT_ORPHAN_STUB, PENDING_RENUMBERING)
- **Commercial SA count: 199 → 202**
- **Full system audit** — identified root cause of agent failures: documentation out of sync with DB
- **Fixed AGENT_GUIDE.md:**
  - `computed_status` → `status` (column name), status values to title-case
  - Residential counts: 225→241 proposals, 200→196 SA
  - Schema note: residential lacks `part`, `phase_locked` columns
  - Views differ between databases — documented all differences
  - Meetings count: 69→70, completed: 11→12
  - Commercial decided: ~249→243, added pending/phase closed counts
- **Fixed QUERY_COOKBOOK.md:** `computed_status` → `status`, fixed join on canonical_id
- **Rewrote STATUS_REPORT.md** — all numbers verified against live DB
- **Rewrote RESIDENTIAL_STATUS_REPORT.md** — all numbers verified against live DB
- **Fixed CLAUDE.md:** residential 225→241, added schema warnings
- **Fixed PROJECT_MEMORY.md:** SA counts, DQ counts, meetings, withdrawn count, shared schema table
- **Verification:** 58/58 documented queries pass on both databases, zero failures

### Session 12 — 2026-03-02 (Deep Verification Pass, Data Cleanup, Tool Fixes)
**Agent:** Claude (Anthropic)
**Actions:**
- **Rewrote CLAUDE.md** with mandatory agent priming ("read docs first"), quick-start state block, end-of-session protocol
- **Added session-start checklist** to AGENT_GUIDE.md with explicit "DO NOT" list
- **Added end-of-session template** to PROJECT_MEMORY.md
- **Fixed iecc_query.py:** added `--status` single-proposal lookup, fixed `--search` to match proponent names (was ID-only), fixed "REC" in docstring
- **Created missing build_combined_report.py** — was documented in all 3 project docs but never existed. Generates 5-sheet XLSX.
- **Normalized v_data_quality_review** view between databases (residential had extra `id` column and different column order)
- **Resolved 63 stale residential DQ flags** — 39 MISSING_RECOMMENDATION (all now have recs), 24 NO_ACTION_RECORDED (now have actions). Residential open flags: 89 → 17.
- **Deleted 8 orphan DQ flags** referencing nonexistent "REC" prefixed proposals (leftover from Session 10 REC→RECP fix)
- **Fixed mangled date `2025-26-02`** in 15 residential CAs → corrected to `2026-02-25` (confirmed from source filename)
- **Fixed 25 residential CAs with NULL action_date** — derived dates from source filenames: `25-22-04` → 2025-04-22 (17 CAs), `25-05-20` → 2025-05-20 (7 CAs), REPC36-25 → 2026-02-10 (1 CA)
- **Added 10 missing residential meetings** — was 7 (all 0 action_count), now 17 (16 completed + 1 scheduled March 12). Populated action_counts for all meetings.
- **Fixed STATUS_REPORT.md** — withdrawn list included CE9-24 and CE25-24 Parts I/II which aren't withdrawn in DB. Corrected to actual 11.
- **Flagged 18 commercial CAs** missing action dates from CAR_REPORT source (MISSING_ACTION_DATE DQ flags). Commercial DQ: 68 → 86, open: 5 → 23.
- **Verified 29 residential pending** — all legitimate: 12 have SG recs (ready for March 12 consensus), 17 awaiting subgroup action.
- **All 30 cookbook queries pass** on both databases (21 commercial, 9 residential)
- **Regenerated combined XLSX**, saved fresh snapshot

**State changes propagated:**
- [x] CLAUDE.md quick-start counts updated (Session 12)
- [x] AGENT_GUIDE.md updated (meetings 7→17, DQ 145→137, commercial DQ 68→86)
- [x] PROJECT_MEMORY.md updated (meetings, DQ counts, this session log)
- [x] STATUS_REPORT.md fixed (withdrawn list)
- [x] RESIDENTIAL_STATUS_REPORT.md fixed (meetings, DQ flags, remaining gaps)
- [x] QUERY_COOKBOOK.md updated (cross-DB header)
- [x] Snapshot saved

### Session 13 — 2026-03-02 (Gayathri Reconciliation, View Fix, Date Normalization)
**Agent:** Claude (Anthropic)
**Actions:**
- **Fixed v_current_status view (BOTH databases):** Postponed/Remand to Subgroup/Reconsider in active phases now = "Pending" instead of "Decided". PUBLIC_INPUT phase proposals with these CAs remain "Decided" (phase closed).
- **Fixed 2 commercial withdrawn flag mismatches:** CE9-24, CE25-24 Part I had CA rec='Withdrawn' but proposals.withdrawn=0. Fixed. Commercial withdrawn: 11 → 13, decided: 243 → 239, pending: 9 → 11.
- **Normalized 86 residential SA dates** — various formats (M-D-YY, M/D/YYYY, MM.DD.YYYY, Month D YYYY, YY-MM-DD) all converted to YYYY-MM-DD.
- **Used Gayathri's pending list (email 2026-03-02) as a LEAD to identify gaps:**
  - Added 7 new proposals as PLACEHOLDERS (no source docs): RECC3-26, RECC4-26, RECC5-26, RECP20-25, RECP21-25, RECP22-25, REPC67-25. All flagged UNVERIFIED_SOURCE.
  - Un-withdrew RECP2-25 based on email only — flagged UNVERIFIED_WITHDRAWAL_REVERSAL.
  - **⚠️ DATA CONTAMINATION (CORRECTED in Session 14):** Inserted 4 SG actions from email data (RECP8-25, REPC54-25, REPC55-25, REPC64-25) and modified vote counts on 4 others. The 4 unsourced SG actions were DELETED in Session 14. Vote count changes on REPC21-25, REPC22-25, REPC46-25 were verified against actual circ forms — those are clean.
- **Residential proposals: 241 → 248**, pending: 29 → 44, decided: 135 → 128, withdrawn: 7 → 6
- **Mined 3 missing commercial CA dates from minutes JSON:** CE121-24 (2025-05-07), CE125-24 (2025-05-21), CE72-24 (2025-06-11). NULL CA dates: 30 → 27.
- Saved snapshot: snap_20260302_184432.json

**State changes propagated:**
- [x] CLAUDE.md quick-start counts updated (Session 13)
- [x] STATUS_REPORT.md updated
- [x] RESIDENTIAL_STATUS_REPORT.md updated
- [x] Snapshot saved

### Session 14 — 2026-03-02 (Data Integrity Cleanup, Withdrawal Mining, Source Rules)
**Agent:** Claude (Anthropic)
**Actions:**
- **Deleted 4 unsourced SG actions** sourced from Gayathri email (RECP8-25, REPC54-25, REPC55-25, REPC64-25). These had no circ form, no date, no reason.
- **Flagged 7 Gayathri-sourced proposals** as UNVERIFIED_SOURCE in data_quality_flags.
- **Flagged RECP2-25** un-withdrawal as UNVERIFIED_WITHDRAWAL_REVERSAL.
- **Mined Admin SG1 minutes (2026-01-14):** Found RECP1-25 withdrawal by proponent, REPC3-25 reassignment to Modeling, REC2-25 move to Envelope.
- **Marked 4 proposals withdrawn:** RECP1-25 (from SG1 minutes), REPC5-25, REPC9-25, REPC44-25 (per Alex). Residential withdrawn: 6 → 10, pending: 44 → 40.
- **Fixed 3 subgroup assignments:** REPC49-25 HVACR→Modeling, REPC42-25 HVACR→Modeling, REPC3-25 Modeling→EPLR (then confirmed should be Modeling per SG1 minutes).
- **Populated RECP12-25:** Added proponent (Vijayakumar), subgroup (Modeling SG2), SG action (AS 7-3-2 on 2026-01-27 from circ form), code section (R408).
- **Verified Modeling SG2 agenda** for March 3 meeting — 11 items all legitimate, REPC3-25 identified as missing.
- **Verified EPLR SG3 status** — parsed 3 EPLR meeting agendas (1/12, 1/26, 2/23). Found REPC54-25 never on any EPLR agenda. EPLR has 1/26 and 2/23 meetings with no circ forms or minutes on disk.
- **Updated AGENT_GUIDE.md:** Rewrote Source Priority section — emails explicitly banned as source for SG/CA actions. Added "WHAT IS NOT A SOURCE" section.
- **Root cause identified:** Build pipeline does not parse subgroup meeting minutes. Withdrawals, reassignments, and some votes only appear in SG minutes, not circ forms. This is the primary source of data gaps.

**State changes propagated:**
- [x] AGENT_GUIDE.md Source Priority rewritten
- [x] PROJECT_MEMORY.md Session 13 log corrected, Session 14 added
- [ ] CLAUDE.md quick-start counts — updating next
- [ ] Snapshot — saving after all changes complete

### Session 15 — 2026-03-02 (Email Gap-Fill Pass, Subgroup Circ Form Mining)
**Agent:** Claude (Anthropic)
**Actions:**
- **Searched Outlook email across all 6 residential subgroups** for missing circ forms, meeting minutes, and status updates.
- **Inserted IRCEPC1-25 SG action:** AS 9-0-0, 2026-01-26, EPLR SG3. Source: Hensley circ form attached to 3/2/2026 email.
- **Inserted REPC61-25 SG action:** AM, 2026-01-27, EB SG5. Source: Mark Rodriguez circ form attached to 2/25/2026 email. Vote fields blank on circ form (NULLs in DB).
- **EPLR SG3 status confirmed DONE** — Hensley emailed 3/2/2026 cancelling March meeting, stating all proposals heard. Outstanding circ forms: REPC25-25, REPC55-25, REPC56-25 (1/26 meeting), REPC65-25, REPC3-25 (2/23 meeting). Hensley needs to submit via CodeApps.
- **Modeling SG2 fully mapped** — Jan 13 (4 proposals) and Jan 27 (7 proposals) already in DB. Feb 17 meeting CANCELLED. All 9+ pending Modeling proposals on March 3 agenda (tomorrow). No gaps — just waiting for the meeting.
- **REPC42-25 and REPC49-25 reassignment confirmed** — Jason Toves and Rick Madrid emails confirm deferral from HVAC SG6 to Modeling SG2. DB already correct.
- **HVAC SG6:** Rick Madrid (2/24 email) confirmed 4 outstanding circ forms to complete.
- **Envelope SG4:** No circ form emails found for pending proposals RECP5-25, REPC15-25.
- **Admin SG1:** No circ form emails found for RECC3-26, RECC4-26, RECC5-26.
- **Verified 4 HVAC SG6 circ forms** (REPC23-25, REPC24-25, REPC43-25, REPC52-25) found in workspace — all already in DB. HVAC SG6 fully accounted for.
- **Confirmed RECC3-26, RECC4-26, RECC5-26** via Jason Toves Teams chat — still need to be added to cdpACCESS but "we are up to date on tracking."
- **Discovered Teams has meeting recordings + transcripts** for EPLR SG3 (1/26 and 2/24 meetings). Located in "IECC RE Electrical Power, Lighting, Renewables..." group chat. Not yet mined.
- **Toves chat lead:** REPC3-25 "approved as modified 5-4" at 2/24 EPLR meeting (chat only, not circ form).
- **Note:** The "2/23 EPLR meeting" actually happened on 2/24 per Teams.
- **Updated CLAUDE.md** quick-start counts, known data gaps, and lessons learned.
- **Residential counts:** 129 decided (+1), 39 pending (-1), 10 withdrawn (unchanged). 2 new SA records.
- **Commercial counts:** 241 decided, 8 pending, 14 withdrawn (unchanged from Session 14).

**Unfinished — carried to Session 16:**
- ~~Mine EPLR Teams transcripts~~ — Teams Copilot cannot access transcripts; Teams web UI not reliably automatable. Alex to pull manually if needed.
- Check other subgroup group chats for meeting recordings/transcripts.
- Decide with Alex whether Teams transcripts qualify as a source for SG actions.

**State changes propagated:**
- [x] CLAUDE.md quick-start counts updated
- [x] CLAUDE.md lessons learned updated
- [x] PROJECT_MEMORY.md Session 15 updated
- [x] AGENT_GUIDE.md — all row counts and status numbers synced to DB
- [x] Snapshot saved

### Session 16 — 2026-03-03 (EPLR Data Mining, Tooling Completion, Doc Corrections)
**Agent:** Claude (Anthropic)
**Actions:**
- **Completed iecc_verify.py** — tested, fixed false positive detection (historical references), clean pass.
- **Built iecc_preflight.py** — session start briefing: DB state, pending by subgroup, meetings, DQ flags, snapshots, doc verification.
- **Restructured docs** — eliminated duplicate count tables from AGENT_GUIDE.md and PROJECT_MEMORY.md. CLAUDE.md is now the single source of truth for all counts.
- **Folder cleanup** — archived one-off scripts, summaries, backups to ARCHIVES/.
- **End-to-end tool test** — all 5 tools pass (preflight, verify, query status, query pending, snapshot).
- **CORRECTED EPLR SG3 proposal list:**
  - REPC25-25 was reassigned to Admin SG1 (per Hensley 1/26 email) — NOT an EPLR proposal
  - REPC56-25 was reassigned to Existing Buildings SG5 (per Hensley 1/26 email) — NOT an EPLR proposal
  - Actual EPLR proposals: IRCEPC1-25 (in DB), REPC54-25, REPC55-25, REPC64-25, REPC65-25, REPC3-25
- **Found March 12 consensus agenda** with SG votes: REPC54-25 (AS 9-0-0), REPC55-25 (AS 9-0-0), REPC64-25 (D 6-2-3). Circ forms exist in CodeApps but not on disk.
- **REPC65-25 and REPC3-25** NOT on March 12 agenda — still truly pending.
- **REPC3-25 AS vs AM discrepancy:** DB has "Approved as Submitted 5-4" but Toves chat said "approved as modified 5-4". Needs resolution.
- **Teams Copilot failed** (3 attempts) — cannot access internal meeting transcripts. Teams web UI not reliably automatable.
- **No DB changes this session** — no new records inserted or modified. Counts unchanged.
- **Updated CLAUDE.md** — corrected EPLR data gaps section, added Session 16 lessons learned, updated session number.

**Unfinished — for next session:**
- REPC54-25, REPC55-25, REPC64-25 have known SG votes from March 12 agenda but NO circ forms on disk. Decide with Alex: insert SA records sourced from consensus agenda? Or wait for circ forms from CodeApps?
- REPC65-25 — no circ form, no SG action, not on March 12 agenda. Truly pending.
- REPC3-25 — has SA in DB (AS 5-4) but may be AM not AS per Toves chat. Needs circ form to resolve.
- Mine Teams transcripts manually (agent cannot do this).

**State changes propagated:**
- [x] CLAUDE.md quick-start state updated (Session 16)
- [x] CLAUDE.md known data gaps corrected (EPLR section rewritten)
- [x] CLAUDE.md lessons learned updated (Session 16 Teams lesson)
- [x] PROJECT_MEMORY.md Session 16 entry added
- [ ] Snapshot — saving now

### Session 17 — 2026-03-03 (Data Gap Fill, DQ Cleanup, Circ Form Ingest)
**Agent:** Claude (Anthropic)
**Actions:**
- **Filled 10 commercial CA dates** from June 18, 2025 consensus agenda: CE63-24, CE65-24, CE67-24, CE78-24, CE108-24, CE123-24, CE124-24, CE128-24, CE165-24, CE166-24. Verified agenda PDF on disk.
- **Resolved 3 stale MISSING_ACTION_DATE DQ flags** — CE121-24, CE125-24, CE72-24 already had dates from Session 13.
- **Mined 37 residential CA reason statements** from consensus meeting minutes (PDFs and DOCX). Coverage: 51% → 77.7% (108/139). Remaining 31: 18 from March 25 meeting (minutes have no reason column), 13 from other meetings (not in minutes text).
- **Moved 29 residential meetings** from commercial DB to residential DB. Commercial meetings: 70 → 41. Residential meetings: 17 → 46.
- **Resolved 20 DQ flags total:** 13 commercial MISSING_ACTION_DATE, 1 NEXT_MEETING_ITEMS (stale), 6 residential NO_ACTION_RECORDED (5 now have SG actions, 1 withdrawn). Open DQ: commercial 23 → 9, residential 25 → 19.
- **Ingested 3 EPLR circ forms** (uploaded by Alex): REPC54-25 (AS 9-0-0), REPC55-25 (AS 9-0-0), REPC64-25 (D 6-0-3). All from 1/26/2026 EPLR SG3 meeting. Updated existing placeholder SA records with full vote, reason, and source data.
- **Remaining EPLR gaps:** REPC65-25 (no circ form), REPC3-25 (has SA but AS vs AM discrepancy unresolved).

**Could not fill from disk:**
- 5 commercial CA dates (CE5, CE10, CE86, CE87, CE164) — in CAR but not in any minutes on disk. No June 18+ minutes exist.
- CE25-24 Part I, CE9-24 — withdrawn, not on any agenda.
- 31 residential CA reasons — 18 from March 25 meeting (no reason column), 13 not in minutes text.

**State changes propagated:**
- [x] CLAUDE.md quick-start counts updated
- [x] CLAUDE.md known data gaps updated
- [x] PROJECT_MEMORY.md Session 17 entry added
- [x] Snapshot saved

### Session 18 — 2026-03-03 (Verification Unification, Deep Audit, REPC34-25 Fix)
**Agent:** Claude (Anthropic)
**Actions:**
- **Unified verification reports** — Merged separate commercial and residential XLSX files into single `IECC_2027_Verification_Report.xlsx` with 10 sheets (Dashboard, Commercial Proposals/CA/SA, Residential Proposals/CA/SA, DQ Flags, Errata, Meetings). All counts verified against both DBs. Created `build_verification_report.py` to regenerate.
- **Deep integrity audit** — Ran 16 checks per database. Found 4 explainable issues (is_final ordering, "Remand to Subgroup" recommendation, CEPC crossovers in residential DB). No actual data corruption.
- **Gap audit** — Classified all 47 pending proposals into categories. Identified 2 genuine data gaps: REPC34-25 and REPC65-25.
- **REPC34-25 mistake and fix:** Wasted ~30 min searching Outlook for a "circ form" that turned out to be a modification document (`REPC34-25_MOD.docx`). REPC34-25 is on the Modeling SG2 March 3 agenda — it hasn't been voted on yet. Root cause: (1) stale subgroup assignment (HVACR SG6 instead of Modeling SG2), (2) Session 10c notes incorrectly described Outlook attachment as a "circ form," (3) agent didn't check upcoming agendas before searching for missing source data.
- **DB fix:** Updated REPC34-25 `current_subgroup` from HVACR (SG6) to Modeling (SG2). Resolved NO_ACTION_RECORDED DQ flag.
- **Documentation overhaul:** Added new Hard Rule #12 (agenda-first check) and Lesson Learned (Session 18) to CLAUDE.md. Added rules #17-19 to AGENT_GUIDE.md Known Issues. Corrected all REPC34-25 references in PROJECT_MEMORY.md. Fixed stale verification report references in CLAUDE.md.

**Key lesson:** When a proposal has NO SG action, FIRST check if it's on an upcoming meeting agenda. A missing circ form almost always means the SG hasn't voted yet.

**State changes propagated:**
- [x] CLAUDE.md lessons learned + new hard rule #12 added
- [x] CLAUDE.md verification report reference updated
- [x] AGENT_GUIDE.md rules #17-19 added (agenda-first, _MOD.docx, stale subgroups)
- [x] PROJECT_MEMORY.md REPC34-25 known issues corrected
- [x] PROJECT_MEMORY.md Session 18 entry added
- [x] Residential DB: REPC34-25 subgroup corrected, DQ flag resolved

### Session 19 — 2026-03-03 (Database Merge: Two DBs → One Unified iecc.db)
**Agent:** Claude (Anthropic)
**Actions:**
- **Merged two databases into one.** Combined `iecc_commercial.db` (264 proposals) and `iecc_residential.db` (248 proposals) into unified `iecc.db` (510 proposals). Added `track TEXT NOT NULL` column ('commercial'/'residential') to ALL tables: proposals, consensus_actions, subgroup_actions, meetings, data_quality_flags, errata, governance_documents, governance_clauses, subgroup_movements.
- **Unified schema.** Added `part` and `phase_locked` columns to residential proposals (were commercial-only). Created 5 unified views with `track` as first column and consistent column naming across both tracks.
- **Handled 2 crossover proposals.** CEPC48-25 Part II kept as residential (has SA+CA there), CEPC50-25 Part II kept as commercial (has SA+CA there). Each exists once in merged DB under its primary track.
- **Rewrote all 6 Python tools** for single DB: iecc_preflight.py, iecc_verify.py, iecc_query.py, iecc_snapshot.py, build_combined_report.py, build_verification_report.py. All tested and verified.
- **Updated all documentation:** CLAUDE.md, AGENT_GUIDE.md, PROJECT_MEMORY.md, IECC_STATUS_REPORT.md, QUERY_COOKBOOK.md, README.md — all now reference single unified iecc.db.
- **Backups** of original separate DBs saved to `ARCHIVES/backups/pre_merge_20260303/`.

**Verification:** All status counts match originals exactly. Commercial: 241 Decided, 7 Pending, 14 Withdrawn, 1 Phase Closed. Residential: 129 Decided, 38 Pending, 10 Withdrawn, 70 Phase Closed. Pending counts differ by 1 each from originals due to crossover proposals (expected — each crossover exists once under its primary track).

**State changes propagated:**
- [x] CLAUDE.md — session count, DB references, hard rules #10-11 updated
- [x] AGENT_GUIDE.md — session count, DB section, schema section, views section, files section
- [x] PROJECT_MEMORY.md — session 19 entry
- [x] IECC_STATUS_REPORT.md — session count
- [x] QUERY_COOKBOOK.md — header updated for unified DB
- [x] README.md — already up to date from Session 18
- [x] All 6 Python tools rewritten and tested
- [x] Snapshot saved

### Session 20 — 2026-03-04 (Jason Toves Comparison & Circ Form Resolution)
**Agent:** Claude (Anthropic)
**Actions:**
- **Compared Jason Toves' tracking spreadsheets against DB.** Jason (deputy director) maintains independent commercial and residential tracking spreadsheets. Compared both against iecc.db to find conflicts. Most "conflicts" were just Jason's tracker not yet updated after committee votes. Identified 3 real residential status conflicts (RECP3-25, RECP7-25, RECP17-25 — variant proposals decided but base proposals not updated) and 1 commercial withdrawal discrepancy (CEPC2-25).
- **Resolved variant proposals.** RECP3-25a, RECP7-25a, RECP17-25b are modifications of their base proposals. Added CA records to base proposals from variant data. Residential decided: 129→132, pending: 36→33, CA final: 139→142.
- **Fixed CEPC2-25/CECP2-25 withdrawal swap.** DB had withdrawal on wrong proposal (CECP2-25 Holland instead of CEPC2-25 Johnson). Corrected: CEPC2-25 now withdrawn, CECP2-25 now active.
- **Updated 5 proponent fields** from Jason's data: RECC1-26, RECC2-26, RECP20-25, RECP21-25, RECP22-25.
- **Updated 2 withdrawals** found since last session: RECP5-25 (Schwarz) and REPC15-25 (Farbman). Commercial 264→263, Residential 248→247.
- **Resolved REPC3-25 AS vs AM discrepancy.** Alex provided circ form. Confirmed: Approved as Modified 5-4 on 2/24/26 (two modifications heard — Mod 1 on 1/26, Mod 2 on 2/24). DB corrected from AS to AM.
- **Added REPC65-25 SG action.** Alex provided circ form. Approved as Modified 8-0-0 on 2/24/26 (Mod 1 on 1/26 AM 7-0-2, Mod 2 on 2/24 AS 8-0-0). Previously had no SG record.
- **Filed circ forms** to EPLR 26-02-24 Meeting folder on disk.
- **Updated all documentation:** IECC_STATUS_REPORT.md, PROJECT_MEMORY.md.

**State changes propagated:**
- [x] IECC_STATUS_REPORT.md — counts, EPLR section, REPC3-25 resolved, CEPC2-25 confirmed, data gaps cleaned
- [x] PROJECT_MEMORY.md — session 20 entry, known issues updated
- [x] Snapshot saved
- [x] Verify clean

### Session 21 — 2026-03-04 (Master Spreadsheet Reconciliation & DB Fixes)
**Agent:** Claude (Anthropic)
**Actions:**
- **Reconciled Alex's master spreadsheet (IECC_Disposition_Restored.xlsx) against DB.** Alex provided his pre-corruption backup. Found 4 discrepancies: 3 residential status conflicts (RECP3-25, RECP7-25, RECP17-25) and 1 commercial SG rec display issue (CECP3-25 — dual SG actions, not a real conflict).
- **Deleted 3 incorrectly copied CA records.** Session 20 had copied consensus actions from variant proposals (RECP3-25a, RECP7-25a, RECP17-25b) to their base proposals. Alex's master spreadsheet confirmed the base proposals should remain Pending. Deleted the copied CAs. Residential decided: 132→129, pending: 33→36, CA final: 142→139.
- **Regenerated IECC_Disposition_Restored.xlsx** from fixed DB matching Alex's original format (Dashboard + Commercial + Residential sheets).
- **Compared Jason Toves' updated tracking spreadsheets against DB.** Found 43 commercial flags and 14 residential flags. Nearly all were Jason being behind (not updating after committee votes). Only 4 items where Jason was ahead of DB.
- **Applied 4 fixes from Jason's data:**
  - CECC1-26: subgroup corrected from "Commercial Consensus Committee" to "Commercial Administration Subgroup"
  - RECP20-25: added cdpACCESS ID 2937, code section "Full Fuel Cycle Energy"
  - RECP21-25: added cdpACCESS ID 2938, code section "Specifications for Standard Reference Design and Proposed Design Table"
  - RECP22-25: added cdpACCESS ID 2939, code section "Table R408.2 Credits For Additional Energy Efficiency"
- **Fixed SQLite journal file issue** — stale journal from failed write blocked DB reads on mounted drive. Resolved by copying DB to local workspace, fixing, and copying back.

**State changes propagated:**
- [x] PROJECT_MEMORY.md — Session 21 entry added
- [x] Verify clean
- [x] Snapshot saved

### Session 22 — 2026-03-05 (Source Verification, Roster Backfill, Cleanup)
**Agent:** Claude (Anthropic)
**Actions:**
- **Verified DB against original JSON source files.** Compared 5 JSON files (Admin SG, Envelope SG, EPLR SG, Modeling SG, consensus minutes) and old commercial DB against current iecc.db. Results: 1 vote mismatch on CECP1-25 (known), 1 rec mismatch on CECP2-25 (DB correct per Session 11), Part suffix normalization false positives in EPLR/Modeling. CE-phase vote/reason gaps exist but Alex deprioritized CE data. DB is clean against source files.
- **Verified DB against Jason Toves' tracking spreadsheets.** All 82 commercial tracking proposals and 93 residential tracking proposals exist in DB. 5 cdpACCESS IDs in Jason's numbered list are raw submissions that never became proposals. DB has everything Jason has.
- **Scanned ICC backend "Residential" folder** (newly added by Alex). Found ballot vote CSVs (Ballot 1, 2, 3), Committee Action Report PDF, RECC1-26 PDF. Identified: 5 missing residential DNP proposals (RE10-24, RE11-24, RE12-24, RE171-24, RE190-24 — all PUBLIC_INPUT phase, not actionable), RE57-24 missing consensus action (Disapproved via Ballot 3), RECC1-26 wrong proponent. No DB changes made per Alex's instruction.
- **Backfilled 15 proponent emails** from ballot roster CSVs and existing DB records. Sources: Ballot 1/2/3 vote CSVs (96 roster entries), Jason's commercial tracking sheet, and cross-referencing existing proponent_email values in DB. Updated: Schmidt (4 proposals), Vijayakumar (2), Tate (3), Rose (1), Schwarz (1), Rabe (1), Kahre (1), Deary (1), Swiecicki (1).
- **Email coverage improved:** Residential active proposals 33% → 92%, Commercial 97% → 99%.
- **Deleted stale iecc.db-journal file** — was blocking direct reads on mounted drive since March 4. DB now reads directly without copy-local workaround.
- **Cleaned up workspace** — moved 8 obsolete files (backup DB, superseded agenda versions, Word temp files, Python cache) to "remove this" folder. Alex also removed 2027_COMMERCIAL, 2027_RESIDENTIAL, ARCHIVES, and Residential folders.

**9 proposals still missing email** — 6 have no proponent name (CEPC56-25a, RECP3-25a, RECP7-25a, RECP17-25b, RECC3-26, RECC4-26, RECC5-26), 2 people not in any source (Truitt/Gonzalez-Laders for RECC1-26/RECC2-26).

**State changes propagated:**
- [x] PROJECT_MEMORY.md — Session 22 entry added
- [x] IECC_STATUS_REPORT.md — email coverage, session date updated
- [x] CLAUDE.md — session count updated
- [x] Snapshot saved
- [x] Verify run

### Session 23/24 — 2026-03-05 (Web App Polish: Accordion, HTMX Inline Edit, Dashboard & Portal Improvements)
**Agent:** Claude (Anthropic)
**Actions:**
- **Implemented accordion action forms on portal.** After staging an action, the form collapses to a summary card showing recommendation, votes, and reason. Cards are expandable. Reduces visual clutter during meetings with many proposals.
- **Built HTMX inline edit/unstage flow.** Edit button on staged action cards uses `hx-post` to return a pre-filled form (`action_unstaged.html` partial) with previous values (recommendation, votes, reason, modification text). Re-staging swaps back to the collapsed card. No page reload at any point. OOB swaps keep progress bar and finalize bar in sync.
- **Improved chair home page.** Upcoming meetings sorted ascending (nearest first). Added Agenda column (badge count or "No agenda"). Added Progress column with color-coded staging progress (green=complete, yellow=partial, gray=none). Completed meetings sorted descending with consistent btn-group styling. Phase names formatted (`CODE_PROPOSAL` → `Code Proposal`).
- **Improved review page.** Added breadcrumb navigation. Added partial-completion warning alert when staged count < total agenda. Added inline Edit buttons per row. Removed redundant inline styles in favor of CSS classes.
- **Improved secretariat dashboard.** Added "In-Progress Meetings" section (meetings with staged actions, showing body/track/date/progress/portal-link, yellow left border). Added vote counts (F-A-NV) column to Recent Subgroup Actions table. Added `IN_PROGRESS_MEETINGS` query to `db/queries.py`.
- **Improved meetings page.** Added delete button (×) for scheduled meetings with confirmation dialog. Added form validation JS with error display. Added notes tooltip (📝 emoji with `title` attribute). Phase name formatting. Consistent btn-group styling for completed meeting export buttons.
- **Improved proposals page.** Added subgroup dropdown filter populated from DB. Added live search with 350ms debounce on keyup (auto-submits filter form).
- **CSS consolidation.** Moved shared utility classes (`.btn-group`, `.btn-mods`, `.btn-xs`, `.btn-sm`, `.text-sm`, `.text-muted`, `.breadcrumb`, `.notes-tooltip`) from individual template `<style>` blocks to `main.css`.
- **Added SVG favicon** to both `base.html` and `chair_base.html` (ICC blue background, "IC" text).
- **Added meeting delete route** in `routes/meetings.py` — prevents deleting completed meetings, cleans up agenda items and staged actions.
- **No database changes.** All changes were web app UI/UX improvements. Zero changes to `iecc.db`.

**Files created:**
- `templates/partials/action_unstaged.html` — HTMX partial for inline unstage with pre-filled values
- `static/favicon.svg` — SVG favicon

**Files modified:**
- `routes/subgroup_portal.py` — HTMX-aware unstage route, review passes total_agenda
- `routes/auth.py` — chair home fetches agenda_count and staged_count per meeting
- `routes/dashboard.py` — fetches in-progress meetings
- `routes/meetings.py` — added delete meeting route
- `routes/proposals.py` — passes subgroups list for dropdown
- `db/queries.py` — added IN_PROGRESS_MEETINGS query
- `templates/partials/action_saved.html` — HTMX Edit button, CSS class styling
- `templates/chair_home.html` — sorted meetings, agenda/progress columns
- `templates/meeting_review.html` — breadcrumbs, partial-completion warning, edit buttons
- `templates/dashboard.html` — in-progress meetings section, vote counts column
- `templates/meetings.html` — delete button, validation, notes tooltip, phase formatting
- `templates/proposal_list.html` — subgroup dropdown, live search with debounce
- `templates/base.html` — favicon link
- `templates/chair_base.html` — favicon link
- `static/css/main.css` — shared utility classes

**State changes propagated:**
- [x] LLM_HANDOFF.md — updated testing checklist, key files table, partials table, next features
- [x] DEVELOPMENT.md — updated "What's DONE" with all new features, added UI Polish section
- [x] PROJECT_MEMORY.md — Session 23/24 entry added

### Session 25 — 2026-03-05 (Circulation Form Pipeline: Generate → Review → SharePoint Upload)
**Agent:** Claude (Anthropic)
**Actions:**
- **Built complete circ form pipeline.** When a chair clicks "Send to Secretariat," the system now auto-generates a circulation form document (PDF via LibreOffice or DOCX fallback) and queues it for secretariat review.
- **Created `circ_forms` DB table** tracking document lifecycle: `pending_review` → `approved`/`uploaded` → `rejected`. Unique per meeting.
- **Created `services/pdf_generator.py`** — generates circ form via `generate_circform_docx()`, converts to PDF with LibreOffice headless, falls back to DOCX if LibreOffice unavailable. Cross-platform: checks `libreoffice`, `soffice`, and Windows Program Files paths.
- **Created `services/sharepoint.py`** — SharePoint Graph API upload using `msal` OAuth2 client credentials. Dormant until Azure AD env vars configured (`SP_TENANT_ID`, `SP_CLIENT_ID`, `SP_CLIENT_SECRET`). Uploads to correct subgroup meeting folder using three-layer name mapping.
- **Created `routes/circforms.py`** — secretariat-only routes for circ form review: list (`/circ-forms`), preview, download, approve (with optional SP upload), reject (with reason).
- **Added SUBGROUP_TO_SP_FOLDER mapping to `config.py`** — maps DB subgroup names to SharePoint folder names (6 residential subgroups).
- **Added SharePoint config to `config.py`** — `SP_TENANT_ID`, `SP_CLIENT_ID`, `SP_CLIENT_SECRET`, `SP_SITE_HOST`, `SP_SITE_PATH`, `SP_DOC_LIBRARY_PATH`, `SP_ENABLED`.
- **Added `GENERATED_DIR`/`CIRCFORMS_DIR` to `config.py`** — writable directory with fallback to system temp if `web/generated/` is read-only.
- **Modified `routes/subgroup_portal.py`** — `send_to_secretariat()` now calls `generate_circform_document()` and inserts `circ_forms` row after committing actions. Errors don't block the send.
- **Modified `routes/dashboard.py`** — fetches pending circ forms count and list for dashboard.
- **Modified `templates/dashboard.html`** — added "Pending Circ Forms" section with Preview/Approve/Reject buttons.
- **Created `templates/circ_forms.html`** — full page with "Pending Review" and "Reviewed" tables.
- **Created `templates/partials/circform_row.html`** — HTMX partial for post-approve/reject row swap.
- **Updated `templates/base.html`** — added "Circ Forms" nav link for secretariat.
- **Updated `main.py`** — registered circforms router, added `/circ-forms` to secretariat middleware guard.
- **Created `IECC_SHAREPOINT_STRUCTURE.md`** — deep audit of SharePoint folder tree, cross-referenced with DB meetings, documented inconsistencies and naming conventions.
- **Added 7 circ_forms queries to `db/queries.py`** — INSERT, PENDING, ALL, BY_ID, BY_MEETING, APPROVE, UPLOAD, REJECT.
- **No proposal/action data changes.** All changes were infrastructure and web features.

**Files created:**
- `services/pdf_generator.py` — DOCX→PDF generation with fallback
- `services/sharepoint.py` — SharePoint Graph API upload (dormant)
- `routes/circforms.py` — secretariat circ form review routes
- `templates/circ_forms.html` — full circ forms page
- `templates/partials/circform_row.html` — HTMX row partial
- `IECC_SHAREPOINT_STRUCTURE.md` — SharePoint folder audit

**Files modified:**
- `config.py` — SP config, SUBGROUP_TO_SP_FOLDER, GENERATED_DIR
- `db/queries.py` — 7 circ_forms queries
- `routes/subgroup_portal.py` — wired PDF gen into send flow
- `routes/dashboard.py` — pending circ forms section
- `main.py` — registered circforms router, middleware
- `templates/base.html` — Circ Forms nav link
- `templates/dashboard.html` — pending circ forms section

**DB changes:**
- Created `circ_forms` table (lifecycle tracking for generated circ form documents)

**Known issue:** Alex's Windows machine likely lacks LibreOffice, so circ forms will generate as DOCX not PDF. Fully functional either way.

**State changes propagated:**
- [x] LLM_HANDOFF.md — circ form pipeline section, key files table, testing checklist updated
- [x] DEVELOPMENT.md — Session 25 features, new priority items, known issues updated
- [x] PROJECT_MEMORY.md — Session 25 entry added

### Session 26 — 2026-03-05 (Documentation Overhaul + Circ Form Pipeline Verification)
**Agent:** Claude (Anthropic)
**Actions:**
- **Verified circ form pipeline end-to-end on live server.** Full test with meeting 83: chair login → portal → auto-populate agenda → stage action → send to secretariat → circ form PDF generated (35KB) → secretariat dashboard shows pending → preview works → approve works. Pipeline confirmed fully functional.
- **Cleaned up test data** — reset meeting 83 back to SCHEDULED status after testing.
- **Removed duplicate CSS** from `templates/circ_forms.html` (inline styles already in `main.css`).
- **Major documentation overhaul in AGENT_GUIDE.md** — replaced sparse 15-line pipeline overview with comprehensive ~120-line section covering:
  - The IECC Code Development Lifecycle (3 phases: Public Input, Public Comment, Final Action)
  - The Document Chain (PCD → Proposal → Modification) with REPC3-25 example
  - Where to Find Documents (table with disk paths for every document type)
  - Code Language Markup Conventions (underline = additions, strikethrough = deletions)
  - Web App Tables section (sg_action_staging, meeting_agenda_items, circ_forms)
- **Added Rule #6 to LLM_HANDOFF.md** — "UNDERSTAND THE DOCUMENT CHAIN BEFORE TOUCHING PROPOSALS" directing agents to AGENT_GUIDE.md
- **Updated all 7 documentation files** — CLAUDE.md, AGENT_GUIDE.md, README.md, LLM_HANDOFF.md, DEVELOPMENT.md, PROJECT_MEMORY.md (Session 25 entry), circ_forms.html
- **Saved DB snapshot** (`snap_20260305_182317.json`)
- **Built rich text editor for modification_text.** Replaced plain textarea with Quill.js rich text editor (CDN 1.3.7). Toolbar includes bold, underline, strikethrough, lists, and clean — matching ICC markup conventions (underline = additions, strikethrough = deletions). Editor initializes lazily when "Modified" recommendation is selected. Dark theme CSS overrides match the portal's dark UI.
- **Updated HTMX integration.** Hidden input captures Quill HTML on `htmx:configRequest` event. Edit (unstage) partial auto-initializes Quill with previous HTML content pre-filled.
- **Updated all display templates** — review page, completed meeting view, and proposal detail page all render modification_text as HTML via `|safe` filter with `.mod-rich` CSS class.
- **Updated doc generators for HTML.** Both circ form and modifications DOCX generators now parse HTML modification text into proper Word formatting (underline, strikethrough, bold, italic TextRuns). Falls back gracefully to plain text for legacy data that doesn't contain HTML tags.
- **Tested end-to-end:** Portal loads with Quill CDN → select "Approved as Modified" → editor appears → submit HTML → staged correctly → review page renders formatted text → Edit pre-fills editor → DOCX exports generate correctly (9.4KB circ form, 11.9KB modifications doc).

**Files modified:**
- `AGENT_GUIDE.md` — major overhaul: document chain, lifecycle, markup conventions, web tables
- `web/LLM_HANDOFF.md` — Rule #6 added, circ form pipeline docs
- `web/DEVELOPMENT.md` — Session 25 features, priorities updated
- `web/README.md` — new files and env vars documented
- `CLAUDE.md` — project tree updated
- `web/templates/circ_forms.html` — duplicate CSS removed
- `web/templates/base.html` — added `{% block extra_head %}` for per-page CDN includes
- `web/templates/chair_base.html` — added `{% block extra_head %}`
- `web/templates/meeting_portal.html` — Quill CDN, replaced textarea with Quill editor, dark theme CSS, initQuillInForm() function, `|safe` filter for completed view
- `web/templates/partials/action_unstaged.html` — Quill editor with pre-fill, auto-init script
- `web/templates/meeting_review.html` — `|safe` filter + `.mod-rich` class for modification text
- `web/templates/proposal_detail.html` — `|safe` filter + `.mod-rich` class for both SG and CA actions
- `web/static/css/main.css` — added `.mod-rich` styles (green underline, red strikethrough)
- `web/services/doc_generator.py` — added `parseModHtml()` / `modParagraphs()` / `richModCell()` JS helpers, `_strip_html()` Python helper. Both circ form and modifications generators now produce rich Word formatting from HTML.

**No DB schema changes.** modification_text column is TEXT — stores HTML from Quill just fine.

**State changes propagated:**
- [x] AGENT_GUIDE.md — comprehensive document chain + lifecycle documentation
- [x] LLM_HANDOFF.md — Rule #6 added
- [x] PROJECT_MEMORY.md — Session 26 entry
- [x] Snapshot saved

### Session 27/28 — 2026-03-05 (Cowork Skills Suite: Build, Test, and Deploy Full Knowledge Layer)
**Agent:** Claude (Anthropic)
**Actions:**
- **Researched Cowork skills system.** Read official Anthropic docs (skills reference, best practices, blog posts) and the built-in skill-creator skill to understand frontmatter schema, packaging, eval framework, and deployment patterns. Created comprehensive `SKILLS_DEVELOPMENT.md` (587 lines) documenting the full skills system, IECC-specific roadmap, and reference links.
- **Built iecc-startup skill (v2).** Enhanced original v1 with dynamic context injection (`!`command``), removed duplicate rules (CLAUDE.md handles those), added knowledge verification step. Packaged as `iecc-startup.skill`.
- **Built iecc-session-close skill.** End-of-session documentation updater with bundled `scripts/session_diff.py` (file change detection + DB snapshot comparison) and `references/session-template.md`. Packaged as `iecc-session-close.skill`.
- **Built 4 additional skills as a coordinated knowledge layer:**
  - **iecc-query** — Database query assistant. Full 12-table + 5-view schema in `references/schema.md`, battle-tested SQL in `references/queries.md`, naming traps (CEPC≠CECP, REC→RECP, status not computed_status), CLI-first approach via iecc_query.py. Serves as shared data layer referenced by all other skills.
  - **iecc-web-dev** — Web development patterns. Two-portal rule, route map in `references/routes.md`, HTMX OOB swap patterns in `references/htmx-patterns.md`, body-to-subgroup mapping trap, auth middleware, CSS theming, 15-point testing checklist.
  - **iecc-doc-gen** — Document generation pipeline. Python→Node.js→DOCX core pattern, PARSE_MOD_HTML_JS rich text pipeline, three doc types (agenda, circ form, modification), PDF conversion via LibreOffice, docx-js patterns in `references/docx-js-patterns.md`.
  - **iecc-meeting-workflow** — Full meeting workflow. End-to-end pipeline (login → agenda → stage → review → send → circ form), meeting states, staging flow in `references/staging-flow.md`, Go Live mode spec in `references/go-live-spec.md`, body-to-subgroup trap.
- **Ran 5 eval test cases** across all 4 skills using skill-creator framework. Results: 24/25 assertions passed (96% mean pass rate). One minor failure: webdev template used `{% extends "base.html" %}` instead of flexible `base_template|default("base.html")` pattern.
- **Generated eval review viewer** — Static HTML at `iecc-skills-eval-review.html` for reviewing all test case outputs.
- **Updated SKILLS_DEVELOPMENT.md** — Moved all 4 skills from "Planned" to "Done" in build priority table with eval pass rates.
- **All 6 skills installed in Cowork** — Verified via screenshot: iecc-startup, iecc-session-close, iecc-query, iecc-web-dev, iecc-doc-gen, iecc-meeting-workflow all visible in Skills panel.
- **Explored IECC standard folder** — Alex shared raw source file system (29 GB, 7,379 files) that the database was built from. Analyzed structure: Code/ (actual IECC text, errata, drafts), Commercial/ and Residential/ (meetings, subgroups, ballots, rosters, proponent comments), Committee Interpretations (numbered pipeline stages 1-11), Communications, Process Documentation. Identified it as the single source of truth with the database serving as a structured index into it.

**Files created:**
- `iecc-startup.skill` — Packaged startup skill (v2)
- `iecc-session-close.skill` — Packaged session-close skill
- `iecc-query.skill` — Packaged query skill with schema + queries references
- `iecc-web-dev.skill` — Packaged web-dev skill with routes + HTMX references
- `iecc-doc-gen.skill` — Packaged doc-gen skill with docx-js patterns reference
- `iecc-meeting-workflow.skill` — Packaged meeting-workflow skill with staging-flow + go-live references
- `iecc-skills-eval-review.html` — Static eval review viewer (97KB)
- `iecc-startup-eval-review.html` — Startup skill eval review viewer (57KB)
- `SKILLS_DEVELOPMENT.md` — Master skills roadmap and Cowork reference doc (587 lines, updated to 26KB)

**Files modified:**
- `SKILLS_DEVELOPMENT.md` — Updated build priority table: all 6 skills marked Done with eval pass rates. Moved 4 skills from "Planned" to description of actual built structure.

**DB changes:** No DB schema changes. No data changes.

**State changes propagated:**
- [x] PROJECT_MEMORY.md — this entry (Session 27/28)
- [ ] DEVELOPMENT.md — no feature status changes (skills are external to web app)
- [ ] AGENT_GUIDE.md — no schema changes
- [ ] LLM_HANDOFF.md — no web pattern changes
- [ ] CLAUDE.md — no project structure changes (skill files are in root, already common pattern)
- [x] SKILLS_DEVELOPMENT.md — all 4 new skills marked as Done

### Session 29 — 2026-03-05 (Centralized Content Database + Portal Content Wiring)
**Agent:** Claude (Anthropic)
**Actions:**
- **Analyzed meeting transcripts end-to-end.** Read two full meeting transcripts (Modeling SG2 3/3/2026, Envelope SG 2/18/2026) in both DOCX and VTT formats. Identified the reality-vs-portal gap: live modifications, further modifications, combined consideration, reason statements in Teams chat, real-time math on screen — none captured by the current portal. Created `PORTAL_ROADMAP.md` synthesizing findings into a three-phase implementation plan.
- **Designed and built centralized content schema.** Created `migrations/002_centralized_content.sql` with 5 new tables (`proposal_text`, `modifications`, `proposal_links`, `documents`, `meeting_events`), 3 column additions (`subgroup_actions.moved_by`/`seconded_by`, `meetings.transcript_path`/`recording_url`), and 11 indexes. Ran migration via Python (SQL file semicolons inside CHECK constraints required workaround).
- **Built content population pipeline.** Created `populate_content.py` — full pipeline that scans the 29 GB IECC Standard folder, registers 1,578 files in `documents` table, extracts proposal language from cdpACCESS DOCX files into `proposal_text` (133 proposals with HTML preserving ICC legislative markup: underline→`<ins>`, strikethrough→`<del>`), extracts 6 modifications, and auto-links 258 cross-references between proposals modifying the same code section.
- **Fixed REC→RECP naming mismatch.** 4 proposal files named `proposal_REC18-25_...` couldn't match to RECP database entries. Added manual mapping and recovered 4 more proposals.
- **Added cdpACCESS numeric file pattern.** CODE_PROPOSAL phase files use `proposal_{cdpaccess_id}_{number}.docx` instead of canonical ID. Added `CDP_PROPOSAL_NUMERIC_RE` pattern and `cdp_id_lookup` dictionary to populate_content.py.
- **Wired centralized content into meeting portal.** Updated `subgroup_portal.py` to batch-load proposal_text, modifications, and proposal_links for all agenda items. Updated `meeting_portal.html` with: proposal language panels (formatted code text with `<ins>`/`<del>` markup), pre-submitted modification panels with "Load into Editor" buttons, cross-reference chips linking related proposals, TEXT/MOD badges on action cards, and "Load Original Proposal Text" button for the Quill editor.
- **Added 4 new queries to `db/queries.py`:** `PROPOSAL_TEXT_FOR_MEETING`, `MODIFICATIONS_FOR_PROPOSALS`, `PROPOSAL_LINKS_FOR_PROPOSALS`, `PROPOSAL_TEXT_BY_UID` — all use dynamic placeholder patterns for batch loading.

**Files created:**
- `PORTAL_ROADMAP.md` — Three-phase roadmap from transcript analysis (Phase 1: proposal language, Phase 2: modifications + meeting actions, Phase 3: post-meeting automation)
- `migrations/002_centralized_content.sql` — SQL migration for 5 new tables, 3 columns, 11 indexes
- `populate_content.py` — Content population pipeline (file scanner + DOCX parser + DB populator + auto-linker)

**Files modified:**
- `web/db/queries.py` — Added 4 centralized content query constants (PROPOSAL_TEXT_FOR_MEETING, MODIFICATIONS_FOR_PROPOSALS, PROPOSAL_LINKS_FOR_PROPOSALS, PROPOSAL_TEXT_BY_UID)
- `web/routes/subgroup_portal.py` — `meeting_portal()` and `unstage_action()` now load proposal_text, modifications, and cross-references for agenda items
- `web/templates/meeting_portal.html` — Added proposal language panels, modification panels, cross-reference chips, TEXT/MOD badges, Load-into-Quill buttons, and supporting CSS/JavaScript

**DB changes:**
- 5 new tables: `proposal_text` (133 rows), `modifications` (6 rows), `proposal_links` (258 rows), `documents` (1,578 rows), `meeting_events` (0 rows — ready for transcript extraction)
- 3 new columns: `subgroup_actions.moved_by`, `subgroup_actions.seconded_by`, `meetings.transcript_path`, `meetings.recording_url`
- 11 new indexes on proposal_uid, meeting_id, doc_type, processed, link endpoints
- Total tables: 18 (was 13 + 3 web app tables)
- Coverage: 133/510 proposals (26%) have extracted text. Gap is primarily PUBLIC_INPUT phase (322 proposals, old cycle, most have only 1 DOCX on disk) and ~38 PUBLIC_COMMENT proposals without DOCX files. Could backfill from monograph PDF.

**State changes propagated:**
- [x] PROJECT_MEMORY.md — this entry (Session 29)
- [x] DEVELOPMENT.md — Priority 3 updated (code language extraction DONE, Quill pre-loading DONE)
- [x] AGENT_GUIDE.md — 5 new tables added to schema section
- [x] LLM_HANDOFF.md — Content loading patterns documented, new query patterns
- [x] CLAUDE.md — populate_content.py and migrations/ added to project structure
- [x] Known issues: coverage gap noted, cost_impact extraction low (1/133)

### Session 30 — 2026-03-05 (Database Perfection: Meeting Audit, DQ Cleanup, Content Backfill)
**Agent:** Claude (Anthropic)
**Actions:**
- **Resolved 11 past-date SCHEDULED meetings.** Used DB evidence (subgroup_actions, consensus_actions, meeting_agenda_items) to classify: 4 → COMPLETED (meetings 70, 67, 88), 7 → CANCELLED. Deleted bogus meetings: meeting 59 (02/24 Res Consensus, no linked records) and meeting 12 (CCC 03/04, only had test portal data — meeting never took place). Next commercial consensus is meeting 13 on 03/11.
- **Entered Brian Shanks SG2 vote results.** 10 subgroup_actions from 03/03 Residential Modeling meeting inserted from chair's email (with Alex's explicit authorization). Includes RECP12-25 marked withdrawn. Source: `Brian Shanks email 2026-03-03`.
- **Resolved 21 of 27 open DQ flags → 6 remaining.** Cleared stale MISSING_ACTION_DATE (dates now filled), NO_ACTION_RECORDED (actions exist), ALTERNATE_MOTION_RECORD, ARTIFACT flags. 6 legitimate flags remain: 2 NO_ACTION_RECORDED (Envelope SG4 hasn't acted), 4 UNVERIFIED_SOURCE (Gayathri email proposals).
- **Backfilled modification text.** Found 3 of 33 "As Modified" actions with data in modifications table: RECP19-25 (6081 chars), REPC20-25 (589 chars), REPC25-25 (13081 chars). 8 active proposals still missing mod text.
- **Linked 37 documents to 9 previously unlinked proposals.** Extended document linkage during content audit.
- **Extended populate_content.py coverage.** Processed Proposal_Text_Sources folder, extracted PDF text, reached 178 proposal_text rows (was 133).
- **Updated AGENT_GUIDE.md email source rule.** Changed from absolute prohibition ("Emails are NEVER a valid source") to judgment-based ("Alex decides what's a valid source"). Session 30 correction per Alex's explicit directive.
- **Comprehensive consensus audit.** Verified 02/25 consensus data intact (26 commercial + 36 residential CAs). Confirmed 30 proposals genuinely pending for consensus — none have been heard yet. Variant proposals (RECP3-25a, RECP17-25b, RECP7-25a) are correctly Decided.

**DB changes (before → after):**
- subgroup_actions: 429 → 442 (+13: 10 from Shanks email, others from earlier session)
- documents: 1,578 → 5,780 (extended scan)
- proposal_text: 133 → 178 (+45 from PDF extraction + Proposal_Text_Sources)
- modifications: 6 → 98 (backfill from circ form parsing + content extraction)
- data_quality_flags open: 27 → 6
- meetings COMPLETED: 27 → 31, CANCELLED: 0 → 6, deleted: 1

**Files modified:**
- `AGENT_GUIDE.md` — Email source rule updated, stale counts updated
- `PROJECT_MEMORY.md` — Session 30 entry, Session 10 issues resolved

**Alex directives this session:**
- "If there's no record of it, it didn't happen" — for determining meeting status
- "I don't give a fuck about RE and CE reason statements" — stop chasing PUBLIC_INPUT phase data gaps
- "Brian's email is valid for the 3/3 meeting" — accept chair email as interim data source
- "Stop searching aimlessly, just ask me directly" — be direct about data gaps

### Session 31 — 2026-03-05 (Data Cleanup & Duplicate Fix)
**Agent:** Claude (Anthropic)
**Actions:**
- Searched full local disk tree for modification docs for REPC21/22/34/46/53 — found circ forms but NO standalone mod docs for HVAC SG proposals
- Searched Outlook for codeapps submissions and chair emails — found Rick Madrid batch submission (Cmte-Submittal-ID-000076) with identical circ forms
- **KEY LEARNING: HVAC SG does NOT create standalone modification documents like commercial track. The "As Modified" changes are described only in the circ form Recommendation/Reason field.**
- Processed 9 circ forms uploaded by Alex (HVAC SG6) + REPC34-25_MOD.docx
- Discovered ALL 10 inserted SG actions were DUPLICATES of existing records (linked via hash UIDs). Merged best data from new extractions into originals (vote breakdowns, reasons where missing), then deleted 10 duplicates. Net SG action count unchanged at 443.
- Fixed vote breakdowns on several originals: RECP8-25 (was 7-3-1 stored backwards), REPC23-25 (6-3-3 corrected), REPC43-25 (9-0-3 corrected)
- Added missing reasons to REPC23-25 (id=327), REPC52-25 (id=400), REPC24-25 (id=399)
- Updated REPC34-25 SG action (id=449): recommendation corrected to "Approved as Further Modified", notes added about Gary Heikkinen's proposed mod (TABLE R408.2 AFUE→COP change). Further modification text pending Brian Shanks circ form.
- Verified RECP2-25 public comment SG actions (Kahre PC2, Wieroniey PC1) already in DB (ids 431, 432) from previous session
- Saved governance reference files (governance_index.json, icc_governance_policies.json) to reference/ folder

**Process understanding gained (from Alex):**
- **Round 3 public comments** now starting: After consensus decisions from Round 2 went out for 30-day public review, public comments are being heard. Envelope SG is first.
- These round 3 PCs are tracked as **continuing actions on the same proposal ID** (e.g., RECP2-25), not as new proposals. They flow through SG → consensus like before.
- REPC34-25_MOD.docx is the **proponent's proposed modification** (input to SG), not the SG's output. SG voted "Approved as Further Modified" — the actual further modification text will come via Brian Shanks' circ form.

**DB state:** 510 proposals, 443 SG actions, 467 consensus actions, 233 DQ flags

**Files modified:**
- `iecc.db` — Fixed vote breakdowns, added reasons, corrected REPC34-25 recommendation
- `PROJECT_MEMORY.md` — Session 31 entry
- `reference/governance_index.json` — Saved governance document index
- `reference/icc_governance_policies.json` — Saved structured governance policies (480 clauses)

### Known Issues from Session 31
**Updated:**
- **REPC34-25 modification text still pending** — SG2 voted "Approved as Further Modified" (8-1-2). Gary Heikkinen's proposed mod (AFUE→COP for TABLE R408.2) was the input. Brian Shanks' circ form with the actual further modification text has not yet been received.
- **REPC21-25, REPC22-25, REPC46-25, REPC53-25 Mod** — "As Modified" but HVAC SG doesn't create standalone modification docs. The modification descriptions exist only in circ form Recommendation/Reason fields, which are now stored in the SG actions. This is the complete record for these proposals.
- **Round 3 public comment tracking** — New pattern: public comments on consensus decisions stored as additional SG actions on the original proposal_uid. First examples: RECP2-25 Kahre PC2 and Wieroniey PC1 (both Disapproved 8-7-0 at Envelope SG 03/04/26).

### Session 32 — 2026-03-06 (Documentation & Skills Deep Integration Audit)
**Agent:** Claude (Anthropic)
**Actions:**
- Completed Passes 3–5 of a multi-pass documentation and skills review initiative. This session was a continuation from Session 31's context overflow.
- **Pass 3** (completed from prior context): Reviewed web docs (LLM_HANDOFF, DEVELOPMENT, ARCHITECTURE), verified startup scripts, checked commercial subgroup DB values, verified file inventory accuracy. Fixed critical bug in `iecc_startup.py` where DQ flag query used nonexistent column `resolved=0` (should be `needs_review=1`). Added CANCELLED meeting status to DEVELOPMENT.md. Expanded ARCHITECTURE.md existing tables from 6→18 entries. Added commercial subgroup DB values and new tools/docs to AGENT_GUIDE.md.
- **Pass 4**: Read files never reviewed in prior passes (PORTAL_ROADMAP.md, web/README.md, iecc_verify.py). Aligned documentation lists across CLAUDE.md, iecc_startup.py, and iecc-startup skill. Added QUERY_COOKBOOK.md and PORTAL_ROADMAP.md to reading order. Updated CLAUDE.md file count from "8 files, ~2000 lines" → "9 files, ~2900 lines". Added completion status markers to all 3 phases in PORTAL_ROADMAP.md.
- **Pass 5** (deep logical integration): Read ALL 6 IECC skills end-to-end plus all reference files. Found and fixed CRITICAL errors: staging-flow.md had every SG# mapping wrong except Modeling (SG2) — all replaced with correct values from config.py. Meeting-workflow SKILL.md falsely claimed proposal text pre-loading was "NOT done yet" when Session 29 completed it. Added missing commercial BODY_TO_SUBGROUP mappings to staging-flow.md. Added "Approved as Modified (Further)" and "Reconsider" to recommendations list. Added Skill Routing Guide table to CLAUDE.md. Added populate_content.py pipeline section to iecc-doc-gen skill. Aligned session-close template and PROJECT_MEMORY.md template to include skills-update checkbox.
- **Integration verification**: Ran 10-point cross-consistency check — all passed: CANCELLED status, BODY_TO_SUBGROUP values, reading list alignment, proposal_uid hash warnings, WAL checkpoint rule, skill routing guide, session template alignment, populate_content.py mention, stale claims check, commercial subgroup values.

**DB changes:**
- No DB schema or data changes.

**Files modified:**
- `CLAUDE.md` — Updated file count (8→9, ~2000→~2900 lines), added QUERY_COOKBOOK.md + PORTAL_ROADMAP.md to reading order, added Skill Routing Guide table
- `AGENT_GUIDE.md` — Added commercial subgroup DB values table, added iecc_startup.py + populate_content.py to Tools, added PORTAL_ROADMAP.md to Essential docs, added errata + subgroup_movements to Reference Tables
- `PROJECT_MEMORY.md` — Updated end-of-session template to include skills-update checkbox
- `PORTAL_ROADMAP.md` — Added completion status markers to all 3 phases
- `iecc_startup.py` — Fixed DQ flag bug (`resolved=0` → `needs_review=1`), added PORTAL_ROADMAP.md to DOCS list
- `web/DEVELOPMENT.md` — Added CANCELLED meeting status
- `web/ARCHITECTURE.md` — Expanded tables from 6→18 entries, added circ_forms + all 5 views
- `web/LLM_HANDOFF.md` — Updated session reference from "21-26" → "21-31"
- `skills-update/iecc-query/SKILL.md` — Added Subgroup DB Values section (commercial + residential), added CANCELLED to meetings status
- `skills-update/iecc-web-dev/SKILL.md` — Added commercial 1:1 mapping note
- `skills-update/iecc-meeting-workflow/SKILL.md` — Fixed stale "NOT done yet" → Session 29 completion, added recommendations
- `skills-update/iecc-meeting-workflow/references/staging-flow.md` — CRITICAL FIX: replaced all wrong SG# values, added commercial mappings
- `skills-update/iecc-session-close/references/session-template.md` — Added skills-update checkbox
- `skills-update/iecc-startup/SKILL.md` — Aligned reading list with CLAUDE.md
- `skills-update/iecc-doc-gen/SKILL.md` — Added Content Extraction Pipeline section (populate_content.py)

**State changes propagated:**
- [x] PROJECT_MEMORY.md — this entry
- [x] DEVELOPMENT.md — Added CANCELLED meeting status
- [x] AGENT_GUIDE.md — Commercial subgroup values, tools, docs, reference tables
- [x] LLM_HANDOFF.md — Updated session range
- [x] CLAUDE.md — Reading order, file count, Skill Routing Guide
- [x] skills-update/ — All 6 IECC skills updated (iecc-query, iecc-web-dev, iecc-meeting-workflow, iecc-doc-gen, iecc-startup, iecc-session-close)
- [x] Known issues — No new issues; no issues resolved

### Session 33 — 2026-03-06 (DB-Is-Truth Overhaul)
**Agent:** Claude (Anthropic)
**Actions:**
- Ran startup, read all 9 docs. **Incorrectly suggested meeting 12 (CCC 03/04) needed updating** — trusted Session 30 docs saying it was "reverted to SCHEDULED" without checking the DB. Meeting 12 was deleted. Alex corrected: that meeting never took place.
- **Root cause:** Documentation was treated as a data source instead of an instruction manual. Row counts and meeting states in docs went stale between sessions, and the startup process never cross-checked docs against the DB.
- **Fixed Session 30 entry** — removed misleading "12→reverted" / "reverted to SCHEDULED" language.
- **Systemic fix — "DB is the sole source of truth" principle applied everywhere:**
  - **CLAUDE.md** — New #1 hard rule: DB is sole source of truth, docs are instructions not data. Never cite doc numbers without verifying.
  - **AGENT_GUIDE.md** — Stripped all hardcoded row counts from schema section. Added prominent warning that counts are approximate reference points. Replaced "(N rows)" annotations with schema-only descriptions.
  - **web/ARCHITECTURE.md** — Stripped all hardcoded row counts from table listing. Added "query DB for current numbers" note.
  - **web/DEVELOPMENT.md** — Fixed stale "133/510" count (was 178 since Session 30). Replaced hardcoded counts with "query DB for current coverage" pattern.
  - **iecc_startup.py** — Added new Phase 2B: DB Cross-Check. Automatically detects: past-date SCHEDULED meetings, orphaned staging data, open DQ flag breakdown, proposals ready for consensus, and upcoming meetings. Also added "DB is sole source of truth" reminder to summary output. Cross-check immediately caught orphaned staging for meeting 88.
  - **iecc-startup skill** — Full rewrite. "DB is sole source of truth" is now the #1 rule, displayed before anything else. Step 3 now requires agents to query the DB directly for pending counts, scheduled meetings, and DQ flags — not recite doc numbers. Readiness report must include live DB counts, startup script issues, upcoming meetings, and any doc-vs-DB discrepancies.

**DB changes:**
- None.

**Files modified:**
- `CLAUDE.md` — New #1 hard rule (DB is truth)
- `AGENT_GUIDE.md` — Stripped hardcoded counts from schema, added "approximate" warning
- `web/ARCHITECTURE.md` — Stripped hardcoded counts from table listing
- `web/DEVELOPMENT.md` — Fixed stale 133→178 count, replaced hardcoded pattern
- `iecc_startup.py` — Added Phase 2B cross-check (stale meetings, orphaned staging, DQ summary, upcoming meetings)
- `PROJECT_MEMORY.md` — this entry + fixed Session 30 entry
- `skills-update/iecc-startup/SKILL.md` — Full rewrite with DB-first verification

**State changes propagated:**
- [x] PROJECT_MEMORY.md — this entry + Session 30 fix
- [x] CLAUDE.md — New #1 hard rule
- [x] AGENT_GUIDE.md — Stripped stale counts
- [x] web/ARCHITECTURE.md — Stripped stale counts
- [x] web/DEVELOPMENT.md — Fixed stale count
- [x] iecc_startup.py — Phase 2B cross-check
- [x] skills-update/iecc-startup — Full rewrite

### Known Issues from Session 30
**New:**
- **30 "As Modified" SG actions missing modification_text** — These have the vote recorded but the actual modification language wasn't extracted. 15 of the 30 DO have circ form documents in the documents table that could be parsed. The other 15 (mostly CE-* and RE-* PUBLIC_INPUT phase) have no source docs on disk. **Alex says: don't chase RE/CE reason statements. Focus forward on REPC/CEPC active proposals.**
- **17 active proposals with no documents linked** — Mostly very new proposals (RECC*-26, REPC36-26, REPC67-25) or multi-part proposals where file naming doesn't match.
- **6 open DQ flags** — All legitimate: 2 NO_ACTION_RECORDED (RECP5-25, REPC15-25 — Envelope SG4 hasn't acted yet), 4 UNVERIFIED_SOURCE (RECC3/4/5-26, REPC67-25 — from Gayathri email, no official confirmation).

**Carried from Session 29:**
- **Cost impact extraction very low** — Only 1/178 proposals had `cost_impact_text` extracted. Low priority.
- **meeting_events table empty** — Schema ready but no transcript extraction pipeline built yet. Phase 2/3 work from PORTAL_ROADMAP.md.

### Known Issues from Session 12
**Remaining:**
- **5 commercial CA dates unfillable** — CE5, CE10, CE86, CE87, CE164 (in CAR but no minutes on disk). 12 more are Withdrawn/DNP (no dates expected).
- **Commercial: 2025-10-07 meeting has 0 actions** — may have been cancelled or data gap.
- **Build scripts not re-validated end-to-end** — DB was modified directly; build scripts may not reproduce current state.

**Resolved:** CA reason coverage (S17, now 77.7%), REPC33/34 circ forms (S18 — were never circ forms), 10 CA dates filled (S17).

### Known Issues from Session 10/10b/10c
**Remaining:**
- **REPC58-25 withdrawal** — recorded but needs verification against official minutes.
- **4 SA vote gaps** — RE169-24, RE33-24, RE52-24, REPC60-25 (No Motion/Withdrawn — no votes applicable).
- **Proposals still without SA:** ~~REPC42-25, REPC49-25, REPC34-25~~ — **RESOLVED Session 30** (Brian Shanks SG2 vote results email).

**Resolved:** Build script normalize_id (S10b), CEC prefix (S10b), SA recommendations (S10c), duplicate SA records (S10c), UNKNOWN subgroups (S10c), malformed dates (S10c), REPC33/34 "circ forms" in Outlook (S18 — were modification docs, not circ forms), REPC65-25 circ form obtained (S20), REPC15-25 withdrawn (S20).

### Historical Issues (Sessions 6–9) — Mostly Resolved
Most issues from early sessions have been resolved through subsequent data mining and cleanup. Key **remaining** items:
- **Low email coverage (~33% residential)** — RE-phase proposals from circ forms lack email data. Not fixable from existing sources.
- **13 modification variants** — e.g., "RE114-24 Kahre" tracked separately from "RE114-24". Could be linked but low priority.
- **CEPC2-25 withdrawal** — Confirmed withdrawn (Session 20). Was previously on wrong proposal (CECP2-25). DQ flag WITHDRAWAL_REQUESTED on CECP2-25 may need cleanup.
- **SharePoint upload built but dormant** — Upload service exists (`services/sharepoint.py`) but requires Azure AD app registration. Alex needs to set up App Registration with `Sites.ReadWrite.All` permission and configure env vars. See Session 25 entry.

All other Session 6–9 issues (governance tables, SG action gaps, vote/reason coverage, residential track build, etc.) were resolved in Sessions 8–12.

---

## How to Resume

Follow the Mandatory First Step in `CLAUDE.md`. That document drives the onboarding sequence.

---

## End-of-Session Template

Copy and fill this in at the end of every session (or use the iecc-session-close skill for the full guided workflow):

```
### Session [N] — [YYYY-MM-DD] ([Short Descriptive Title])
**Agent:** Claude (Anthropic)
**Actions:**
- [First major thing done — be specific about what and why]
- [Data changes: counts before → after]
- [Files created or modified — full relative paths]
- [Issues found or resolved — reference Known Issues if applicable]

**DB changes:**
- [New tables, columns, views, or data modifications]

**Files modified:**
- [List all modified files with what changed]

**State changes propagated:**
- [ ] PROJECT_MEMORY.md — this entry
- [ ] DEVELOPMENT.md — feature status updated?
- [ ] AGENT_GUIDE.md — schema/views/domain knowledge changed?
- [ ] LLM_HANDOFF.md — web patterns/rules changed?
- [ ] CLAUDE.md — project structure changed?
- [ ] skills-update/ — any IECC skills updated? (list which ones)
- [ ] Known issues added/resolved below?
```
