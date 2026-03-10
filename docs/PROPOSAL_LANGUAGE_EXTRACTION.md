# Proposal Language Extraction — Process Document

> **Purpose:** Document the end-to-end process for extracting proposal language and modification text from source files and loading it into the portal. Built from a traced example of REPC34-25 (Heikkinen, Gas-Fired Heat Pump Credits).
>
> **Created:** 2026-03-05 (Session 29)

---

## The Goal

Every proposal in the portal should display:
1. **Proposal language** — the exact code text being proposed, with underline (additions) and strikethrough (deletions) formatting
2. **Modification language** — pre-submitted changes to the proposal, also with markup formatting
3. **Reason statement** — why the proponent wants the change

Currently the portal shows only a proposal ID and metadata. The Quill rich text editor exists but starts blank. Chairs reference cdpACCESS or PDFs in separate browser tabs.

---

## Source Documents (Where Proposal Language Lives)

### 1. cdpACCESS Proposal DOCX (Primary Source)

**What:** Individual `.docx` files exported from cdpACCESS, ICC's official code development platform.

**Format:** Consistent template across all proposals:
- Header: Proposal ID (e.g., `REPC34-25`)
- Code reference: `IECC: TABLE R408.2`
- Proponents line with name, org, email
- `2027 International Energy Conservation Code (DRAFT)` header
- `Revise as follows:` instruction (bold)
- **Code section text with formatting runs:**
  - `run.bold` = section headers and numbers
  - `run.underline` = new text being added
  - `run.font.strike` = existing text being deleted
  - `run.italic` = defined terms (not a change)
- `Reason:` statement (bold header)
- `Cost Impact (Detailed):` (bold header)
- `Justification:` (bold header)

**Filename pattern:** `proposal_{ID}_{cdpaccess_numeric_id}.docx`
- Example: `proposal_REPC35-25_1770667041.docx`
- The numeric suffix is the cdpACCESS internal ID

**How to parse with python-docx:**
```python
from docx import Document

doc = Document('proposal_REPC35-25_1770667041.docx')
for para in doc.paragraphs:
    for run in para.runs:
        text = run.text
        is_addition = bool(run.underline)
        is_deletion = bool(run.font.strike)
        is_bold = bool(run.bold)
        is_italic = bool(run.italic)
        # Build HTML: <u>additions</u>, <s>deletions</s>, <b>headers</b>, <i>terms</i>
```

**Where found on disk:**
```
IECC standard/Commercial/Meetings/2027 Meetings/Consensus/{date} Meeting/Documents/Public Comments/
IECC standard/Residential/Meetings/2027 Meetings/Consensus/{date} Meeting/Documents/Public Comments/
```

**Key fact:** These `.docx` files are posted to meeting folders when the proposal is scheduled for a consensus committee meeting. They may NOT exist on disk for proposals still at subgroup level (like REPC34-25 at time of writing).

### 2. Public Comment Monograph PDF (Backup Source)

**What:** A compiled PDF of ALL public comments, published January 2025.

**Location:**
```
IECC standard/Residential/SubGroups/2027/Public Comments to the 2027 IECC Public Comment.pdf  (4.3 MB)
IECC standard/Code/2027 IECC/Public Comments to the 2027 IECC Public Comment.pdf  (same file)
```

**Contains:** Every REPC/CEPC proposal with full text, tables, reason statements. Organized sequentially by proposal number.

**How to extract:** Use `pdftotext` and search by proposal ID:
```python
import subprocess
result = subprocess.run(['pdftotext', 'monograph.pdf', '-'], capture_output=True, text=True)
text = result.stdout
idx = text.find('REPC34-25\nIECC:')  # Find the proposal header
# Extract from header to next proposal
```

**Limitation:** PDF extraction loses formatting (underline/strikethrough). The text is there but the markup isn't machine-readable. Tables also lose structure. This is a backup for content only — the `.docx` files are the primary source for formatted extraction.

### 3. Modification Documents (_MOD.docx)

**What:** Proposed modifications to a proposal's language, submitted before meetings.

