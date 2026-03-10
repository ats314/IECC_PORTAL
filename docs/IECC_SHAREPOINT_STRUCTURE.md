# IECC SharePoint Folder Structure — Residential (RECDC)

> **Reviewed:** 2026-03-05
> **Location:** `ICC-CS_AE TECHNICAL SERVICES GROUP / Shared Documents / Committees / Cmtes-Public / Codes / Energy / Residential (RECDC) / Meeting Minutes & Agendas / 2027 IECC /`
> **Primary contributors:** Jason Toves, Alex Smith

---

## Top-Level Structure

```
2027 IECC/
├── Residential Consensus Committee/     ← 24 meeting folders + "Previous Meetings"
└── Residential Subgroups/               ← 7 subgroup folders
    ├── Admin Subgroup
    ├── Cost Effectiveness
    ├── Envelope and Embodied Carbon Subgroup
    ├── HVAC & Water Heating
    ├── Modeling Subgroup
    ├── Residential EPLR
    └── Residential Existing Buildings
```

---

## Residential Consensus Committee

24 meeting folders spanning 2024-12-17 through 2026-03-12, plus a "Previous Meetings" archive folder.

### Folder Naming Convention
`YY-MM-DD Meeting` (e.g., `26-01-20 Meeting`)

### Meeting Folder Contents (varies significantly)

**Example: 26-01-20 Meeting** (well-populated)
```
26-01-20 Meeting/
├── 26-01-20 IECC Residential Consensus Committee Agenda.pdf
├── IECC Residential Consensus Committee Public Meeting Preliminary Minutes (01-20-26).pdf
├── IECC Residential Consensus Committee Public Meeting Approved Minutes (01-20-26).pdf
├── Admin/                          ← circ forms by subgroup name
├── Envelope/
├── EPLR/
├── Existing Building/
└── Modeling/
```

**Example: 26-02-10 Meeting** (different organization)
```
26-02-10 Meeting/
├── 26-02-10 IECC Residential Consensus Committee Agenda.pdf
├── 26-02-10 IECC Residential Consensus Committee Agenda v2.0.pdf
├── IECC Residential Consensus Committee Public Meeting Preliminary Minutes (02-10-26).pdf
├── IECC Residential Consensus Committee Public Meeting Approved Minutes (02-10-26).pdf
└── Documents/
    ├── Circulation Forms/          ← circ forms nested under Documents
    │   ├── Admin/
    │   ├── Envelope/
    │   ├── EPLR/
    │   ├── Existing Building/
    │   └── Modeling/
    └── Public Comments/
```

**Example: 26-02-25 Meeting** — EMPTY folder (no files posted)

**Example: 26-03-12 Meeting** — Single agenda docx only (upcoming meeting)

### Circulation Form File Naming
`26-01-13 SG2 Modeling IECC Circulation Forms_REPC29-25.pdf`
Pattern: `{date} {SG#} {subgroup name} IECC Circulation Forms_{proposal ID}.pdf`

### Agenda File Naming
`26-01-20 IECC Residential Consensus Committee Agenda.pdf`
Pattern: `{date} IECC Residential Consensus Committee Agenda.pdf`

### Minutes File Naming
- Preliminary: `IECC Residential Consensus Committee Public Meeting Preliminary Minutes ({date}).pdf`
- Approved: `IECC Residential Consensus Committee Public Meeting Approved Minutes ({date}).pdf`
(Date format in filename: `MM-DD-YY`)

---

## Residential Subgroups

### Admin Subgroup (12 meeting folders)
- Date range: 25-02-12 through 26-02-12
- All created by Jason Toves, recent ones by Alex Smith
- Note: `26-02-12 Meeeting` has typo in folder name (triple 'e')
- No loose files

### Cost Effectiveness (4 meeting folders)
- Date range: 25-04-03 through 25-07-17
- `25-07-17` folder missing "Meeting" suffix — naming inconsistency
- Only 4 meetings total, last one July 2025 — appears inactive

