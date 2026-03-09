# IECC 2027 Secretariat — Proposal Tracking System

**510 proposals in a unified SQLite database (`iecc.db`) — 263 commercial + 247 residential**

New agents: follow the Mandatory First Step in `CLAUDE.md`. That file drives the onboarding sequence.

## Documentation Index

### Database & CLI Tools
| Document | Purpose |
|----------|---------|
| `CLAUDE.md` | **START HERE** — Hard rules, lessons learned, session protocol |
| `AGENT_GUIDE.md` | Full schema, naming traps, queries, verification protocol |
| `PROJECT_MEMORY.md` | Session history, decisions, known issues |
| `IECC_STATUS_REPORT.md` | Human-readable status summary |
| `QUERY_COOKBOOK.md` | Ready-to-use SQL queries |

### Web Application (`web/`)
| Document | Purpose |
|----------|---------|
| `web/LLM_HANDOFF.md` | **START HERE FOR WEB WORK** — what to read, critical rules, what to build next |
| `web/README.md` | Project overview, setup, file structure, tech stack |
| `web/ARCHITECTURE.md` | Request lifecycle, auth system, templates, DB tables, HTMX patterns |
| `web/DEVELOPMENT.md` | Current state, what's built, what's NOT built, gotchas, code patterns |

## Quick Start — Web App

```
cd web
start.bat          # Windows (double-click)
```
Opens at **http://localhost:8080**. Two portals: secretariat (admin) and subgroup chairs (meeting management). See `web/LLM_HANDOFF.md` for full details.
