# Architecture Reference

## Request Lifecycle

```
Browser Request
    ↓
auth_middleware (main.py)
    → Is path public (/login, /health, /static)? → Pass through
    → Has valid cookie? No → Redirect to /login
    → Is secretariat page + user is chair? → Redirect to /home
    → Is /home + user is secretariat? → Redirect to /
    → Set request.state.user → Continue
    ↓
Route Handler (routes/*.py)
    → Uses render(request, template, context) from helpers.py
    → render() auto-injects: user, base_template (chair_base or base)
    ↓
Jinja2 Template
    → {% extends base_template %} picks correct layout
    → User info displayed in navbar from {{ user }}
    ↓
HTML Response
```

## Authentication System

### How It Works
1. **Login page** (`/login`) — standalone HTML, not extending any base template
2. User selects their name from radio buttons grouped by role
3. POST to `/login` sets cookie `icc_user` with the user ID (e.g., "brian.shanks")
4. Cookie lasts 7 days (`max_age=86400*7`)
5. Middleware reads cookie on every request, attaches user dict to `request.state.user`
6. `render()` helper passes user to every template automatically

### User Dict Structure
```python
{
    "user_id": "brian.shanks",
    "name": "Brian Shanks",
    "role": "chair",           # "chair" or "secretariat"
    "title": "SG2 Chair — Modeling and Whole Building Metrics",
    "body": "Residential Modeling Subgroup",   # None for secretariat
    "track": "residential",                     # None for secretariat
}
```