### Envelope and Embodied Carbon Subgroup (15 meeting folders + loose files)
- Date range: 25-02-05 through 26-03-04
- Loose files mixed with meeting folders:
  - `25-01-28 Residential Public Meeting Minutes - Tentatived.pdf` (consensus committee minutes in wrong folder?)
  - Multiple modification PDFs: `49 CE49-24 Part III-WESTON-MP1 mod-71.pdf`, `RE39-24-DUFFY-MP2 mod-144.pdf`, etc.
  - Naming pattern for mods varies wildly

### HVAC & Water Heating (14 meeting folders + loose files)
- Date range: 25-02-13 through 26-02-23
- Loose files:
  - `2027 IECC HVAC Subgroup Roster May_2025.xlsx`
  - Multiple floor mod PDFs: `floor mod RE 114-24.pdf`, `floor mod RE71-24.pdf`
  - `Mod R408(2101).pdf`, `Mod RE126-24.pdf`

### Modeling Subgroup (14 meeting folders + loose files)
- Date range: 25-02-04 through 26-03-03
- Loose files: RE proposal PDFs, modification docs, `Source Multipliers.xlsx`
- Meeting folder example (26-03-03): agenda PDF + PNNL analysis docx

### Residential EPLR (9 meeting folders + loose file)
- Date range: 25-02-03 through 26-02-24
- 1 loose EPLR proposal docx

### Residential Existing Buildings (10 meeting folders + 1 subfolder)
- Date range: 25-02-18 through 26-02-12
- `Proposals` subfolder (contains proposal documents)

---

## Cross-Reference: SharePoint vs Database

### Subgroup Name Mapping (SharePoint → DB)

| SharePoint Folder Name | DB `current_subgroup` | DB Meeting `body` | Proposals |
|---|---|---|---|
| Admin Subgroup | Consistency and Administration (SG1) | Residential Administration Subgroup | 47 |
| Cost Effectiveness | *(no proposals assigned)* | *(no meetings in DB)* | 0 |
| Envelope and Embodied Carbon Subgroup | Envelope (SG4) | Residential Envelope Subgroup | 42 |
| HVAC & Water Heating | HVACR (SG6) | Residential HVAC Subgroup | 51 |
| Modeling Subgroup | Modeling (SG2) | Residential Modeling Subgroup | 31 |
| Residential EPLR | EPLR (SG3) | Residential EPLR Subgroup | 29 |
| Residential Existing Buildings | Existing Buildings (SG5) | Residential Existing Building Subgroup | 16 |

**Key observation:** Three different naming systems exist for the same subgroups — the SharePoint folder name, the proposal `current_subgroup` value, and the meeting `body` value. The portal's `BODY_TO_SUBGROUP` mapping bridges body→subgroup for agenda auto-populate.

### Meeting Count Comparison

| Body | SharePoint Folders | DB Meetings | Gap |
|---|---|---|---|
| Consensus Committee | 24 + Previous | 22 | SP has ~2 extra (possibly in "Previous" or pre-cycle) |
| Admin (SG1) | 12 | 2 scheduled + 3 completed (as "Consistency and Administration") | **Major gap** — 12 on SP, only 5 in DB |
| Cost Effectiveness | 4 | 0 | Not in DB at all |
| Envelope (SG4) | 15 | 4 scheduled | **Major gap** — 15 on SP, only 4 in DB |
| HVAC (SG6) | 14 | 3 scheduled | **Major gap** — 14 on SP, only 3 in DB |
| Modeling (SG2) | 14 | 4 | **Major gap** — 14 on SP, only 4 in DB |
| EPLR (SG3) | 9 | 5 scheduled | Gap — 9 on SP, 5 in DB |
| Existing Buildings (SG5) | 10 | 4 scheduled | Gap — 10 on SP, 4 in DB |

**The DB is missing most historical subgroup meetings from the 2025 Code Proposal phase.** The DB only has future scheduled meetings (Public Comment phase) for most subgroups, plus a few Consensus Committee meetings. SharePoint has the complete history going back to Feb 2025.

