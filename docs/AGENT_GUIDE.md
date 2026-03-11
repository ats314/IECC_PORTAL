# IECC 2027 Database System — Agent Onboarding Guide

> **READ THIS FIRST.** This document gives any AI agent full context to operate on this project immediately. No discovery phase needed.
> **Single unified database: `iecc.db`** with `track` column ('commercial'/'residential') on all tables and views.
> **Last Updated:** 2026-03-06 (Session 33)

---

## Session-Start Checklist

Before doing ANY work, confirm you have completed these steps:
- [ ] Run `python3 tools/iecc_preflight.py` (DB state, pending, DQ, meetings, doc check)
- [ ] Read CLAUDE.md (project structure, hard rules, lessons learned)
- [ ] Read this file (AGENT_GUIDE.md) — you are here
- [ ] Read PROJECT_MEMORY.md (session history, known issues)
- [ ] Confirm to user: "I've read the project docs. Ready to work."

**DO NOT:**
- Run `.schema` or `PRAGMA table_info` — the schema is fully documented below
- Search for files — the file inventory is in the "Files in This Project" section
- Ask Alex what the project is — it's all in this document
- Use `computed_status` — the column is called `status`
- Use prefix `REC` — it does not exist, use `RECP`
- **Conclude a document "doesn't exist" after only checking local disk/database** — You MUST also search Outlook and SharePoint. See "MANDATORY: Document Search Protocol" section below. Local files are downstream copies; upstream sources are email and SharePoint.
- **Touch or reference cdpACCESS / codeapps** — You do not have access and never will.

---

## Who You're Working For

**Alex Smith** — Director of Energy Programs, International Code Council (ICC)
- Secretariat to the IECC Commercial and Residential Consensus Committees
- Manages the 2027 International Energy Conservation Code development process
- Based in Jacksonville, FL (ICC headquarters in Washington, DC)
- Email: alsmith@iccsafe.org
- Staff support: Jason Toves (jtoves@iccsafe.org)

**Alex's role:** He runs the administrative machinery for code development — tracking hundreds of proposals through subgroups, consensus committees, ballots, and final publication. His current tools are messy Excel spreadsheets and SharePoint folders. This project replaces that with a structured SQLite database and LLM-assisted workflow.

---

## What This Project Is

A **proposal tracking system** for the 2027 IECC covering both Commercial and Residential provisions. It tracks code change proposals in a single unified SQLite database (`iecc.db`) from submission through final committee action, including subgroup recommendations, consensus committee votes, errata, and governance rules. Query the DB for current counts — don't rely on numbers in this doc.

### The Database
| File | Notes |
|------|-------|
| `iecc.db` | Unified DB, commercial + residential. All tables have `track TEXT NOT NULL` column ('commercial'/'residential'). Run `python3 tools/iecc_preflight.py` for live counts. |

Original separate databases (`iecc_commercial.db`, `iecc_residential.db`) are archived in `ARCHIVES/backups/pre_merge_20260303/`.

### Tools
| Tool | Purpose |
|------|---------|
| `iecc_query.py` | Status, crossovers, search (ID or proponent), pending, single-proposal lookup (`--status`) |
| `iecc_snapshot.py` | Change detection — save baseline, compare after updates |
| `build_combined_report.py` | Combined disposition XLSX (Dashboard, Commercial, Residential, Crossovers, Data Quality) |

> **Governance tables** (`governance_documents`, `governance_clauses`) have `track='commercial'` only (4 documents, 480 clauses from `icc_governance_policies.json`).

### What You Can Do With It
1. **Status queries** — "What proposals are still pending?" "What did the committee decide on CEPC28-25?"
2. **Agenda preparation** — Generate lists of proposals ready for consensus hearing
3. **Data quality audits** — Find missing votes, conflicting records, incomplete data
4. **Document production** — Draft agendas, status reports, notification letters
5. **Governance lookups** — Search ICC Council Policies for procedural rules
6. **Process verification** — Confirm whether actions followed proper procedure
7. **Cross-track analysis** — Crossover proposals that appear in both commercial and residential tracks

---

## Critical Domain Knowledge

### The IECC Code Development Lifecycle

The ICC code development process produces the 2027 International Energy Conservation Code through three phases. Understanding this lifecycle is essential — it determines what documents exist, what language the subgroups work from, and where to find the authoritative text for any proposal.

#### Phase 1: Public Input (2024) — CLOSED
The general public submits code change proposals (CE for commercial, RE for residential, IRCE for IRC Energy). These are new proposals to change the existing IECC code text. The consensus committee holds hearings and takes action on each proposal. Results are published in a **Committee Action Report (CAR)** and as **Substantive Technical Changes (STCs)**. This phase is DONE — all CE/RE/IRCE proposals have been decided or did not advance. Any without a consensus action are "Phase Closed," NOT "Pending."

**Key document:** The **Monograph** — a published compilation of all approved changes from the Public Input phase. It shows the new code text that was approved, with markup (strikethrough = deleted, underline = added) against the existing published IECC. The monograph becomes the basis for the Public Comment Draft.

#### Phase 2: Public Comment (2025-2026) — WE ARE HERE
The approved changes from Phase 1 are compiled into a **Public Comment Draft (PCD)** — a clean version of the proposed 2027 IECC incorporating all approved public input changes. This was published October 22, 2025.

The public then submits comments on this draft. These are the proposals currently being heard:

| Prefix | What It Is | Example |
|--------|-----------|---------|
| CEPC/REPC | Public comments — requests to change the PCD text | REPC3-25 |
| CECP/RECP | Code proposals — renumbered from CE/RE phase | RECP18-25 |
| CECC/RECC | Committee-generated proposals | RECC3-26 |
| IRCEPC | IRC Energy public comments | IRCEPC1-25 |

**The PCD is the base text.** Every active proposal (REPC, RECP, CEPC, CECP, etc.) proposes changes to the PCD. The proposal document itself contains the relevant code section from the PCD with the proposed changes marked up (underline = new text, strikethrough = deleted text). Some proposals also use italics for defined terms.

Subgroups review these proposals and make recommendations to the Consensus Committee. Subgroups can approve proposals as submitted (the language in the proposal becomes the language recommended to the committee), or approve them **as modified** — meaning the subgroup changed the proposed language. Modifications can come from anywhere: the subgroup chair, committee members, proponents, or the public. They arrive through cdpACCESS (CodeApps), email, or during live Teams meetings. Tracking modifications is messy and is a major pain point for Alex.