### Route Access Matrix
| Route Pattern | Secretariat | Chair | No Login |
|---------------|-------------|-------|----------|
| `/login` | Yes | Yes | Yes |
| `/health` | Yes | Yes | Yes |
| `/` (dashboard) | Yes | **Blocked → /home** | **→ /login** |
| `/proposals*` | Yes | **Blocked → /home** | **→ /login** |
| `/meetings*` | Yes | **Blocked → /home** | **→ /login** |
| `/home` | **Blocked → /** | Yes | **→ /login** |
| `/meeting/*/portal` | Yes | Yes | **→ /login** |
| `/meeting/*/review` | Yes | Yes | **→ /login** |
| `/meeting/*/export-*` | Yes | Yes | **→ /login** |
| `/meeting/*/stage` | Yes | Yes | **→ /login** |

## Template Inheritance

Two separate base templates — chairs and secretariat never share nav:

```
login.html (standalone — no base)

base.html (SECRETARIAT)
├── dashboard.html
├── proposal_list.html
├── proposal_detail.html
├── meetings.html
├── meeting_detail.html
├── meeting_portal.html    ← uses base_template variable
└── meeting_review.html    ← uses base_template variable

chair_base.html (CHAIRS)
├── chair_home.html
├── meeting_portal.html    ← uses base_template variable
└── meeting_review.html    ← uses base_template variable
```

**Portal and review templates** use `{% extends base_template|default("base.html") %}` so they adapt to whoever is logged in. The `render()` helper sets `base_template` based on user role.

## Database Tables Used by the Web App

The web app reads from the main `iecc.db` (one dir up). It does NOT create its own database — it uses the same one as the CLI tools.

### Existing Tables (read-only from web app's perspective)

> Row counts change between sessions. Query the DB for current numbers — don't trust hardcoded counts in docs.

| Table | Purpose |
|-------|---------|
| `proposals` | Master proposal records (commercial + residential) |
| `subgroup_actions` | Committed subgroup decisions |
| `consensus_actions` | Consensus committee votes |
| `data_quality_flags` | DQ issues found during audits |
| `meetings` | Meeting schedule — SCHEDULED, COMPLETED, or CANCELLED |
| `proposal_text` | Extracted code language with ICC markup |
| `modifications` | Pre-submitted modification documents |
| `proposal_links` | Cross-references between related proposals |
| `documents` | Source document registry |
| `errata` | PCD errata corrections |
| `subgroup_movements` | Proposal reassignment history |
| `governance_documents` | ICC Council Policies — commercial only |
| `governance_clauses` | Searchable governance clause text |
| `v_current_status` | VIEW — computed status per proposal |
| `v_ready_for_consensus` | VIEW — proposals with SG action but no consensus action |
| `v_full_disposition` | VIEW — flattened for reporting/export |
| `v_data_quality_review` | VIEW — DQ flags sorted by needs_review |
| `v_multi_action_proposals` | VIEW — procedural chains (Postpone → Reconsider → Final) |

### Tables Created by the Web App
| Table | Purpose | Created In |
|-------|---------|-----------|
| `sg_action_staging` | Temporary staging during a meeting | `subgroup_portal.py._ensure_tables()` |
| `meeting_agenda_items` | Agenda order for a meeting | `subgroup_portal.py._ensure_tables()` |
| `circ_forms` | Circ form document lifecycle (pending_review → approved/uploaded → rejected) | `circforms.py._ensure_circ_forms_table()` |

`sg_action_staging` and `meeting_agenda_items` are created with `CREATE TABLE IF NOT EXISTS` on first portal access. They use `UNIQUE(meeting_id, proposal_uid)` constraints.

### Staging → Commit Flow
1. Chair stages actions in `sg_action_staging` during meeting
2. Chair reviews on `/meeting/{id}/review`
3. "Send to Secretariat" copies each row to `subgroup_actions`, sets meeting status to COMPLETED, deletes staging rows
4. `source_file` column records `web_portal/{meeting_id}` for traceability

## HTMX Integration

The app uses HTMX for two key interactions:

### 1. Proposal List Filtering
`/proposals` sends HTMX requests with filter params. If `HX-Request` header present, returns partial `proposal_rows.html` instead of full page. Table body swaps via `hx-target`.

### 2. Action Staging in Portal
When a chair submits an action form in the portal:
- Form POSTs to `/meeting/{id}/stage` with `hx-post`
- Returns `action_saved.html` partial which replaces the form area
- Includes OOB (Out-of-Band) swap for the progress bar and finalize bar
- The finalize bar always updates to show current count + modification export button

### OOB Swap Pattern
```html
<!-- In action_saved.html partial -->
<div id="progress-fill-wrapper" hx-swap-oob="innerHTML">
    <div class="progress-fill" style="width: {{ pct }}%;"></div>
</div>
<div id="progress-text" hx-swap-oob="true">{{ done_count }} / {{ total }} actions recorded</div>
<div id="finalize-bar" hx-swap-oob="true">
    <!-- Updated finalize bar with remaining count + export buttons -->
</div>
```

## Word Document Generation

Documents are generated via Node.js `docx` library (not python-docx). The flow:

1. Python builds a JS script as a string with data embedded as JSON
2. Writes the script to a temp file
3. Runs `node temp_script.js` via subprocess
4. Node script outputs the .docx buffer to stdout
5. Python reads stdout bytes and returns as HTTP response

Three document types:
| Endpoint | Generator Function | Output |
|----------|-------------------|--------|
| `/meeting/{id}/export-agenda` | `generate_agenda_docx()` | Meeting agenda with proposal table |
| `/meeting/{id}/export-circform` | `generate_circform_docx()` | Circulation form with votes + recommendations |
| `/meeting/{id}/export-modifications` | `generate_modification_docx()` | Modification language for cdpACCESS entry |

## CSS Theme

Single CSS file (`static/css/main.css`). Dark theme with ICC blue accent colors:

```
--icc-blue:    #1B3A5C  (navbar, portal header)
--icc-light:   #2E75B6  (links, accents)
--icc-accent:  #D5E8F0  (light text on dark)
--bg-dark:     #0f1419  (page background)
--bg-card:     #1a2332  (card background)
--bg-input:    #1e2a3a  (form inputs)
```

Status badges use semantic colors: green (decided/success), amber (pending/warning), red (danger), gray (withdrawn/closed). Track badges: blue for commercial, green for residential.