**Naming conventions (inconsistent — learned from disk scan):**
- `REPC36-25_MOD[4].docx`, `REPC36-25_MOD[5].docx` — numbered mod versions
- `REPC4-25_MOD to align CZ3 with Commercial.docx` — descriptive suffix
- `REPC25_Add Group R Parking Areas to IECC-R per Board Answer_MOD Approved as Modified by SG1.docx` — long descriptive
- `RE145-24_MOD2_Add EV Ready and EV Capable.docx` — numbered with description
- `25-03-18 SG2 Modeling IECC Circulation Forms_RE119-24_Mod.pdf` — circ form with mod attached

**Where found on disk:**
```
2027_RESIDENTIAL/Residential Subgroups/{subgroup}/Meeting/          — SG meeting folders
2027_RESIDENTIAL/Residential Consensus Committee/{date}/Documentation/Modifications/
IECC standard/Residential/Meetings/2027 Meetings/Consensus/{date}/Documents/Modification/
```

**Format:** Variable. Some are just the modified code text. Some include the full circ form. Some are the complete proposal with changes marked up. Need to be parsed on a case-by-case basis.

**IMPORTANT:** `_MOD.docx` files are NOT circ forms. They don't contain votes, recommendations, or dates. They contain the proposed modified code language only.

### 4. PNNL Analysis Reports (Supporting)

**What:** Technical analysis from Pacific Northwest National Laboratory (PNNL) supporting credit value calculations for TABLE R408.2.

**Example:** `PNNL response to requests for analysis for REPC33-34-49.docx`

**Contains:** Engineering analysis, COP calculations, EnergyPlus modeling results, and revised credit values. These inform modifications — the subgroup uses PNNL's numbers to decide what the new credit values should be.

**Not machine-parseable in a general way** — each report is unique technical content.

---

## Traced Example: REPC34-25

### Proposal Metadata (from DB)
| Field | Value |
|-------|-------|
| canonical_id | REPC34-25 |
| proponent | Heikkinen, Gary |
| code_section | TABLE R408.2 CREDITS FOR ADDITIONAL ENERGY EFFICIENCY |
| cdpaccess_id | 2665 |
| cdpaccess_url | https://energy.cdpaccess.com/proposal/2665/ |
| track | residential |
| current_subgroup | Modeling (SG2) |
| status | Pending (no SG action yet) |

### What the Proposal Does
Modifies TABLE R408.2 credit values for gas-fired heat pumps (rows RH01.14 and RH01.15). Marks several Climate Zone 6-8 values as "TBD" because PNNL acknowledged their EnergyPlus models had issues with gas-fired heat pump objects.

### Document Chain
1. **Proposal text:** In the Public Comment Monograph PDF (pages ~293-294). Also on cdpACCESS (requires login). No `.docx` on disk yet — hasn't been posted for consensus.
2. **Supporting analysis:** PNNL report in `Modeling Subgroup/26-03-03 Meeting/` folder. Reveals AFUE vs COP conversion issues and provides recalculated credit values.
3. **Upcoming meeting:** On the 3/3/2026 SG2 agenda as item (h), with note "Please see PNNL Credit Review Report."
4. **Expected outcome:** Subgroup will likely approve as modified with PNNL's recalculated credit values. A modification document may be submitted before the meeting, or the modification may be worked out live during the meeting using PNNL's numbers.

### What the Portal Would Need to Show
For a chair running the 3/3 meeting on REPC34-25:
- **The current TABLE R408.2** with all credit rows visible
- **The proposed changes** (TBD values for gas-fired heat pump rows)
- **The PNNL analysis** or at minimum the recalculated values
- **A way to capture the modification** — which cells change, to what values
- **The final table flowing into the circ form** after the vote

---

## Extraction Pipeline (Proposed)

### Phase 1: cdpACCESS DOCX Ingestion (Best Case)

For proposals that have `.docx` files on disk:

1. **Find the file:** Match `proposal_{canonical_id}_{cdp_id}.docx` in meeting `Public Comments/` folders
2. **Parse with python-docx:** Extract paragraphs and runs with formatting flags
3. **Convert to HTML:** Map run formatting to HTML tags:
   - `run.underline` → `<u>text</u>` (or `<ins>text</ins>`)
   - `run.font.strike` → `<s>text</s>` (or `<del>text</del>`)
   - `run.bold` → `<b>text</b>`
   - `run.italic` → `<i>text</i>`