---

## Inconsistencies Found

### 1. Circ Form Organization (Critical)
Two different filing patterns exist for consensus committee meetings:
- **Pattern A** (26-01-20): Circ form subfolders directly in the meeting folder (`Admin/`, `Modeling/`, etc.)
- **Pattern B** (26-02-10): Circ forms nested under `Documents/Circulation Forms/{subgroup}/`

This inconsistency means anyone looking for circ forms has to check two different locations depending on the meeting.

### 2. Folder Naming Inconsistencies
- `26-02-12 Meeeting` — typo (triple 'e') in Admin Subgroup
- `25-07-17` — missing "Meeting" suffix in Cost Effectiveness
- Subgroup names don't match between folders, DB proposals, and DB meetings (three naming systems)

### 3. Loose Files in Subgroup Folders
Multiple subgroups have modification PDFs, proposal documents, rosters, and other reference materials dumped at the root level alongside meeting folders. This makes it hard to find meeting-specific documents vs. reference materials. Affected subgroups: Envelope, HVAC, Modeling, EPLR, Existing Buildings.

### 4. Inconsistent File Naming for Modifications
- `floor mod RE 114-24.pdf` (HVAC)
- `Mod R408(2101).pdf` (HVAC)
- `49 CE49-24 Part III-WESTON-MP1 mod-71.pdf` (Envelope)
- `RE39-24-DUFFY-MP2 mod-144.pdf` (Envelope)

No standard naming convention is followed across subgroups.

### 5. Empty/Incomplete Meeting Folders
Some consensus committee meeting folders exist but are empty (e.g., 26-02-25). This could mean the meeting was cancelled, or documents haven't been posted yet.

### 6. Minutes in Wrong Folder
`25-01-28 Residential Public Meeting Minutes - Tentatived.pdf` appears in the Envelope subgroup folder, but it's a residential consensus committee document based on the name.

### 7. Multiple Agenda Versions Without Clear Superseding
26-02-10 has both an original agenda and `v2.0` — no indication of which is current without opening both.

---

## Suggestions for Portal Integration

### What the portal already solves:
1. **Circ form chaos** — The portal generates standardized circ forms from structured data. No more inconsistent filing by multiple people.
2. **Action tracking** — Instead of chairs sending circ forms whenever they get around to it, actions are recorded in real-time during meetings.
3. **Naming consistency** — The portal uses canonical proposal IDs and standardized recommendation values.

### What the portal could additionally address:

1. **Auto-generate agenda PDFs** — The portal already has agenda export (Word). Could post directly to SharePoint via Graph API in the future.

2. **Meeting folder scaffolding** — When a meeting is created in the portal, auto-create the SharePoint folder with the correct `YY-MM-DD Meeting` naming convention and standard subfolders.

3. **Circ form auto-filing** — When "Send to Secretariat" is clicked, auto-upload the circ form Word doc to the correct SharePoint meeting folder under the correct subgroup subfolder.

4. **Historical meeting import** — The DB is missing most 2025 subgroup meetings. These could be backfilled from SharePoint folder dates to build a complete meeting history.

5. **Reference doc organization** — Loose files in subgroup folders (modifications, rosters, proposals) could be organized into standard subfolders like `Reference Documents/` or `Modifications/`.

---

## SharePoint URL Pattern

Base URL: `https://2023701800.sharepoint.com/sites/ICC-CS_AETECHNICALSERVICESGROUP/Shared%20Documents/Forms/AllItems.aspx`

Folder navigation uses the `id` query parameter with URL-encoded paths:
```
?id=/sites/ICC-CS_AETECHNICALSERVICESGROUP/Shared Documents/Committees/Cmtes-Public/Codes/Energy/Residential (RECDC)/Meeting Minutes & Agendas/2027 IECC/{path}
&viewid=7ea8890f-d6ff-4285-8504-9d85daa994f7
&p=true
```