**Deadline:** April 30, 2026 for all committee action.

**Vote thresholds for committee action on public comments:**
- **Disapprove a comment** (keep PCD language) = simple majority
- **Accept a comment** (disapprove the STC, reverting to 2024 IECC language) = **2/3 majority**, triggers 30-day comment period
- **Accept a modification** (change the STC) = **2/3 majority**, triggers 30-day comment period

**30-day comment trigger (Round 3):** When a committee action creates a substantive technical change, it gets posted for 30 days of public comment. These "Round 3" public comments flow back through subgroups → consensus, tracked as **additional SG actions on the same proposal_uid** (not new proposals). Example: RECP2-25 had Kahre PC2 and Wieroniey PC1 heard at Envelope SG on 03/04/26. Envelope SG is the first to hear this round.

**HVAC SG documentation pattern:** The residential HVAC SG (SG6) does NOT produce standalone modification documents for "Approved as Modified" proposals. The modification rationale exists only in the circ form's Recommendation/Reason field. This is unlike the commercial track where modification documents with legislative markup are standard. For HVAC SG proposals, the circ form IS the complete record.

#### Phase 3: Final Action (2026) — NOT YET
Committee Action Report (CAR) issued May 7, 2026. Commenter objection period through June 7, 2026. After that: ballots, objections resolution, and Final Draft published December 1, 2026.

### The Document Chain (What Text Does the Subgroup See?)

When a subgroup considers a proposal at a meeting, they work from the **proposal document** — which is a self-contained PDF/DOCX showing:

1. **Header:** Proposal ID, code section reference (e.g., "IECC: R401.3"), proponents
2. **"Revise as follows:" instruction** — what kind of change this is
3. **The full code section text** from the Public Comment Draft, with the proposed changes marked up:
   - **Underline** = new text being added
   - **Strikethrough** = existing text being deleted
   - **Italics** = defined terms (not a change, just code formatting convention)
4. **Reason statement** — why the proponent wants the change
5. **Cost impact** and **Justification**

If the subgroup approves "as modified," the modification may change the proposed language. The modification text is recorded on the circulation form and in the `subgroup_actions.modification_text` column. The modified version is what gets recommended to the Consensus Committee.

**Example — REPC3-25 document chain:**
- **PCD base text:** Section R401.3 (Certificate) — the current draft language as of Oct 2025
- **Proposal:** Adds new language to item 5 about REC ownership and financial contracts (underlined in the proposal document)
- **Subgroup action:** Approved as Modified 5-4 — Mod 2 changed the wording of item 5 to clarify REC conveyance language
- **What the Consensus Committee sees:** The modified version of item 5

### Where to Find Documents

| Document Type | Location | Format | Content |
|--------------|----------|--------|---------|
| **Public Comment Draft (PCD)** | `ARCHIVES/Commercial (CECDC)/Resources/2027 IECC/2027 IECC Public Comment Draft/` | PDF (6.9 MB) | The complete proposed 2027 IECC code text — THE base document |
| **PCD Errata** | Same folder + `Archive/` subfolder | PDF | Corrections to the PCD (multiple versions, latest is 12-13-25) |
| **Monograph** | `ARCHIVES/Commercial (CECDC)/Resources/2027 IECC/Monograph/` | PDF | Phase 1 approved changes with markup |
| **Public Comment documents** | `ARCHIVES/.../2027 IECC Public Comment Monograph/` | PDF | All submitted public comments compiled |
| **Individual proposal PDFs** | `2027_RESIDENTIAL/Residential Subgroups/{subgroup}/{meeting}/` | PDF | Per-proposal documents with markup against PCD |
| **Circulation forms** | Same subgroup meeting folders | DOCX | Official SG action records (vote, recommendation, reason, modification text) |
| **Modification documents** | Subgroup folders, `_MOD.docx` suffix | DOCX | Proposed modifications to proposal language (NOT circ forms) |
| **cdpACCESS** | `https://energy.cdpaccess.com/proposal/{id}/` | Web | Official ICC platform — authoritative proposal text. Many proposals have `cdpaccess_id` in DB — query to check coverage. |

**⚠️ Important:** The residential PCD is the same document as the commercial PCD — the 2027 IECC covers both. Residential provisions are in Chapter 4 (R-prefixed sections like R401.3). Commercial provisions are in Chapters 2-3 (C-prefixed sections). There is NOT a separate residential PCD file on disk — use the same PCD PDF and look for the R-section.

### Code Language Markup Conventions

ICC code documents use consistent formatting:
- **Underline** = new text being added (not in the current code or PCD)
- **Strikethrough** = existing text being deleted
- **Italics** = defined terms (terms that have a specific definition in Chapter 2 of the IECC). These are NOT changes — they're just code formatting convention. Examples: *approved*, *building*, *fenestration*, *solar heat gain coefficient*, *duct system*, *building thermal envelope*
- **Bold** = section headers and numbers

When a proposal says "Revise as follows:" it means the code section text shown is the PCD text with the proposed changes applied using the markup above. Unchanged text appears in normal (roman) type.

### ⚠️ THE NAMING CONVENTION TRAP ⚠️

This is the #1 source of errors. The naming was poorly designed and confuses everyone, including the committee chair.

#### Commercial Prefixes
| Prefix | Meaning | Phase | Example |
|--------|---------|-------|---------|
| `CE` | Commercial Energy (public input) | PUBLIC_INPUT (closed) | `CE114-24` |
| `CECP` | Commercial Energy Code Proposal | CODE_PROPOSAL (active) | `CECP7-25` |
| `CEPC` | Commercial Energy Public Comment | PUBLIC_COMMENT (active) | `CEPC28-25` |
| `CECC` | Commercial Energy Consensus Committee | PUBLIC_COMMENT (active) | `CECC1-26` |

#### Residential Prefixes
| Prefix | Meaning | Phase | Example |
|--------|---------|-------|---------|
| `RE` | Residential Energy (public input) | PUBLIC_INPUT (closed) | `RE114-24` |
| `RECP` | Residential Energy Code Proposal | CODE_PROPOSAL (active) | `RECP18-25` |
| `REPC` | Residential Energy Public Comment | PUBLIC_COMMENT (active) | `REPC45-25` |
| `RECC` | Residential Energy Consensus Committee | PUBLIC_COMMENT (active) | `RECC3-26` |
| `IRCE` | IRC Energy (public input, Chapter 11) | PUBLIC_INPUT (closed) | `IRCE3-24` |
| `IRCEPC` | IRC Energy Public Comment | PUBLIC_COMMENT (active) | `IRCEPC1-25` |

