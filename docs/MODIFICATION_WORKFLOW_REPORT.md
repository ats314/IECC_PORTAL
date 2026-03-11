# Modification Workflow: Deep Research Report

**Prepared for:** Alex Smith, Director of Energy Programs
**Date:** March 10, 2026
**Context:** ICC Code Development Platform — Portal readiness for ICC leadership demo

---

## The Real-World Scenario

A subgroup chair has their agenda set for a meeting. Three days before, a proponent emails a modification as a Word document. The chair reviews it, agrees to allow it on the agenda. At the meeting, the subgroup deliberates — they may accept the proponent's modification as-is, or further modify the language with their own additions (underlined) and deletions (struck through). Per CP#28-05 §4.3.4, the text presentation standard is: deletions are shown struck out, additions are shown underlined. Multiple modification versions may exist by the time the subgroup votes.

The question: how well does the portal handle this end-to-end?

---

## What CP#28-05 Actually Requires

The IECC follows the **Codes development policy** (CP#28-05), not the Standards consensus procedures (CP#12C-25). Key sections that govern modifications:

**§4.3.4 — Text Presentation:** "Text proposed to be deleted shall be shown struck out. Text proposed to be added shall be shown by underlining." This is the canonical ICC legislative markup convention that the portal already implements correctly via Quill.js (underline = additions, strikethrough = deletions).

**§4.3.5.5 — Floor Modifications at Committee:** "A floor modification shall include a copyright release as prescribed by ICC." This means any modification introduced during a live meeting (not pre-submitted through cdpACCESS) requires a copyright release. The portal doesn't currently capture or track this.

**§6.2 — Agenda Distribution:** Agenda distributed 14 days in advance. The portal's auto-populate and manual add features handle this timeline, but there's no enforcement mechanism.

**§4.3.1 — Code Change Proposals:** Proposals and modifications are submitted through cdpACCESS. The portal complements cdpACCESS — it doesn't replace it.

---

## Current State of the Portal

### What Works Well

The portal has a solid foundation for modification handling. Here's what's already built and functioning:

**Pre-submitted modifications display correctly.** The `modifications` table holds 484 rows extracted from source DOCX files. When a chair opens the portal or Go Live, modifications for each agenda proposal are loaded and displayed in collapsible panels with submitter name, date, and the full rich text content. The "Load into Editor" buttons copy the modification HTML into the Quill editor, pre-setting the recommendation to "Approved as Modified."

**Quill.js editor enforces ICC markup.** The toolbar exposes underline and strikethrough as the primary formatting tools, matching the CP#28-05 convention. Bold and lists are available as secondary tools. The editor produces clean HTML that flows through to document export.

**Document export pipeline handles rich text.** The `PARSE_MOD_HTML_JS` constant in `doc_generator.py` correctly parses `<u>`, `<s>`, `<strong>`, and `<em>` tags from Quill output and converts them to docx-js TextRun objects with proper formatting. Both the circulation form and modification document exports use this pipeline.

**Go Live mode supports quick modification loading.** "Load Mod" buttons let the chair pull in a pre-submitted modification with one click, and the "Load Original" button pulls the proposal's code language as a starting point for committee markup.

**Staging captures modification text.** The `sg_action_staging` table stores `modification_text` as HTML from the Quill editor, and the staging route validates that "Modified" recommendations include non-empty modification text.

### The Gaps

**1. No upload pathway for new modifications.**
The 484 existing modifications were batch-extracted from DOCX files by `populate_content.py`. There is no UI for a chair (or proponent) to upload a new modification document before or during a meeting. The chair's only option today is to manually type or paste modification text into the Quill editor — which is impractical for complex multi-paragraph code changes that arrive as formatted Word documents.

**2. No version tracking.**
When a chair loads a pre-submitted modification into the editor and then the committee further modifies it, the original version is effectively overwritten. There's no record of "proponent submitted version A → committee modified to version B → committee further amended to version C." The `modifications` table has `parent_modification_id` and `submitted_by` columns, but they're almost entirely unused (0 of 484 rows have a parent, only 4 have a submitter).

**3. No distinction between proponent modifications and committee modifications.**
CP#28-05 distinguishes between pre-submitted modifications (through cdpACCESS) and floor modifications (at the meeting). The portal treats all modification text identically. There's no label, tag, or metadata to indicate whether the text came from a proponent submission, was loaded from the database, or was composed live by the committee.

**4. No "modification received" workflow before the meeting.**
The scenario described — proponent sends a modification 3 days before, chair accepts it — has no portal counterpart. The chair would need to separately communicate this to the secretariat and hope the modification gets into the system before the meeting.

**5. No copyright release tracking for floor modifications.**
CP#28-05 §4.3.5.5 requires a copyright release for floor modifications. The portal has no mechanism to flag or track whether this requirement has been satisfied.

**6. No side-by-side comparison.**
When multiple modifications exist for a proposal, or when the committee wants to compare the original code language against a proposed modification, there's no diff view or side-by-side display. The chair must mentally compare by toggling between loaded versions.

---

## Recommended Architecture

The modifications pipeline should be organized around three distinct phases that mirror how real meetings work: **Pre-Meeting Preparation**, **During the Meeting**, and **Post-Meeting Record**.

### Phase 1: Pre-Meeting Preparation (Chair receives modification, adds to agenda)

**New feature: Modification Upload on Meeting Portal**

Add a "Pre-Submitted Modifications" management section to the meeting portal, visible to chairs before going live. For each proposal on the agenda:

- An "Upload Modification" button opens a panel where the chair can either paste rich text directly or upload a DOCX file
- For DOCX uploads: extract the text content server-side (reuse the pattern from `populate_content.py`) and store as HTML in the `modifications` table with proper metadata
- Each uploaded modification gets tagged: `submitted_by` (proponent name), `submitted_date`, `meeting_id` (linking it to the upcoming meeting), and `status = 'pending_review'`
- The chair can preview the uploaded modification, edit it for formatting cleanup, then mark it as "accepted for agenda"

**Database changes needed:**
- Populate `meeting_id` on modifications to link them to specific meetings
- Add `modification_type` column: `'proponent_submitted'`, `'committee_floor'`, or `'committee_amendment'`
- Add `accepted_by` and `accepted_date` columns for the chair's approval

**Why this matters for the demo:** ICC leadership will want to see that the portal handles the real workflow — a chair receiving a Word doc from a proponent and getting it into the system without secretariat intervention.

### Phase 2: During the Meeting (Go Live mode handles deliberation)

This is where the portal needs to shine for the demo. The Go Live screen is already well-designed for speed. Here are the enhancements:

**Feature: Version-Aware Modification Panel**

When a proposal has pre-submitted modifications, Go Live should display them in a clearly labeled panel above the action form:

```
┌─────────────────────────────────────────────────┐
│  CEPC28-25 — §C402.1.3 Building Envelope        │
│  Code Section: Table C402.1.3 | Proponent: Doe   │
├─────────────────────────────────────────────────┤
│  📎 Pre-Submitted Modifications                  │
│  ┌───────────────────────────────────────────┐   │
│  │ ▸ Mod by J. Smith (Mar 7) — Proponent     │   │
│  │   [Preview] [Load into Editor]             │   │
│  └───────────────────────────────────────────┘   │
│                                                   │
│  ── Committee Action ──────────────────────────   │
│  [AS] [AM] [Disapproved] [Withdrawn] [Postponed] │
│  ...                                              │
└─────────────────────────────────────────────────┘
```

Each modification shows its origin (proponent vs. committee), submitter, and date. The "Load into Editor" action is a clear one-click operation.

**Feature: "Start from Original" vs "Start from Mod" workflow**

When the chair selects "Approved as Modified," present two clear starting points:

1. **"Start from Original Code Language"** — loads the proposal text from `proposal_text` table (the existing "Load Original" button, but with better labeling)
2. **"Start from [Proponent]'s Modification"** — loads a specific pre-submitted modification

This clarifies the committee's starting point. If the committee says "we'll work from Smith's modification but change section 3," the chair loads the proponent's version and makes targeted edits.

**Feature: Committee Markup Indicators**

When the committee further modifies a loaded modification, the Quill editor should visually distinguish what the committee changed. This is tricky because both the proponent and committee use the same underline/strikethrough convention (per CP#28-05).

The practical approach: don't try to track character-level diffs in real time. Instead, when the chair submits the action, store both the **source modification ID** (which pre-submitted mod was loaded, if any) and the **final committee text**. The version chain is preserved through metadata, not through in-editor diffing.

The staging table needs: `source_modification_id` — a nullable FK to `modifications.id` indicating which pre-submitted modification was used as the starting point.

**Feature: Quick Amendment Workflow**

Sometimes the committee makes a small amendment during deliberation — "change 'shall' to 'should' in line 3." For these cases, the editor should support a rapid find-and-replace within the loaded text. Add a small "Find & Replace" button to the Quill toolbar area. This is faster than scrolling through dense code language looking for the right word.

### Phase 3: Post-Meeting Record (Finalization and document export)

**Feature: Modification Provenance in Circ Form**

When the meeting is finalized and the circ form is generated, each modification should carry its provenance:

- "Based on modification submitted by J. Smith (Mar 7), further modified by committee"
- "Committee floor modification (copyright release required)"
- "Proponent's modification approved without change"

This metadata flows into the `source_modification_id` on the committed `subgroup_actions` row and gets rendered in the circ form export.

**Feature: Version History on Proposal Detail Page**

The public-facing proposal detail page (`/proposals/{id}`) should show the modification lineage:

```
Modification History:
  Mar 7  — J. Smith submitted modification (proponent)
  Mar 10 — Residential Modeling SG: Approved as Modified
           Committee further modified Smith's version
           [View committee markup]
```

This uses the existing timeline pattern on the proposal detail page but adds modification-specific context.

---

## Execution Plan: What to Build and When

### For the Demo (Priority — build this week)

These are low-effort, high-impact changes that make the portal feel complete:

1. **Label pre-submitted modifications with origin metadata in Go Live.** The data exists in `modifications` — just render `submitted_by` and `submitted_date` more prominently. This is a template-only change.

2. **Add "Start from Original" / "Start from Modification" choice when "Approved as Modified" is selected in Go Live.** Two buttons instead of one. Template + minor JS change.

3. **Track source_modification_id on staging.** Add the column to `sg_action_staging`, populate it when "Load Mod" is clicked, carry it through to `subgroup_actions` on finalization. Small schema change + route logic.

4. **Show modification type labels.** Add `modification_type` to the `modifications` table and label the 484 existing rows as `'proponent_submitted'`. Display this as a badge ("Proponent" / "Committee") in the portal.

### Post-Demo (Phase 2 — next 2-4 weeks)

5. **Modification upload UI on meeting portal.** Chair can paste formatted text or upload a DOCX for a specific proposal. Server extracts content to HTML and stores in `modifications` table with full metadata.

6. **Copyright release flag for floor modifications.** Boolean column on `subgroup_actions` + checkbox in the action form that appears when no pre-submitted modification was loaded.

7. **Modification provenance in circ form export.** Extend `doc_generator.py` to include source attribution in the exported document.

### Future (Phase 3 — as needed)

8. **Side-by-side diff view.** Show original code language next to proposed modification with visual diff highlighting. Would use a JS diff library.

9. **Proponent self-service upload.** Proponents submit modifications directly through a portal form (authenticated via cdpACCESS integration or separate login).

10. **Full version chain.** Populate `parent_modification_id` to link committee amendments back to the proponent's original submission, creating an auditable chain.

---

## How the Meeting Actually Runs (Go Live Walkthrough)

Here's the flow with these enhancements, as the chair would experience it during a live subgroup meeting on Teams:

1. Chair opens Go Live, shares screen. The first proposal appears with its code language and any pre-submitted modifications visible in a labeled panel.

2. Chair says: "CEPC28-25 — we received a modification from Smith. Let me pull it up." Clicks "Load Smith's Modification." The Quill editor fills with the proponent's markup showing additions underlined and deletions struck through.

3. Committee discusses. Someone says: "I'd accept this if we change 'shall comply' to 'shall be designed to comply' in the second paragraph." Chair uses find-and-replace or manual edit in the Quill editor to make that change.

4. Chair reads back the final language. Committee votes. Chair enters the vote (or clicks "Unanimous" which auto-fills from the member roster), selects "Approved as Modified," and clicks "Save & Next."

5. The system records: recommendation = "Approved as Modified", source_modification_id = Smith's submission ID, modification_text = the final committee-amended HTML. Auto-advances to the next proposal.

6. After all proposals are addressed, chair clicks "Review & Send." The review page shows each action with modification provenance. Chair clicks "Send to Secretariat" and the circ form generates with proper attribution.

This workflow takes about 30-60 seconds per proposal in Go Live — comparable to the paper-based process but with automatic document generation and record-keeping.

---

## Technical Notes

**Quill.js is the right choice.** It produces clean, predictable HTML that the existing `PARSE_MOD_HTML_JS` pipeline handles well. No need to switch editors. The toolbar already exposes the ICC-standard formatting options.

**The JavaScript-inside-Python document generation pattern is fragile but functional.** Don't change it for the demo. The `PARSE_MOD_HTML_JS` constant handles both HTML and plain text gracefully, and both the circ form and modification document exports use it consistently.

**The `modifications` table schema is ready for expansion.** The unused `parent_modification_id`, `submitted_by`, and `meeting_id` columns were designed for exactly the version-tracking features described above. The migration is mostly about populating existing columns, not adding new ones.

**Database numbers (current):**
- 484 modifications in the database (4 with submitter info, 0 linked to meetings)
- 217 proposals with extracted code language text (43% coverage)
- 124 committed subgroup actions with modification text
- 510 total proposals across both tracks

---

## Summary

The portal's modification handling is architecturally sound — the Quill editor, HTML storage, document export pipeline, and Go Live integration form a working chain. The gaps are in workflow orchestration: there's no way to get a proponent's modification into the system before a meeting, no version tracking when the committee amends a loaded modification, and no provenance metadata in the final record.

The demo-critical items (1-4 above) are all template and minor schema changes that can be built in a day or two. They'll make the portal feel like a complete meeting management tool rather than a data entry form. The post-demo items (5-7) are the real workflow improvements that chairs will need once the portal is in active use.
