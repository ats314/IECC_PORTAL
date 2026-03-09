# Portal Roadmap — From Document Chaos to Working System

> **Purpose:** Big-picture plan for getting the IECC portal from "metadata-only" to a tool that actually reduces Alex's workload. Built from analysis of two real meeting transcripts, the full document chain trace, and the current portal state.
>
> **Created:** 2026-03-05 (Session 29)

---

## What I Learned From the Transcripts

I read both meetings end-to-end — the Modeling SG2 meeting (March 3, 2026, ~2.5 hours) and the Envelope SG meeting (February 18, 2026, ~48 minutes). Here's what actually happens versus what the portal currently supports.

### Reality vs. Portal

| What Actually Happens | What the Portal Does Today |
|---|---|
| Chairs pull up proposal text by opening cdpACCESS or SharePoint docs in separate browser tabs | Portal shows proposal ID and metadata only — Quill editor starts blank |
| Modifications arrive before the meeting as DOCX files posted to SharePoint folders | Portal has no modification text, no link to the source document |
| Modifications get reworked LIVE during the meeting — Gayathri did real-time subtraction of PNNL credit values on screen for REPC34-25 | Portal has a Quill editor but nothing is pre-loaded, no way to capture live edits |
| A modification of a modification happens (REPC34-25: initial mod failed 3-5-3, then "further modified" to 1.23 COP baseline, passed 8-1-2) | Portal treats each proposal as having one possible action |
| Multiple proposals get combined for consideration (RECP9+15 heard together, REPC34+49 linked) | No cross-reference tracking |
| Reason statements are typed into Teams chat during or right after a vote | Portal has a reason field but no integration with what chairs actually do |
| Proposals get withdrawn mid-meeting via verbal request (REPC12-25) | No withdrawal workflow |
| Agenda gets reordered on the fly at participant request | Agenda is static once created |
| Circ forms are needed the SAME DAY after a meeting (Amy Schmidt: "I'll try to get a circulation form done really quick") | Circ form generation exists but requires manual data entry of the action that just happened |
| Chair struggles to find and display the right document version (Amy had her car shopping screen up accidentally) | Portal doesn't help chairs find or display the documents they need |

### Key Patterns Across Both Meetings

**Document flow is not linear.** A proposal doesn't just go "submitted → modification → vote." It goes "submitted → modification submitted → modification discussed → modification rejected → further modification proposed live → math done on screen → further modification passed → different reason statement than original → related proposal disapproved as superseded → circ form needed today."

**Chairs are overwhelmed by document juggling.** Both Brian Shanks (SG2) and Amy Schmidt (Envelope) spent significant meeting time finding, displaying, and switching between documents. The portal should eliminate this entirely.

**The chat channel is a data source.** Reason statements, suggested language modifications, and procedural motions all flow through Teams chat. This is unstructured data that currently requires manual extraction.