#### ⚠️⚠️⚠️ CRITICAL ERRORS TO AVOID ⚠️⚠️⚠️

**ERROR 1 — CEPC vs CECP:** ONE LETTER APART, completely different proposals.
- `CEPC7-25` (Fester) — already decided, Disapproved 18-6-4 on Jan 21
- `CECP7-25` (Swiecicki) — still pending, has SG recommendation

**ERROR 2 — REC is WRONG, use RECP:** The prefix "REC" does NOT exist. It MUST be "RECP".
- Just as CEC was renamed to CECP on the commercial side, REC was renamed to RECP on the residential side.
- This error caused a MAJOR data corruption in Session 10 — 18 phantom proposals, inflated pending counts, failed reconciliation with staff lists.
- If you see "REC" anywhere in source data, normalize it to "RECP" immediately.

**ERROR 3 — REPC vs RECP:** Same one-letter trap as commercial side.
- `REPC` = Residential Energy **Public Comment** (new proposals submitted during public comment)
- `RECP` = Residential Energy **Code Proposal** (proposals renumbered from RE phase)

**Rule:** Always verify the full proposal ID including proponent name when there's any ambiguity. The database uses `canonical_id` (normalized) and `proposal_uid` (SHA1 hash) to disambiguate.

**Historical renames:**
- `CEC` → `CECP` (Commercial Energy Code Proposal)
- `REC` → `RECP` (Residential Energy Code Proposal)

#### Phase Model
| Phase Key | Commercial | Residential | Status |
|-----------|-----------|-------------|--------|
| `PUBLIC_INPUT` | CE | RE, IRCE | **CLOSED** — proposals decided or did not advance. NOT pending. |
| `CODE_PROPOSAL` | CECP | RECP | **ACTIVE** — currently being heard |
| `PUBLIC_COMMENT` | CEPC, CECC | REPC, RECC, IRCEPC | **ACTIVE** — currently being heard |

RE and CE proposals are NOT "still being heard." They are closed. Any RE/CE proposal without a consensus action is "Phase Closed," NOT "Pending."

### Subgroups

**Commercial:**
| Abbreviation | Full Name |
|-------------|-----------|
| EPLR | Commercial EPLR Subgroup |
| Envelope/ENVL | Envelope and Embodied Energy Subgroup |
| HVACR | Commercial HVACR and Water Heating Subgroup |
| Modeling/MODL | Commercial Modeling Subgroup |
| Cost | Cost Effectiveness Subgroup |
| Admin | Commercial Administration Subgroup |

**Residential:**
| DB Value (use in queries) | SG# | Common Name |
|---------------------------|-----|-------------|
| `Consistency and Administration (SG1)` | SG1 | Admin |
| `Modeling (SG2)` | SG2 | Modeling — Chair: Brian Shanks |
| `EPLR (SG3)` | SG3 | EPLR — DONE hearing proposals |
| `Envelope (SG4)` | SG4 | Envelope — First to hear Round 3 PCs |
| `Existing Buildings (SG5)` | SG5 | Existing Building |
| `HVACR (SG6)` | SG6 | HVAC — Chair: Rick Madrid. No standalone mod docs. |