4. **Extract sections:** Split into structured fields:
   - `proposal_text_html` — the code section with markup
   - `reason` — the reason statement
   - `cost_impact` — the cost impact statement
5. **Store:** New DB table or column on `proposals` table

### Phase 2: Monograph PDF Fallback

For proposals without `.docx` files:

1. **Extract text from monograph:** `pdftotext` → find proposal by ID
2. **Store as plain text** (no formatting available from PDF)
3. **Flag for manual review** — formatting will need to be added when the `.docx` becomes available

### Phase 3: Modification Ingestion

1. **Scan meeting folders** for `_MOD` files matching proposal IDs
2. **Parse with python-docx** (same run-formatting extraction)
3. **Link to proposal** via proposal_uid
4. **Store as HTML** in a new `modifications` table or in `modification_text` on staging

---

## File Location Reference

### Where to Find Each Document Type

| Document | Path Pattern | Format |
|----------|-------------|--------|
| cdpACCESS proposal docs | `IECC standard/{track}/Meetings/2027 Meetings/Consensus/{date}/Documents/Public Comments/proposal_{ID}_{cdp_id}.docx` | DOCX |
| Public Comment Monograph | `IECC standard/Code/2027 IECC/Public Comments to the 2027 IECC Public Comment.pdf` | PDF |
| Residential Monograph (copy) | `IECC standard/Residential/SubGroups/2027/Public Comments to the 2027 IECC Public Comment.pdf` | PDF |
| Modification documents | `2027_RESIDENTIAL/Residential Subgroups/{subgroup}/{date} Meeting/*_MOD*.docx` | DOCX |
| Modification documents (consensus) | `2027_RESIDENTIAL/Residential Consensus Committee/{date}/Documentation/Modifications/` | DOCX |
| Circ forms (SG) | `2027_RESIDENTIAL/Residential Subgroups/{subgroup}/{date} Meeting/{date} {SG} IECC Circulation Forms_{ID}.pdf` | PDF |
| Circ forms (consensus) | `IECC standard/{track}/Meetings/2027 Meetings/Consensus/{date}/Documents/Circulation Forms/{subgroup}/` | PDF |
| PNNL analysis | `2027_RESIDENTIAL/Residential Subgroups/{subgroup}/{date} Meeting/PNNL*.docx` | DOCX |
| Meeting agendas | `2027_RESIDENTIAL/Residential Subgroups/{subgroup}/{date} Meeting/*Agenda*.pdf` | PDF |
| PCD (base code text) | `IECC standard/Residential/Resources/2025 Public Comment Draft for the 2027 International Energy Conservation Code.pdf` | PDF |
| Circ form template | `IECC standard/Forms (Administrative)/YY-M-D (SG Name) IECC Circulation Forms.docx` | DOCX |

### Key Observations
- Commercial and Residential use identical document formats (same cdpACCESS export)
- The `IECC standard/` folder mirrors much of `2027_RESIDENTIAL/` and `ARCHIVES/` but is the canonical SharePoint-synced location
- Proposal `.docx` files appear in consensus meeting folders when scheduled for hearing — they may not exist for proposals still at subgroup level
- Modification document naming is inconsistent — must search by proposal ID pattern, not exact filename

---

## Next Steps

1. **Build the python-docx parser** — extract proposal language with HTML formatting from `.docx` files
2. **Add a `proposal_language` column** (or table) to store the extracted HTML
3. **Wire the portal** to display proposal language in the meeting view, pre-loaded into the Quill editor for modifications
4. **Build a file scanner** that finds proposal docs and mod docs by matching filenames to DB proposal IDs
5. **Test with REPC34-25** once its `.docx` appears (after it goes to consensus), or test with REPC35-25 which already has a `.docx` on disk

### Immediate Test Candidate
**REPC35-25** (Schmidt, Amy — TABLE R408.2) has a `.docx` on disk at:
```
IECC standard/Residential/Meetings/2027 Meetings/Consensus/26-02-10 Meeting/Documents/Public Comments/proposal_REPC35-25_1770667041.docx
```
This is the same TABLE R408.2 as REPC34-25, making it a perfect test case for the extraction pipeline.