**Cross-references are everywhere.** REPC34 and REPC49 are linked (49 disapproved because 34's modification covered it). REPC4 and REPC11 are linked (need to advance together). RECP9 and RECP15 were combined for consideration. These relationships are critical for chairs and currently exist only in people's heads.

---

## Transcript Format Recommendation

**Use DOCX as the primary format for LLM extraction.** It reads naturally, groups speaker turns into coherent paragraphs, and preserves context across a discussion. Vote sequences are readable and continuous.

**Keep VTT for timestamping and archival.** VTT has millisecond-precision timestamps and explicit `<v Speaker>` tags that make it perfect for building a searchable index or linking back to video recordings.

**Don't try to parse transcripts in real-time during meetings.** The value is in post-meeting extraction — feeding the DOCX to an LLM to pull out structured data (votes, reason statements, modifications, cross-references) and then loading that into the portal.

---

## The Plan: Three Phases

### Phase 1: Get Proposal Language Into the Portal (Weeks 1-2) — ✅ MOSTLY COMPLETE (Session 29-30)

> **Status:** Steps 1-4 done. 178/510 proposals have extracted text with ICC markup. Portal pre-loads code language, modifications, and cross-references. 26% coverage gap remains (PUBLIC_INPUT phase proposals lack DOCX files).

This is the foundation. Everything else depends on chairs being able to see the actual proposal text in the portal instead of switching to cdpACCESS.

**Step 1: Build the DOCX parser**
- Use python-docx to extract proposal language from cdpACCESS DOCX files
- Map formatting runs to HTML: `run.underline` → `<ins>`, `run.font.strike` → `<del>`, `run.bold` → `<b>`, `run.italic` → `<i>`
- Extract structured fields: proposal text with markup, reason statement, cost impact
- Test with REPC35-25 (already on disk, same TABLE R408.2 as the traced example)

**Step 2: Build the file scanner**
- Scan the IECC Standard folder tree for proposal DOCX files matching DB proposal IDs
- Pattern: `proposal_{canonical_id}_{cdp_id}.docx` in `Public Comments/` folders
- Also scan for `*_MOD*.docx` files and match them to proposals
- Generate a mapping: proposal_uid → file path → extracted HTML

**Step 3: Add storage**
- New columns or table for `proposal_language_html`, `reason_text`, `cost_impact_text`
- Store the extraction source (file path, extraction date) for auditability
- Flag proposals where no DOCX was found (fall back to monograph PDF plain text)

**Step 4: Wire the portal**
- Pre-load the Quill editor with extracted proposal language when a chair opens a proposal
- Show the formatted text (underline for additions, strikethrough for deletions)
- Display reason statement and cost impact below the code text
- Add a "source" indicator showing where the text came from (cdpACCESS DOCX, monograph PDF, or manual entry)

**What this gives you:** Chairs open a proposal in the meeting portal and immediately see the formatted code text. No more switching to cdpACCESS or hunting for PDFs.

### Phase 2: Handle Modifications and Meeting Actions (Weeks 3-5) — PARTIALLY DONE

> **Status:** Step 8 (cross-reference tracking) done — 258 auto-detected proposal links in DB, cross-reference chips in portal. Steps 5-7 partially done (modification ingestion built via populate_content.py, 102 modifications in DB, Quill editor loads them). Step 6 (meeting action capture redesign for "further modified" / combined consideration) NOT YET DONE.

This is where the portal starts doing real work during meetings.

**Step 5: Modification ingestion**
- Parse `_MOD.docx` files the same way as proposals (same formatting extraction)
- Link each modification to its parent proposal
- Show the modification alongside the original proposal language in the portal
- Support multiple modifications per proposal (the subgroup might receive more than one)

**Step 6: Meeting action capture**
- Redesign the action staging to capture the full reality:
  - **Simple case:** Approve / Disapprove / Approve as Modified — with vote tally (Yes-No-Abstain)
  - **Complex case:** "Approve as Further Modified" — captures that the original modification was rejected and a new one was crafted during the meeting
  - **Withdrawal:** Proposal withdrawn by proponent (no vote needed)
  - **Combined consideration:** Two or more proposals heard together, linked in the record
  - **Superseded:** Proposal disapproved because another proposal's modification covered it (REPC49 → REPC34)
- Each action stores: vote tally, reason statement, who moved/seconded, the final text (if modified)

**Step 7: Reason statement workflow**
- Pre-populate from the proposal's original reason statement
- Allow the chair to edit during the meeting (since the actual reason for the committee's action may differ from the proponent's reason)
- Accept paste from Teams chat (where reason statements actually get written)

**Step 8: Cross-reference tracking**
- Link related proposals (REPC34↔REPC49, REPC4↔REPC11, RECP9↔RECP15)
- Show linked proposals when viewing any one of them
- When an action is taken on one, prompt about the linked proposal(s)
- Types: "combined for consideration," "superseded by," "depends on," "companion to"

**What this gives you:** The portal captures what actually happened during the meeting, including the messy reality of failed modifications, further modifications, withdrawals, and cross-references. This is the data that flows into circ forms.

### Phase 3: Post-Meeting Automation (Weeks 6-8) — PARTIALLY DONE

> **Status:** Step 10 (circ form auto-generation) done — pipeline built in Session 25, generates DOCX/PDF on "Send to Secretariat". Step 11 (file system reconciliation) partially done — documents table has 5,780 files scanned. Steps 9 (transcript extraction) and 12 (meeting prep dashboard) NOT YET DONE. meeting_events table schema exists but is empty.

This is where Alex's workload drops dramatically.

**Step 9: Transcript-powered data extraction**
- After a meeting, upload the DOCX transcript
- LLM extracts: proposals discussed, vote outcomes, reason statements, modifications proposed, who moved/seconded
- Present the extraction to Alex for review and correction (not blind automation)
- One-click import of verified data into the portal's meeting record
- This catches anything the chair didn't enter during the live meeting

**Step 10: Circ form auto-generation**
- The circ form generation pipeline already exists in the codebase
- Wire it to pull from the completed meeting actions (Phase 2 data)
- Pre-populate: proposal ID, action taken, vote tally, reason statement, final text with markup
- Generate the DOCX circ form with one click after the meeting is finalized
- Send to Alex/secretariat for review before posting to SharePoint

**Step 11: File system reconciliation**
- Periodic scan of the IECC Standard folder for new documents
- Detect new proposal DOCX files, modification DOCX files, and circ form PDFs
- Flag discrepancies: "REPC35-25 has a modification on disk but not in the portal"
- Alert Alex when documents appear that need attention

**Step 12: Meeting prep dashboard**
- For an upcoming meeting, show: which proposals have text loaded, which have modifications, which are missing documents
- Flag: "REPC34-25 has no DOCX on disk — language is from monograph PDF (no formatting)"
- One-click view of all linked/related proposals for the meeting's agenda items

**What this gives you:** Post-meeting work goes from "manually type everything into forms and generate documents from scratch" to "review what the system extracted, correct any errors, click generate."

---

## What This Doesn't Cover (Yet)

- **Live modification editing during meetings.** Phase 2 captures the final result, but doesn't give chairs a collaborative editor for crafting modifications in real-time. That's a bigger feature that could come later.
- **cdpACCESS integration.** The DOCX files on disk are the primary source. If ICC ever provides an API, that would be better, but we work with what we have.
- **Teams chat integration.** Extracting reason statements directly from Teams chat would be ideal but requires Microsoft Graph API access. For now, chairs paste from chat into the portal.
- **Video/audio playback.** VTT timestamps could eventually link to meeting recordings, but that's a quality-of-life feature, not a core workflow need.

---

## Priority Order (If Time Is Limited)

If you can only do some of this before the next round of meetings:

1. **Phase 1, Steps 1-4** (proposal language in the portal) — this is the single highest-impact change. Chairs can finally see what they're voting on without leaving the portal.
2. **Phase 2, Step 6** (meeting action capture redesign) — the portal needs to handle "further modified" and "combined consideration" or it can't record what actually happens.
3. **Phase 3, Step 10** (circ form auto-generation from meeting data) — this is where Alex's time gets freed up the most.

Everything else is important but these three unlock the core value proposition: the portal becomes the one place chairs go during a meeting, and the one place Alex goes after a meeting.

---

## On Transcripts Specifically

The meeting transcripts are a gold mine for backfilling data and for quality assurance. Specific uses:

- **Backfill historical meeting actions** that weren't captured in the portal (many meetings have already happened)
- **Verify vote tallies** — the transcript is the authoritative record of who voted how
- **Extract reason statements** that were spoken but not formally recorded
- **Identify cross-references** between proposals that only emerged during discussion
- **Train the LLM extraction pipeline** — these two transcripts are the perfect test cases for building a prompt that reliably extracts structured meeting data

The DOCX format is better for all of these. VTT adds timestamps if you ever want to link back to video, but the DOCX is what you'd feed to an LLM.

---

## Summary

The portal's fundamental problem isn't that it's missing features — it's that it doesn't have the *content*. Chairs can't use it for meetings because the proposal text isn't there. Alex can't generate circ forms from it because the meeting actions aren't captured with enough detail. The document chain (proposal → modification → action → circ form) exists on disk and in people's heads, but not in the database.

This plan fills that gap in three phases: get the content in (Phase 1), capture what happens to it (Phase 2), and automate what comes after (Phase 3). Each phase delivers standalone value, and each one makes the next one more powerful.