**⚠️ Use the exact DB value (with SG# suffix) in WHERE clauses.** `current_subgroup LIKE '%Modeling%'` works but `current_subgroup = 'Modeling'` does NOT — the DB value is `'Modeling (SG2)'`. Legacy records also have `'Energy Performance and Labeling Requirements (SG3)'` for EPLR, and some records use `'Energy Performance and Labeling Requirements'` without the SG number.

**⚠️ Disk folder names DON'T match DB subgroup names.** When searching for files on disk, use this mapping:

| DB Value | Disk Folder (`2027_RESIDENTIAL/Residential Subgroups/`) |
|----------|--------------------------------------------------------|
| `Consistency and Administration (SG1)` | `Admin Subgroup` |
| `Modeling (SG2)` | `Modeling Subgroup` |
| `EPLR (SG3)` | `Residential EPLR` |
| `Envelope (SG4)` | `Envelope and Embodied Carbon Subgroup` |
| `Existing Buildings (SG5)` | `Residential Existing Buildings` |
| `HVACR (SG6)` | `HVAC & Water Heating` |

#### Commercial Subgroup DB Values

Commercial subgroups do NOT use SG# suffixes — their DB values match meeting body names directly:

| DB Value (use in queries) | Common Name |
|---------------------------|-------------|
| `Commercial Administration Subgroup` | Admin |
| `Commercial Modeling Subgroup` | Modeling |
| `Commercial EPLR Subgroup` | EPLR |
| `Commercial HVACR and Water Heating Subgroup` | HVACR |
| `Envelope and Embodied Energy Subgroup` | Envelope (note: NOT prefixed with "Commercial") |
| `Commercial Consensus Committee` | Consensus Committee |

**Special status-like values in `current_subgroup`:** Some commercial proposals have `'Committee Action Complete'`, `'Posted for Public Comment'`, `'Withdrawn'`, or `None` — these are workflow states, not real subgroup assignments. Filter them out with `current_subgroup NOT IN ('Committee Action Complete', 'Posted for Public Comment', 'Withdrawn') AND current_subgroup IS NOT NULL`.

Commercial source documents: `ARCHIVES/Commercial (CECDC)/Resources/2027 IECC/Commercial Subgroups/`

Subgroups review proposals and make recommendations. The Consensus Committee makes final decisions. A subgroup recommendation is advisory only.

### Vote Thresholds
- **Simple majority** to disapprove a public comment (draft language stays)
- **2/3 majority** to accept a comment requesting change (triggers 30-day comment period)
- Subgroup votes are simple majority recommendations

---

## Database Schema (Quick Reference)

> **Unified schema.** All tables have a `track` column ('commercial'/'residential'). All views include `track` as the first column.
>
> **⚠️ ROW COUNTS BELOW ARE APPROXIMATE REFERENCE POINTS, NOT LIVE DATA.** Always run `python3 tools/iecc_preflight.py` or query the DB directly for current counts. Never cite these numbers to Alex as fact without verifying. The DB is the sole source of truth for all IECC proposal data — documentation only teaches you how to query it correctly.

### Core Tables

**`proposals`** — Master registry (commercial + residential, split by `track` column)
```sql
-- Key columns:
track TEXT NOT NULL,            -- 'commercial' or 'residential'
proposal_uid TEXT PRIMARY KEY,  -- SHA1(canonical_id)[:16]
canonical_id TEXT UNIQUE,       -- e.g., 'CEPC28-25'
original_id TEXT,               -- Pre-normalization ID (e.g., 'CEC1-25')
cdpaccess_id INTEGER,           -- cdpACCESS system ID
cdpaccess_url TEXT,
cycle TEXT,                     -- '2024' or '2025'
phase TEXT,                     -- 'PUBLIC_INPUT', 'CODE_PROPOSAL', or 'PUBLIC_COMMENT'
phase_locked INTEGER,           -- 1 = PUBLIC_INPUT phase (read-only)
prefix TEXT,                    -- 'CE', 'CEPC', 'CECP', 'CECC'
part TEXT,                      -- 'Part I', 'Part II', or NULL
code_section TEXT,
proponent TEXT,                 -- 'Lastname, Firstname'
proponent_email TEXT,
initial_subgroup TEXT,
current_subgroup TEXT,
withdrawn INTEGER DEFAULT 0,
withdrawn_date TEXT,
withdrawn_reason TEXT,
source_file TEXT,
created_at TEXT,
```

**`consensus_actions`** — Committee decisions (use `is_final=1` for authoritative current action)
```sql
-- Key columns:
track TEXT NOT NULL,            -- 'commercial' or 'residential'
proposal_uid TEXT NOT NULL,     -- FK to proposals
sequence INTEGER DEFAULT 1,    -- Order (supports Postpone → Reconsider chains)
action_date TEXT,               -- NOTE: column is 'action_date', not 'meeting_date'
recommendation TEXT,            -- See allowed values below
recommendation_raw TEXT,        -- Original text before normalization
vote_for INTEGER, vote_against INTEGER, vote_not_voting INTEGER,
vote_raw TEXT,                  -- Original vote string
reason TEXT, modification_text TEXT, notes TEXT,
moved_by TEXT, seconded_by TEXT,
is_final INTEGER DEFAULT 0,    -- 1 = authoritative current action
source TEXT, source_file TEXT,  -- Provenance tracking
```

**CA allowed recommendations:** `Approved as Submitted`, `Approved as Modified`, `Approved as Modified (Further)`, `Disapproved`, `Withdrawn`, `Do Not Process`, `No Motion`, `Postponed`, `Reconsider`, `Remand to Subgroup`

**`subgroup_actions`** — Subgroup recommendations
```sql
-- Key columns:
id INTEGER PRIMARY KEY,
track TEXT NOT NULL,            -- 'commercial' or 'residential'
proposal_uid TEXT,              -- FK to proposals (use HASH uid, not canonical_id!)
subgroup TEXT,                  -- Subgroup name (e.g., 'HVACR (SG6)', 'Modeling (SG2)')
action_date TEXT,
recommendation TEXT,            -- See allowed values below
recommendation_raw TEXT,        -- Original text before normalization
vote_for INTEGER, vote_against INTEGER, vote_not_voting INTEGER,
vote_raw TEXT,                  -- Original vote string from circ form
reason TEXT, modification_text TEXT, notes TEXT,
source_file TEXT,               -- Path to circ form or source attribution
moved_by TEXT, seconded_by TEXT,
```

**⚠️ proposal_uid MUST be the hash UID from the `proposals` table, NOT the canonical_id string.** Always look up the hash first: `SELECT proposal_uid FROM proposals WHERE canonical_id = 'REPC34-25'`. Session 31 created 10 duplicate records by using canonical_id strings as proposal_uid — the originals existed under hash UIDs and the view joined on both.

**SA allowed recommendations:** `Approved as Submitted`, `Approved as Modified`, `Approved as Further Modified`, `Disapproved`, `No Motion`, `Discussion Only`, `Withdrawn`. Legacy unnormalized values also exist: `AM`, `AS`, `Approved`.

**A single proposal can have MULTIPLE subgroup_actions** — e.g., the original SG hearing plus Round 3 public comment actions heard by the same or different SG.

**`subgroup_movements`** — Subgroup reassignment history
```sql
proposal_uid TEXT, sequence INTEGER,
move_from TEXT, move_to TEXT,  -- NOT from_subgroup/to_subgroup
move_date TEXT, source_file TEXT,
```

**`errata`** — Public Comment Draft corrections
```sql
reporter TEXT, report_date TEXT, code_section TEXT,
description TEXT, related_proposal TEXT,
confirmed INTEGER DEFAULT 0, corrected INTEGER DEFAULT 0,
note TEXT, source_file TEXT,
```

### Reference Tables
- **`meetings`** — All have `track` column. Columns: `meeting_date`, `meeting_time`, `body`, `phase`, `status` (COMPLETED/SCHEDULED/CANCELLED), `tentative`, `action_count`, `notes`, `source`
- **`data_quality_flags`** — All have `track` column. Columns: `proposal_uid`, `canonical_id`, `table_name`, `flag_type`, `raw_value`, `resolved_value`, `needs_review` (0/1), `created_at`. **No `severity` or `source` column.**
- **`governance_documents`** — ICC Council Policies (CP#7-04, CP#12C-25, CP#28-05, CP#49-21)
- **`governance_clauses`** — Individual clauses with hierarchy, searchable text, cross-references
- **`errata`** — PCD errata corrections. Columns: `track`, `reporter`, `report_date`, `code_section`, `description`, `related_proposal`, `confirmed` (0/1), `corrected` (0/1), `note`, `source_file`
- **`subgroup_movements`** — Proposal reassignment history between subgroups. Columns: `track`, `proposal_uid` (FK), `sequence`, `move_from`, `move_to`, `move_date`, `source_file`

### Web App Tables (created by web application)
- **`sg_action_staging`** — Temporary staging area for meeting portal actions. Columns: `meeting_id`, `proposal_uid`, `recommendation`, `vote_for`, `vote_against`, `vote_not_voting`, `reason`, `modification_text`. Cleaned up when meeting is sent to secretariat.
- **`meeting_agenda_items`** — Meeting agenda items. Columns: `meeting_id`, `proposal_uid`, `order_num`. Created during agenda auto-populate.
- **`circ_forms`** — Circulation form document lifecycle tracking (Session 25). Columns: `meeting_id` (UNIQUE), `track`, `subgroup`, `body`, `generated_at`, `pdf_path` (absolute path to generated doc), `status` (`pending_review`/`approved`/`uploaded`/`rejected`), `reviewed_by`, `reviewed_at`, `sharepoint_url`, `rejection_reason`. Auto-created when chair sends meeting to secretariat.

### Centralized Content Tables (Session 29)

- **`proposal_text`** — Actual code language extracted from cdpACCESS DOCX files. Columns: `proposal_uid` (FK), `source_type` (`cdpaccess_docx`/`monograph_pdf`/`manual_entry`/`transcript`), `source_path`, `proposal_html` (formatted with `<ins>`/`<del>` for ICC markup), `proposal_plain`, `reason_text`, `cost_impact_text`, `code_section_text`, `extracted_at`, `verified` (0/1), `verified_by`, `verified_at`, `notes`. Unique on `(proposal_uid, source_type)`.
- **`modifications`** — Pre-submitted modification documents (what was SUBMITTED, not what the committee DECIDED). Columns: `proposal_uid` (FK), `track`, `submitted_by`, `submitted_date`, `source_path`, `modification_html`, `modification_plain`, `reason_text`, `status` (`received`/`posted_to_sharepoint`/`approved_by_committee`/etc.), `meeting_id` (FK, nullable), `parent_modification_id` (self-FK for "further modified" chains), `extracted_at`, `notes`.
- **`proposal_links`** — Cross-references between proposals. Columns: `proposal_uid_a` (FK), `proposal_uid_b` (FK), `link_type` (`combined_consideration`/`superseded_by`/`companion`/`depends_on`/`conflicts_with`/`same_section`), `created_by` (`manual`/`auto_scanner`/`transcript_extraction`), `notes`, `created_at`. Unique on `(proposal_uid_a, proposal_uid_b, link_type)`.
- **`documents`** — Registry of every file on disk tied to a proposal or meeting. Columns: `proposal_uid` (FK, nullable), `meeting_id` (FK, nullable), `track`, `doc_type` (`proposal_docx`/`modification_docx`/`pnnl_analysis`/`circ_form_docx`/`circ_form_pdf`/`transcript_docx`/`transcript_vtt`/`agenda_pdf`/`agenda_docx`/`monograph_pdf`/`pcd_pdf`/`proponent_comment`/`other`), `file_name`, `file_path` (full disk path, UNIQUE), `file_size`, `file_hash`, `discovered_at`, `processed` (0/1), `processed_at`, `notes`.
- **`meeting_events`** — Structured data from meeting transcripts (schema ready, not yet populated). Columns: `meeting_id` (FK), `proposal_uid` (FK, nullable), `event_type` (`motion`/`second`/`vote`/`amendment`/`further_modification`/`withdrawal`/`discussion`/etc.), `speaker`, `content`, `vote_for`/`vote_against`/`vote_abstain`, `vote_outcome`, `timestamp_seconds`, `source`, `confidence` (0.0-1.0), `verified` (0/1).

**Column additions (Session 29):** `subgroup_actions.moved_by TEXT`, `subgroup_actions.seconded_by TEXT`, `meetings.transcript_path TEXT`, `meetings.recording_url TEXT`.

> **Not in current DB:** `reference_rules`, `system_instructions` — from Session 2, not yet restored.

### Key Views

**`v_current_status`** — The most useful view. Every proposal with computed lifecycle status.
```sql
SELECT * FROM v_current_status WHERE status = 'Pending' AND track = 'commercial';
-- Returns: track, canonical_id, prefix, phase, proponent, current_subgroup, code_section,
--          withdrawn, sg_recommendation, sg_vote_for, sg_vote_against, sg_date,
--          ca_recommendation, ca_vote_for, ca_vote_against, ca_date,
--          status (Decided/Withdrawn/Pending/Phase Closed)
```
> **⚠️ CRITICAL:** The column is `status` (NOT `computed_status`). Values are title-case: `Decided`, `Withdrawn`, `Pending`, `Phase Closed`. NOT SCREAMING_SNAKE.
>
> **Warning:** 3 artifact proposals (CE115-24 AM, CEPC48-25 Part II, CEPC50-25) appear as Pending but are not genuinely pending. Filter them out or check `data_quality_flags` for `ARTIFACT_%` flag types.
>
> **Note (Session 13):** Proposals with CA recommendation of Postponed, Remand to Subgroup, or Reconsider in active phases (CODE_PROPOSAL, PUBLIC_COMMENT) now show as "Pending" instead of "Decided". This reflects that these proposals still need further action.

**`v_ready_for_consensus`** — Proposals with SG action but no consensus action yet.
```sql
SELECT * FROM v_ready_for_consensus WHERE track = 'residential';
-- Returns: track, canonical_id, code_section, proponent, current_subgroup,
--          sg_recommendation, sg_action_date, sg_vote_for, sg_vote_against,
--          sg_vote_not_voting, sg_reason, sg_modification
```

**`v_full_disposition`** — Flattened for reporting/export (all proposals with SG + consensus data).
```sql
-- Returns: track, canonical_id, prefix, phase, proponent, code_section, current_subgroup,
--          withdrawn, sg_body, sg_recommendation, sg_vote, sg_date,
--          ca_recommendation, ca_vote, ca_date, ca_reason, moved_by, seconded_by,
--          consensus_source, status
```

**`v_data_quality_review`** — All data quality flags sorted by needs_review status. Includes `track` column.

**`v_multi_action_proposals`** — Proposals with multiple consensus actions (procedural chains like Postpone → Reconsider → Final). Includes `track` column.

---

## Current Status

> **⚠️ LIVE COUNTS:** Run `python3 tools/iecc_preflight.py` to get current counts (decided, pending, withdrawn, CA, SA, DQ). For a human-readable summary, see `IECC_STATUS_REPORT.md`. Do NOT hardcode counts in docs — they go stale fast.

### Key Dates
| Milestone | Date |
|-----------|------|
| Round 3 public comments starting | March 2026 (Envelope SG first, 03/04/26) |
| Next commercial consensus | March 11, 2026 |
| Next residential consensus | March 12, 2026 |
| Committee action deadline | April 30, 2026 |
| CAR issued | May 7, 2026 |
| Commenter objection deadline | June 7, 2026 |
| Final Draft 2027 IECC | December 1, 2026 |

### Key People (Residential)
| Name | Role | Subgroup | Notes |
|------|------|----------|-------|
| Rick Madrid | SG Chair | HVAC (SG6) | Submits circ forms via codeapps. Email batch submissions (Cmte-Submittal-ID-000076). |
| Brian Shanks | SG Chair | Modeling (SG2) | Circ forms pending for several proposals incl. REPC34-25. |
| Denise Beach | SG member | HVAC (SG6) | Named on circ forms (REPC43-25). |
| Nathan Kahre | Proponent (NAHB) | Envelope (SG4), HVAC | Multiple proposals (REPC53/56/58/59/60). Also files round 3 public comments. |
| Gayathri Vijayakumar | Proponent | Modeling (SG2), Envelope (SG4) | RECP2-25, REPC34-25_MOD author. UNVERIFIED_SOURCE flag on RECC3-26 etc. |
| Jay Crandell | Committee member | HVAC (SG6) | REPC52-25 circ form. |
| Robby Schwarz | SG member | HVAC (SG6) | Named on multiple circ forms (RECP8-25, REPC24-25, REPC23-25). |
| Mike Moore | SG member | HVAC (SG6) | Named on circ forms (REPC21-25, REPC22-25). |

---

## Source Priority (When Data Conflicts)

Sources are listed in descending authority:

1. **Circulation forms** — Official subgroup action records, signed by SG chair. **THE ONLY valid source for subgroup actions.**
2. **Approved meeting minutes (PDF)** — Committee Action Report, consensus committee minutes. **THE ONLY valid source for consensus actions.**
3. **JSON minutes files** — Digitized from official minutes (hand-verified by Alex)
4. **Excel tracking sheets** — Alex's working documents
5. **Derived/computed data** — Anything the build script calculates

When sources conflict, always prefer the higher-ranked source. Flag conflicts in `data_quality_flags`.

### ⚠️ EMAIL AS A SOURCE — USE JUDGMENT ⚠️

**Default rule:** Emails are not a primary source. Circ forms and official minutes are authoritative.

**Exception (Session 30):** When Alex explicitly directs you to use email data (e.g., "use Outlook to find out"), **do it.** Chair emails with vote results (e.g., Brian Shanks' SG2 vote results from 3/3/2026) are valid interim records. Enter the data, mark `source_file` with the email attribution, and note that circ forms will replace them when they arrive. Do NOT refuse to enter data Alex told you to enter because of a documentation rule.

**What to avoid:** Do NOT independently mine emails and insert data without Alex's direction. The Session 14 error was inserting 4 SG actions from Gayathri's email without Alex asking — those had no date, no reason, no backing. That's different from Alex saying "use Brian's email."

**Bottom line:** Alex decides what's a valid source, not this document. When in doubt, ask him.

---

## ⚠️ MANDATORY: Document Search Protocol ⚠️

**When looking for ANY document (circ form, modification, agenda, minutes), search ALL locations in this order. Fast/local first, slow/remote last. Do NOT stop after the fast checks and conclude "it doesn't exist."**

1. **`documents` table + `modifications` table** — Instant. Check if we already have the file indexed or the text extracted. This is a 1-second SQL query. Always do this first.
2. **Local disk** — Fast `find` or `ls` on the relevant meeting folder. Check the subgroup meeting folder AND the consensus meeting folder for the relevant date.
   - **Residential:** `2027_RESIDENTIAL/Residential Subgroups/{folder name}/`
   - **Commercial:** `ARCHIVES/Commercial (CECDC)/Resources/2027 IECC/Commercial Subgroups/`
   - **⚠️ Disk folder names don't match DB subgroup names** — see the mapping table in the Subgroups section above.
3. **Outlook email** — If steps 1-2 come up empty, search Outlook. Chairs submit circ forms and modifications via email to Alex. Search for the proposal ID, chair name, or subgroup name. This is where documents arrive FIRST from chairs, before they make it to local disk.
4. **SharePoint** — `Shared Documents/.../Commercial Subgroups/` or `Residential Subgroups/`. The official ICC document repository. Chairs upload circ forms here.

**DO NOT search cdpACCESS / codeapps.** You do not have access and never will.

**The critical rule: if local searches fail, you MUST search Outlook and SharePoint before concluding a document doesn't exist.** Local disk is a downstream copy that lags behind. If a chair emailed a circ form last week and Alex hasn't synced it to the folder yet, it's in Outlook but not on disk.

**Session 30 lesson:** Agent searched the `documents` table and local folders for CECP7-25's circ form, didn't find it, and concluded it hadn't been submitted — without ever checking Outlook or SharePoint. The circ form was sitting in Outlook the entire time (from gjohnsonconsulting@gmail.com, subject "2/9/26 Modeling SB circ form & meeting notes"). ALWAYS complete all 4 steps.

---

## Common Agent Tasks

### "What's the status of proposal X?"
```sql
SELECT * FROM v_current_status WHERE canonical_id = 'CEPC28-25';
```

### "What proposals are ready for the next consensus meeting?"
```sql
SELECT * FROM v_ready_for_consensus ORDER BY current_subgroup;
```

### "Show me all decisions from a specific meeting"
```sql
SELECT p.canonical_id, p.proponent, ca.recommendation,
       ca.vote_for, ca.vote_against, ca.vote_not_voting, ca.reason
FROM consensus_actions ca
JOIN proposals p ON ca.proposal_uid = p.proposal_uid
WHERE ca.action_date = '2026-02-25' AND ca.is_final = 1
ORDER BY p.canonical_id;
```

### "What proposals are assigned to Modeling subgroup?"
```sql
SELECT canonical_id, proponent, withdrawn
FROM proposals
WHERE current_subgroup LIKE '%Modeling%' AND phase = 'PUBLIC_COMMENT';
```

### "Show me all data quality issues"
```sql
SELECT * FROM data_quality_flags ORDER BY needs_review DESC, created_at DESC;
```

### "Show me all data quality issues needing review"
```sql
SELECT * FROM v_data_quality_review WHERE needs_review = 1;
```

### "What's the full action history for a proposal?"
```sql
-- All consensus actions (not just final)
SELECT sequence, action_date, recommendation,
       vote_for, vote_against, vote_not_voting, reason, is_final
FROM consensus_actions
WHERE proposal_uid = (SELECT proposal_uid FROM proposals WHERE canonical_id = 'CEPC11-25')
ORDER BY sequence;
```

### "Show proposals with multiple actions (procedural chains)"
```sql
SELECT * FROM v_multi_action_proposals ORDER BY canonical_id, sequence;
```

---

## Files in This Project

### Essential (Read These)
| File | Purpose |
|------|---------|
| `CLAUDE.md` | Project structure, hard rules, lessons learned, end-of-session protocol |
| `AGENT_GUIDE.md` | **THIS FILE** — Schema, naming traps, queries, verification protocol |
| `PROJECT_MEMORY.md` | Session history and decisions log |
| `iecc.db` | Unified database (SQLite) — all tables have `track` column |
| `QUERY_COOKBOOK.md` | Ready-to-use SQL queries |
| `PORTAL_ROADMAP.md` | Three-phase portal improvement plan |
| `IECC_STATUS_REPORT.md` | Combined status report — both commercial and residential |

### Tools
| File | Purpose |
|------|---------|
| `iecc_query.py` | Unified cross-database query tool |
| `iecc_snapshot.py` | Change detection (save/compare snapshots) |
| `iecc_verify.py` | Auto-check all docs against DB (run every session) |
| `iecc_preflight.py` | Session start briefing (DB state, pending, DQ, meetings) |
| `iecc_startup.py` | FULL startup: docs inventory + DB health + server test |
| `populate_content.py` | Content extraction pipeline (DOCX → proposal_text table) |

### Build & Report Scripts
| File | Purpose |
|------|---------|
| `build_commercial_db.py` | Commercial DB build script |
| `build_residential_db.py` | Residential DB build script |
| `build_combined_report.py` | Single master report XLSX generator (11 sheets) |

### Source Data (Commercial)
| File | Purpose |
|------|---------|
| `ARCHIVES/commercial_consensus_committee_minutes_updated.json` | Committee decisions |
| `ARCHIVES/commercial_envelope_subgroup_recommendations_UNIFIED_v2.json` | Envelope SG |
| `ARCHIVES/commercial_eplr_subgroup_recommendations_UNIFIED.json` | EPLR SG |
| `ARCHIVES/commercial_hvacr_subgroup_recommendations.json` | HVACR SG |
| `ARCHIVES/commercial_modeling_subgroup_recommendations.json` | Modeling SG |
| `ARCHIVES/admin_subgroup_recommendations_with_dates_v4.json` | Admin SG |

### Source Data (Residential)
| Directory | Content |
|-----------|---------|
| `2027_RESIDENTIAL/Residential Subgroups/` | Circulation forms (216 DOCX), SG meeting files |
| `2027_RESIDENTIAL/Residential Consensus Committee/` | Consensus meeting minutes (PDFs) |

### Generated Reports
| File | Content |
|------|---------|
| `IECC_2027_Combined_Disposition.xlsx` | Single master report: Dashboard, Commercial/Residential Proposals, CA, SA, Crossovers, Data Quality, Errata, Meetings. **Generate on demand:** `python3 build_combined_report.py` (not persisted in repo — regenerate when needed). |

### Reference Documents
| File | Location | Content |
|------|----------|---------|
| Public Comment Draft (PCD) | `ARCHIVES/Commercial (CECDC)/Resources/2027 IECC/2027 IECC Public Comment Draft/` | The base code text — THE authoritative document for all active proposals |
| PCD Errata | Same folder | Corrections to PCD (latest: 12-13-25) |
| Monograph | `ARCHIVES/Commercial (CECDC)/Resources/2027 IECC/Monograph/` | Phase 1 approved changes with markup |
| Public Comment Monograph | `ARCHIVES/Commercial (CECDC)/Resources/2027 IECC/2027 IECC Public Comment Monograph/` | All submitted public comments compiled (4.3 MB) |
| Committee Action Report | `ARCHIVES/Commercial (CECDC)/Resources/2027 IECC/Committee Action Report (CAR)/` | Phase 1 committee decisions |
| IECC Committee proposal process | `ARCHIVES/Commercial (CECDC)/Resources/2027 IECC/Monograph/IECC Committee proposal process.pdf` | Process diagram |

Source documents for commercial subgroups: `ARCHIVES/Commercial (CECDC)/Resources/2027 IECC/Commercial Subgroups/`
Source documents for residential subgroups: `2027_RESIDENTIAL/Residential Subgroups/`
Residential consensus meeting documents: `2027_RESIDENTIAL/Residential Consensus Committee/`

---

## Things That Will Trip You Up

1. **⚠️ REC does NOT exist — use RECP** — The prefix "REC" is WRONG. The correct residential code proposal prefix is "RECP" (Residential Energy Code Proposal). Same pattern as CEC→CECP. This caused a major data corruption in Session 10.
2. **CEPC vs CECP / REPC vs RECP** — One letter difference, completely different proposals. Always check proponent name. This applies to BOTH tracks.
3. **PUBLIC_INPUT phase is CLOSED** — CE and RE proposals are not pending. They were decided or did not advance. Only CODE_PROPOSAL and PUBLIC_COMMENT phase proposals are active.
4. **`is_final` flag** — Some proposals have multiple consensus actions (Postpone → Reconsider → Final decision). Always filter on `is_final = 1` for current status.
5. **Withdrawn proposals** — Check `withdrawn = 1` before including in active lists.
6. **CEPC48-25 Part II** — Flagged as residential code (R404.2.2). Not a commercial item despite the CEPC prefix.
7. **CEPC50-25** — Orphan parent stub. Both Part I and Part II were decided separately. The base record is resolved.
8. **CE115-24 AM** — Alternate motion record from Excel, not a real proposal. CE115-24 was decided (Disapproved 17-10-3).
9. **PDFs are ZIP archives** — The project PDFs contain JPEG images + OCR text. Use `unzip` not pypdf to extract.
10. **SharePoint access** — Energy Documents folder on ICC SharePoint is not publicly accessible. Requires browser extension or direct file upload.
11. **Duane Jonlin** — Commercial committee chair. Sometimes uses wrong prefixes (CEPC when he means CECP). Verify carefully.
12. **Crossover proposals** — Some CE/CEPC proposals appear in the residential database (they were heard by both committees). Use `iecc_query.py --crossovers` to see them.
13. **Subgroup meeting minutes are NOT parsed by the build pipeline.** Circ forms and consensus committee minutes are. But withdrawals, reassignments, and some votes only appear in SG meeting minutes. This is the #1 source of stale data in the DB. When something doesn't reconcile, check the SG meeting minutes folder first.
14. **Proposal variants (a/b suffixes)** — RECP17-25b, RECP3-25a, RECP7-25a are separate DB records from their base proposals. The variant is usually the committee's modified version of the same underlying code change. If the variant was decided, the base may be moot — but don't assume. Ask Alex.
15. **EPLR SG3 data gap** — EPLR is DONE hearing proposals (Hensley confirmed 3/2/2026). **Resolved in Session 17:** IRCEPC1-25 (AS 9-0-0), REPC54-25 (AS 9-0-0), REPC55-25 (AS 9-0-0), REPC64-25 (D 6-0-3) all have circ forms ingested. REPC25-25 reassigned to Admin SG1, REPC56-25 reassigned to EB SG5. **Still open:** REPC65-25 (no circ form, not on March 12 agenda), REPC3-25 (has SA but AS vs AM discrepancy — DB says AS 5-4, Toves chat says AM 5-4, needs circ form).
16. **Teams meeting recordings** — All subgroup and consensus meetings are done through Teams. Recordings, transcriptions, notes, and chats are available. These are a major untapped data source for filling gaps, especially where circ forms are missing. Meetings live in GROUP CHATS, not team channels.
17. **Agenda-first rule for missing data** — When a proposal has NO subgroup action, your FIRST step is to check if it's on an upcoming meeting agenda. Query the `meetings` table for scheduled meetings, then check the agenda files in the subgroup's folder on disk (e.g., `2027_RESIDENTIAL/Residential Subgroups/Modeling Subgroup/` for agendas). A missing circ form almost always means the SG hasn't voted yet — NOT that we lost the paperwork. Only after confirming the proposal is NOT on any upcoming agenda should you search Outlook or other sources. **This was learned the hard way in Session 18** — wasted 30 minutes in Outlook downloading a modification document when the proposal was on the next day's agenda.
18. **`_MOD.docx` files are NOT circ forms** — Files like `REPC34-25_MOD.docx` are modification documents (proposed code text changes). They do NOT contain vote data, recommendations, or dates. Circ forms have a standard template with SG chair signature, vote counts, recommendation, and reason.
19. **Subgroup assignments can change** — Proposals may be deferred or reassigned from one SG to another mid-cycle. The DB `current_subgroup` field may be stale. When a proposal appears on a different SG's agenda, update the DB immediately.

20. **DB crash safety — WAL mode + checkpoint after every write.** The DB uses WAL journal mode to survive VM crashes. After any INSERT/UPDATE/DELETE, always run `conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')` before `conn.close()`. This prevents stale WAL files from corrupting the DB on next session start. Do NOT change journal mode. Preflight auto-repairs corruption if it happens, but prevention is better.
21. **Session will crash without warning — act accordingly.** Never batch cleanup to "end of session." After every meaningful DB change: checkpoint, update docs, save snapshot. After every file creation: put it in the right place immediately. Leave no loose ends. The VM can die mid-sentence.
22. **Never dump scratch files into the IECC project folder.** Use `/sessions/[session-id]/` for temp work. Only final deliverables and project files go in the IECC folder. Every stray file you leave is Alex's problem.

---

## How to Update the Database

### Adding new meeting data
1. Get minutes/agenda document from Alex
2. Extract decisions: proposal ID, recommendation, vote counts, reason, mover/seconder
3. Insert into `consensus_actions` with appropriate `sequence` and `is_final` flags
4. Update any previous `is_final` flags if this supersedes earlier actions
5. Add meeting to `meetings` table if new date

### Adding new subgroup recommendations
1. Get **circulation form** (DOCX/PDF) — this is the ONLY valid source
2. Extract: proposal ID, subgroup, recommendation, vote, reason, date
3. Insert into `subgroup_actions` with `source_file` pointing to the actual circ form path
4. Cross-check against `proposals` table for correct `proposal_uid`
5. **Do NOT insert SG actions from emails, verbal reports, or agendas.** If no circ form exists, don't create the record.

### Marking withdrawals
```sql
UPDATE proposals SET withdrawn = 1, withdrawn_date = '2026-02-25',
       withdrawn_reason = 'Withdrawn by proponent at consensus meeting'
WHERE canonical_id = 'CEPC2-25';
```

### Adding data quality flags
```sql
INSERT INTO data_quality_flags (proposal_uid, canonical_id, table_name, flag_type, raw_value, needs_review)
VALUES ((SELECT proposal_uid FROM proposals WHERE canonical_id = 'CEPC28-25'),
        'CEPC28-25', 'subgroup_actions', 'VOTE_MISMATCH',
        'SG vote differs from minutes vs circulation form', 1);
```

---

## Verification Protocol — Before Reporting Status to Alex

The DB has been wrong before. Every time you report pending counts, agenda items, or subgroup workload to Alex, run this checklist FIRST:

### For any "pending" proposal:
1. **Check for withdrawals in subgroup meeting minutes.** The build pipeline does NOT parse SG minutes. Withdrawals often happen at SG meetings and only appear in those minutes PDFs. Look in `2027_RESIDENTIAL/Residential Subgroups/[subgroup name]/` for meeting minute files.
2. **Check for variants.** Search for the proposal ID with wildcard suffixes (e.g., RECP3-25a, RECP3-25b). If a variant was decided at consensus, the base proposal may be moot. Flag it to Alex.
3. **Check the source.** If the proposal was added from email (`source_file LIKE '%email%'` or `source_file LIKE '%gayathri%'`), it's unverified. Say so.
4. **Check subgroup assignment.** SG assignments in the DB may be stale — proposals get reassigned at SG meetings (which we don't parse). Cross-reference against the most recent SG agenda if available.

### For any SG action:
1. **Confirm a circ form exists on disk.** `find . -iname "*[proposal_id]*" | grep -i "circ"`. If no circ form, the SG action record is suspect.
2. **Check the `source_file` column.** If it says anything other than a circ form or official minutes path, flag it.

### For reconciliation against external lists (Gayathri, SG chairs, agendas):
1. **Discrepancies mean the DB is probably wrong,** not the external list. Alex's staff know their proposals.
2. **Trace every discrepancy to a source document** before updating anything. Read the actual PDF/DOCX.
3. **Never bulk-update from an email.** Each change needs its own source doc.

---

## Alex's Communication Style

Alex is direct, fast-paced, and frustrated with tools that waste his time. He values:
- **Speed** — Get to the answer fast. Don't ask discovery questions you can answer yourself.
- **Accuracy** — Wrong data is worse than no data. Verify before stating.
- **Practical output** — He wants agendas, status lists, and draft documents. Not explanations of methodology.
- **Proactive identification of problems** — Flag errors, conflicts, and missing data without being asked.

When Alex says "review the database" he means: query it, cross-reference it, find problems, and tell him what needs fixing. Not: describe the schema back to him.
