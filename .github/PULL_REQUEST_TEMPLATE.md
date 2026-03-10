## Summary

Brief description of what this PR does and why.

## Changes

-

## Testing Checklist

Verify these after making changes (see [web/DEVELOPMENT.md](web/DEVELOPMENT.md) for details):

### Auth & Navigation
- [ ] `/login` shows user selection, both roles visible
- [ ] Chair login (brian.shanks) → `/home` with sorted meetings
- [ ] Chair navigating to `/` → redirects to `/home`
- [ ] Secretariat login (alex.smith) → `/` dashboard
- [ ] Secretariat navigating to `/home` → redirects to `/`

### Chair Portal
- [ ] "Open Portal" loads with correct proposals for the chair's subgroup
- [ ] Action staging — recommendation → accordion collapses, progress bar updates
- [ ] Inline edit — Edit button → form with previous values pre-filled
- [ ] "Review & Finalize" → staged actions, breadcrumbs, partial-completion warning

### Secretariat Portal
- [ ] Dashboard — in-progress meetings, vote counts in recent actions
- [ ] Proposals — subgroup dropdown, live search with debounce
- [ ] Meetings — delete button, notes tooltip, phase formatting
- [ ] Portal from secretariat — `/meeting/{id}/portal` works with secretariat nav

### Go Live & Documents
- [ ] Go Live — big text, vote counters, auto-advance, keyboard nav
- [ ] Document upload — upload PDF → appears in Go Live viewer
- [ ] Go Live staging — card collapses, progress updates, auto-advances

### Pipeline
- [ ] Complete meeting as chair → circ form auto-generated
- [ ] Sign in as secretariat → circ form on dashboard → Preview/Approve/Reject
- [ ] Document exports — download .docx files

## Database Impact

- [ ] No schema changes
- [ ] Schema changes (describe below)
- [ ] WAL checkpoint included after DB writes

## Screenshots

If UI changes, include before/after screenshots.
