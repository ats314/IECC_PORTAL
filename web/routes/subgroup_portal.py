"""Subgroup Chair Meeting Portal — the core feature.

WORKFLOW:
1. Chair opens /meeting/{id}/portal
2. Agenda auto-populates with all pending proposals for their subgroup
   OR chair manually adds/removes proposals
3. Chair can drag-and-drop to reorder the agenda
4. Chair exports agenda as Word doc for pre-meeting distribution
5. During the meeting, chair enters actions proposal-by-proposal (staged)
6. Chair clicks "Review & Finalize" to see summary
7. "Send to Secretariat" commits data to subgroup_actions, marks meeting COMPLETED
"""
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from db.connection import get_db, checkpoint
from db import queries
import config
import json
import logging
from routes.helpers import render

logger = logging.getLogger(__name__)

router = APIRouter()


def _ensure_tables(conn):
    """Create staging and agenda tables if they don't exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sg_action_staging (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id INTEGER NOT NULL,
            proposal_uid TEXT NOT NULL,
            canonical_id TEXT NOT NULL,
            subgroup TEXT NOT NULL,
            action_date TEXT NOT NULL,
            recommendation TEXT NOT NULL,
            vote_for INTEGER,
            vote_against INTEGER,
            vote_not_voting INTEGER,
            reason TEXT,
            modification_text TEXT,
            moved_by TEXT,
            seconded_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(meeting_id, proposal_uid)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS meeting_agenda_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id INTEGER NOT NULL,
            proposal_uid TEXT NOT NULL,
            sort_order INTEGER NOT NULL DEFAULT 0,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(meeting_id, proposal_uid),
            FOREIGN KEY (meeting_id) REFERENCES meetings(id),
            FOREIGN KEY (proposal_uid) REFERENCES proposals(proposal_uid)
        )
    """)


def _get_meeting(conn, meeting_id):
    meeting = conn.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,)).fetchone()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return dict(meeting)


# ==================== PORTAL MAIN VIEW ====================

@router.get("/meeting/{meeting_id}/portal")
async def meeting_portal(request: Request, meeting_id: int):
    """Render the chair's meeting portal with agenda and action entry."""
    with get_db() as conn:
        _ensure_tables(conn)
        meeting = _get_meeting(conn, meeting_id)

        # Get agenda items
        agenda = [dict(r) for r in conn.execute(queries.AGENDA_ITEMS, (meeting_id,)).fetchall()]

        # Resolve meeting body to proposal subgroup name
        subgroup_name = config.resolve_subgroup(meeting["body"])

        # Get available proposals NOT on agenda
        available = [dict(r) for r in conn.execute(
            queries.AVAILABLE_FOR_AGENDA, (meeting["track"], subgroup_name, meeting_id)
        ).fetchall()]

        # Get staged actions for this meeting
        staged = {}
        for row in conn.execute(
            "SELECT * FROM sg_action_staging WHERE meeting_id = ?", (meeting_id,)
        ).fetchall():
            staged[row["proposal_uid"]] = dict(row)

        # Load proposal text, modifications, and cross-references for all agenda items
        proposal_content = {}
        proposal_mods = {}
        proposal_links_map = {}

        if agenda:
            uids = [item["proposal_uid"] for item in agenda]
            placeholders = ",".join("?" * len(uids))

            # Proposal text (extracted code language)
            try:
                sql = queries.PROPOSAL_TEXT_FOR_MEETING.format(placeholders=placeholders)
                for row in conn.execute(sql, uids).fetchall():
                    proposal_content[row["proposal_uid"]] = dict(row)
            except Exception as e:
                logger.warning(f"Could not load proposal_text: {e}")

            # Pre-submitted modifications
            try:
                sql = queries.MODIFICATIONS_FOR_PROPOSALS.format(placeholders=placeholders)
                for row in conn.execute(sql, uids).fetchall():
                    uid = row["proposal_uid"]
                    if uid not in proposal_mods:
                        proposal_mods[uid] = []
                    proposal_mods[uid].append(dict(row))
            except Exception as e:
                logger.warning(f"Could not load modifications: {e}")

            # Cross-references
            try:
                sql = queries.PROPOSAL_LINKS_FOR_PROPOSALS.format(placeholders=placeholders)
                for row in conn.execute(sql, uids + uids).fetchall():
                    row = dict(row)
                    for uid in uids:
                        if row["proposal_uid_a"] == uid or row["proposal_uid_b"] == uid:
                            if uid not in proposal_links_map:
                                proposal_links_map[uid] = []
                            # Show the OTHER proposal's canonical_id
                            other_id = row["canonical_b"] if row["proposal_uid_a"] == uid else row["canonical_a"]
                            proposal_links_map[uid].append({
                                "canonical_id": other_id,
                                "link_type": row["link_type"],
                                "notes": row["notes"],
                            })
            except Exception as e:
                logger.warning(f"Could not load proposal_links: {e}")

        # Annotate agenda items with staged actions and content
        for item in agenda:
            item["staged_action"] = staged.get(item["proposal_uid"])
            item["content"] = proposal_content.get(item["proposal_uid"])
            item["modifications"] = proposal_mods.get(item["proposal_uid"], [])
            item["links"] = proposal_links_map.get(item["proposal_uid"], [])

        done_count = sum(1 for a in agenda if a["staged_action"])
        has_modifications = any(
            a["staged_action"] and "Modified" in (a["staged_action"].get("recommendation") or "")
            for a in agenda if a.get("staged_action")
        )
        is_completed = meeting.get("status") == "COMPLETED"

        # For completed meetings, fetch committed actions
        committed_actions = []
        if is_completed:
            committed_actions = [dict(r) for r in conn.execute(
                """SELECT sa.*, p.canonical_id, p.code_section
                   FROM subgroup_actions sa
                   JOIN proposals p ON sa.proposal_uid = p.proposal_uid
                   WHERE sa.source_file = ?
                   ORDER BY p.canonical_id""",
                (f"web_portal/{meeting_id}",)
            ).fetchall()]

    # Load subgroup members for moved_by/seconded_by dropdowns
    with get_db() as conn:
        members = [dict(r) for r in conn.execute(
            "SELECT display_name FROM subgroup_members WHERE body = ? ORDER BY last_name, first_name",
            (meeting["body"],)
        ).fetchall()]

    return render(request, "meeting_portal.html", {
        "meeting": meeting,
        "agenda": agenda,
        "available": available,
        "total": len(agenda),
        "done_count": done_count,
        "recommendations": config.RECOMMENDATIONS,
        "is_completed": is_completed,
        "has_modifications": has_modifications,
        "committed_actions": committed_actions,
        "members": members,
    })


# ==================== AGENDA MANAGEMENT ====================

@router.post("/meeting/{meeting_id}/agenda/auto-populate")
async def auto_populate_agenda(request: Request, meeting_id: int):
    """Auto-populate agenda with all pending proposals for the subgroup."""
    with get_db() as conn:
        _ensure_tables(conn)
        meeting = _get_meeting(conn, meeting_id)
        subgroup_name = config.resolve_subgroup(meeting["body"])
        conn.execute(queries.AUTO_POPULATE_AGENDA, (meeting_id, meeting["track"], subgroup_name))
    checkpoint()
    return RedirectResponse(url=f"/meeting/{meeting_id}/portal", status_code=303)


@router.post("/meeting/{meeting_id}/agenda/add")
async def add_to_agenda(request: Request, meeting_id: int, proposal_uid: str = Form(...)):
    """Add a single proposal to the agenda."""
    with get_db() as conn:
        _ensure_tables(conn)
        # Get max sort order
        row = conn.execute(
            "SELECT COALESCE(MAX(sort_order), 0) + 10 as next_order FROM meeting_agenda_items WHERE meeting_id = ?",
            (meeting_id,)
        ).fetchone()
        conn.execute(queries.INSERT_AGENDA_ITEM, (meeting_id, proposal_uid, row["next_order"]))
    checkpoint()
    return RedirectResponse(url=f"/meeting/{meeting_id}/portal", status_code=303)


@router.post("/meeting/{meeting_id}/agenda/remove")
async def remove_from_agenda(request: Request, meeting_id: int, proposal_uid: str = Form(...)):
    """Remove a proposal from the agenda."""
    with get_db() as conn:
        _ensure_tables(conn)
        # Also remove any staged action for this proposal
        conn.execute("DELETE FROM sg_action_staging WHERE meeting_id = ? AND proposal_uid = ?",
                     (meeting_id, proposal_uid))
        conn.execute(queries.DELETE_AGENDA_ITEM, (meeting_id, proposal_uid))
    checkpoint()
    return RedirectResponse(url=f"/meeting/{meeting_id}/portal", status_code=303)


@router.post("/meeting/{meeting_id}/agenda/reorder")
async def reorder_agenda(request: Request, meeting_id: int):
    """Reorder agenda items. Expects JSON body: {order: [proposal_uid, ...]}"""
    body = await request.json()
    order = body.get("order", [])

    with get_db() as conn:
        _ensure_tables(conn)
        for i, uid in enumerate(order):
            conn.execute(queries.UPDATE_AGENDA_ORDER, ((i + 1) * 10, meeting_id, uid))
    checkpoint()
    return JSONResponse({"status": "ok", "count": len(order)})


@router.post("/meeting/{meeting_id}/agenda/clear")
async def clear_agenda(request: Request, meeting_id: int):
    """Remove all items from agenda."""
    with get_db() as conn:
        _ensure_tables(conn)
        conn.execute("DELETE FROM meeting_agenda_items WHERE meeting_id = ?", (meeting_id,))
        conn.execute("DELETE FROM sg_action_staging WHERE meeting_id = ?", (meeting_id,))
    checkpoint()
    return RedirectResponse(url=f"/meeting/{meeting_id}/portal", status_code=303)


# ==================== ACTION STAGING ====================

@router.post("/meeting/{meeting_id}/stage")
async def stage_action(
    request: Request,
    meeting_id: int,
    canonical_id: str = Form(...),
    recommendation: str = Form(...),
    vote_for: int = Form(None),
    vote_against: int = Form(None),
    vote_not_voting: int = Form(None),
    reason: str = Form(""),
    modification_text: str = Form(""),
    moved_by: str = Form(""),
    seconded_by: str = Form(""),
):
    """Stage a subgroup action (NOT committed to main DB yet)."""
    with get_db() as conn:
        _ensure_tables(conn)
        meeting = _get_meeting(conn, meeting_id)

        prop = conn.execute(queries.PROPOSAL_UID_BY_CANONICAL, (canonical_id,)).fetchone()
        if not prop:
            raise HTTPException(status_code=404, detail=f"Proposal {canonical_id} not found")
        proposal_uid = prop["proposal_uid"]

        # Validate
        errors = []
        if "Modified" in recommendation and not modification_text.strip():
            errors.append("Modification text is required for 'Approved as Modified' recommendations.")
        if recommendation not in config.RECOMMENDATIONS:
            errors.append(f"Invalid recommendation: {recommendation}")

        if errors:
            templates = request.app.state.templates
            return templates.TemplateResponse("partials/action_error.html", {
                "request": request, "errors": errors, "canonical_id": canonical_id,
            })

        conn.execute("""
            INSERT INTO sg_action_staging
                (meeting_id, proposal_uid, canonical_id, subgroup, action_date,
                 recommendation, vote_for, vote_against, vote_not_voting,
                 reason, modification_text, moved_by, seconded_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(meeting_id, proposal_uid) DO UPDATE SET
                recommendation = excluded.recommendation,
                vote_for = excluded.vote_for,
                vote_against = excluded.vote_against,
                vote_not_voting = excluded.vote_not_voting,
                reason = excluded.reason,
                modification_text = excluded.modification_text,
                moved_by = excluded.moved_by,
                seconded_by = excluded.seconded_by
        """, (
            meeting_id, proposal_uid, canonical_id,
            meeting["body"], meeting["meeting_date"],
            recommendation,
            vote_for, vote_against, vote_not_voting,
            reason.strip() or None,
            modification_text.strip() or None,
            moved_by.strip() or None,
            seconded_by.strip() or None,
        ))

    templates = request.app.state.templates

    with get_db() as conn:
        staged_count = conn.execute(
            "SELECT COUNT(*) as c FROM sg_action_staging WHERE meeting_id = ?", (meeting_id,)
        ).fetchone()["c"]
        agenda_count = conn.execute(
            "SELECT COUNT(*) as c FROM meeting_agenda_items WHERE meeting_id = ?", (meeting_id,)
        ).fetchone()["c"]
        mod_count = conn.execute(
            "SELECT COUNT(*) as c FROM sg_action_staging WHERE meeting_id = ? AND recommendation LIKE '%Modified%' AND modification_text IS NOT NULL",
            (meeting_id,)
        ).fetchone()["c"]

    return templates.TemplateResponse("partials/action_saved.html", {
        "request": request,
        "canonical_id": canonical_id,
        "recommendation": recommendation,
        "vote_for": vote_for,
        "vote_against": vote_against,
        "vote_not_voting": vote_not_voting,
        "moved_by": moved_by.strip() or None,
        "seconded_by": seconded_by.strip() or None,
        "done_count": staged_count,
        "total": agenda_count,
        "meeting_id": meeting_id,
        "has_modifications": mod_count > 0,
    })


@router.post("/meeting/{meeting_id}/unstage/{canonical_id}")
async def unstage_action(request: Request, meeting_id: int, canonical_id: str):
    """Remove a staged action (chair wants to redo it). Returns HTMX partial if HX-Request."""
    with get_db() as conn:
        _ensure_tables(conn)
        # Get the previous values before deleting
        prev = conn.execute(
            "SELECT * FROM sg_action_staging WHERE meeting_id = ? AND canonical_id = ?",
            (meeting_id, canonical_id)
        ).fetchone()
        prev = dict(prev) if prev else {}

        conn.execute(
            "DELETE FROM sg_action_staging WHERE meeting_id = ? AND canonical_id = ?",
            (meeting_id, canonical_id)
        )

        # If HTMX request, return inline form partial
        if request.headers.get("HX-Request"):
            # Get proposal details
            prop = conn.execute(
                "SELECT p.* FROM proposals p WHERE p.canonical_id = ?", (canonical_id,)
            ).fetchone()
            prop = dict(prop) if prop else {}

            # Load proposal content for pre-loading Quill
            content = None
            if prop.get("proposal_uid"):
                try:
                    content_row = conn.execute(
                        queries.PROPOSAL_TEXT_BY_UID, (prop["proposal_uid"],)
                    ).fetchone()
                    content = dict(content_row) if content_row else None
                except Exception:
                    pass

            staged_count = conn.execute(
                "SELECT COUNT(*) as c FROM sg_action_staging WHERE meeting_id = ?", (meeting_id,)
            ).fetchone()["c"]
            agenda_count = conn.execute(
                "SELECT COUNT(*) as c FROM meeting_agenda_items WHERE meeting_id = ?", (meeting_id,)
            ).fetchone()["c"]

            # Load members for dropdowns
            meeting = _get_meeting(conn, meeting_id)
            members = [dict(r) for r in conn.execute(
                "SELECT display_name FROM subgroup_members WHERE body = ? ORDER BY last_name, first_name",
                (meeting["body"],)
            ).fetchall()]

            templates = request.app.state.templates
            return templates.TemplateResponse("partials/action_unstaged.html", {
                "request": request,
                "meeting_id": meeting_id,
                "canonical_id": canonical_id,
                "code_section": prop.get("code_section", ""),
                "proponent": prop.get("proponent", ""),
                "cdpaccess_url": prop.get("cdpaccess_url", ""),
                "recommendations": config.RECOMMENDATIONS,
                "prev_recommendation": prev.get("recommendation", ""),
                "prev_vote_for": prev.get("vote_for"),
                "prev_vote_against": prev.get("vote_against"),
                "prev_vote_not_voting": prev.get("vote_not_voting"),
                "prev_reason": prev.get("reason", ""),
                "prev_modification_text": prev.get("modification_text", ""),
                "prev_moved_by": prev.get("moved_by", ""),
                "prev_seconded_by": prev.get("seconded_by", ""),
                "done_count": staged_count,
                "total": agenda_count,
                "content": content,
                "members": members,
            })

    return RedirectResponse(url=f"/meeting/{meeting_id}/portal", status_code=303)


# ==================== GO LIVE MODE ====================

@router.get("/meeting/{meeting_id}/go-live")
async def go_live(request: Request, meeting_id: int, index: int = 0, edit: int = 0):
    """Presentation-friendly meeting mode — big text, minimal chrome, auto-advance."""
    with get_db() as conn:
        _ensure_tables(conn)
        meeting = _get_meeting(conn, meeting_id)

        # Get agenda items
        agenda = [dict(r) for r in conn.execute(queries.AGENDA_ITEMS, (meeting_id,)).fetchall()]
        if not agenda:
            return RedirectResponse(url=f"/meeting/{meeting_id}/portal", status_code=303)

        # Get staged actions for this meeting
        staged = {}
        for row in conn.execute(
            "SELECT * FROM sg_action_staging WHERE meeting_id = ?", (meeting_id,)
        ).fetchall():
            staged[row["proposal_uid"]] = dict(row)

        # If edit=1, clear the staged action so the form shows
        if edit and 0 <= index < len(agenda):
            uid = agenda[index]["proposal_uid"]
            if uid in staged:
                conn.execute(
                    "DELETE FROM sg_action_staging WHERE meeting_id = ? AND proposal_uid = ?",
                    (meeting_id, uid)
                )
                del staged[uid]

        # Load content for current proposal
        current_index = min(index, len(agenda) - 1)
        current_uid = agenda[current_index]["proposal_uid"]

        # Proposal text
        try:
            content_row = conn.execute(queries.PROPOSAL_TEXT_BY_UID, (current_uid,)).fetchone()
            if content_row:
                agenda[current_index]["content"] = dict(content_row)
            else:
                agenda[current_index]["content"] = None
        except Exception:
            agenda[current_index]["content"] = None

        # Modifications
        try:
            sql = queries.MODIFICATIONS_FOR_PROPOSALS.format(placeholders="?")
            mods = [dict(r) for r in conn.execute(sql, [current_uid]).fetchall()]
            agenda[current_index]["modifications"] = mods
        except Exception:
            agenda[current_index]["modifications"] = []

        # Cross-references
        try:
            sql = queries.PROPOSAL_LINKS_FOR_PROPOSALS.format(placeholders="?")
            links_raw = conn.execute(sql, [current_uid, current_uid]).fetchall()
            links = []
            for row in links_raw:
                row = dict(row)
                other_id = row["canonical_b"] if row["proposal_uid_a"] == current_uid else row["canonical_a"]
                links.append({"canonical_id": other_id, "link_type": row["link_type"], "notes": row["notes"]})
            agenda[current_index]["links"] = links
        except Exception:
            agenda[current_index]["links"] = []

        # Annotate all agenda items with staged actions (for nav strip)
        for item in agenda:
            item["staged_action"] = staged.get(item["proposal_uid"])

        done_count = sum(1 for a in agenda if a["staged_action"])

        # Load subgroup members for dropdowns
        members = [dict(r) for r in conn.execute(
            "SELECT display_name FROM subgroup_members WHERE body = ? ORDER BY last_name, first_name",
            (meeting["body"],)
        ).fetchall()]

    templates = request.app.state.templates
    return templates.TemplateResponse("meeting_golive.html", {
        "request": request,
        "meeting": meeting,
        "agenda": agenda,
        "current_index": current_index,
        "total": len(agenda),
        "done_count": done_count,
        "recommendations": config.RECOMMENDATIONS,
        "members": members,
    })


@router.post("/meeting/{meeting_id}/go-live/stage")
async def go_live_stage(
    request: Request,
    meeting_id: int,
    index: int = 0,
    canonical_id: str = Form(...),
    recommendation: str = Form(...),
    vote_for: int = Form(None),
    vote_against: int = Form(None),
    vote_not_voting: int = Form(None),
    reason: str = Form(""),
    modification_text: str = Form(""),
    moved_by: str = Form(""),
    seconded_by: str = Form(""),
):
    """Stage an action from Go Live mode, then redirect to next proposal."""
    with get_db() as conn:
        _ensure_tables(conn)
        meeting = _get_meeting(conn, meeting_id)

        prop = conn.execute(queries.PROPOSAL_UID_BY_CANONICAL, (canonical_id,)).fetchone()
        if not prop:
            raise HTTPException(status_code=404, detail=f"Proposal {canonical_id} not found")
        proposal_uid = prop["proposal_uid"]

        conn.execute("""
            INSERT INTO sg_action_staging
                (meeting_id, proposal_uid, canonical_id, subgroup, action_date,
                 recommendation, vote_for, vote_against, vote_not_voting,
                 reason, modification_text, moved_by, seconded_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(meeting_id, proposal_uid) DO UPDATE SET
                recommendation = excluded.recommendation,
                vote_for = excluded.vote_for,
                vote_against = excluded.vote_against,
                vote_not_voting = excluded.vote_not_voting,
                reason = excluded.reason,
                modification_text = excluded.modification_text,
                moved_by = excluded.moved_by,
                seconded_by = excluded.seconded_by
        """, (
            meeting_id, proposal_uid, canonical_id,
            meeting["body"], meeting["meeting_date"],
            recommendation,
            vote_for, vote_against, vote_not_voting,
            reason.strip() or None,
            modification_text.strip() or None,
            moved_by.strip() or None,
            seconded_by.strip() or None,
        ))

        # Find next unaddressed proposal
        agenda = [dict(r) for r in conn.execute(queries.AGENDA_ITEMS, (meeting_id,)).fetchall()]
        staged_uids = set(
            r["proposal_uid"] for r in conn.execute(
                "SELECT proposal_uid FROM sg_action_staging WHERE meeting_id = ?", (meeting_id,)
            ).fetchall()
        )

    checkpoint()

    # Auto-advance to next un-staged proposal, or stay on current if all done
    next_index = index + 1
    for i in range(len(agenda)):
        candidate = (index + 1 + i) % len(agenda)
        if agenda[candidate]["proposal_uid"] not in staged_uids:
            next_index = candidate
            break
    else:
        # All done — go back to current index to show staged result
        next_index = index

    return RedirectResponse(url=f"/meeting/{meeting_id}/go-live?index={next_index}", status_code=303)


# ==================== REVIEW & SEND ====================

@router.get("/meeting/{meeting_id}/review")
async def review_meeting(request: Request, meeting_id: int):
    """Review all staged actions before sending to secretariat."""
    with get_db() as conn:
        _ensure_tables(conn)
        meeting = _get_meeting(conn, meeting_id)

        staged = [dict(r) for r in conn.execute(
            "SELECT * FROM sg_action_staging WHERE meeting_id = ? ORDER BY canonical_id",
            (meeting_id,)
        ).fetchall()]

        total_agenda = conn.execute(
            "SELECT COUNT(*) as c FROM meeting_agenda_items WHERE meeting_id = ?",
            (meeting_id,)
        ).fetchone()["c"]

    modification_count = sum(
        1 for a in staged
        if a["modification_text"] and "Modified" in (a["recommendation"] or "")
    )

    return render(request, "meeting_review.html", {
        "meeting": meeting,
        "staged_actions": staged,
        "has_modifications": modification_count > 0,
        "modification_count": modification_count,
        "total_agenda": total_agenda,
    })


@router.post("/meeting/{meeting_id}/send")
async def send_to_secretariat(request: Request, meeting_id: int):
    """Commit all staged actions to the main subgroup_actions table."""
    with get_db() as conn:
        _ensure_tables(conn)
        meeting = _get_meeting(conn, meeting_id)

        staged = conn.execute(
            "SELECT * FROM sg_action_staging WHERE meeting_id = ?", (meeting_id,)
        ).fetchall()

        if not staged:
            raise HTTPException(status_code=400, detail="No staged actions to send")

        for action in staged:
            conn.execute(queries.INSERT_SG_ACTION, (
                meeting["track"],
                action["proposal_uid"],
                action["subgroup"],
                action["action_date"],
                action["recommendation"],
                action["vote_for"],
                action["vote_against"],
                action["vote_not_voting"],
                action["reason"],
                action["modification_text"],
                f"web_portal/{meeting_id}",
                action["moved_by"],
                action["seconded_by"],
            ))

        conn.execute(queries.UPDATE_MEETING_STATUS, ("COMPLETED", len(staged), meeting["id"]))
        conn.execute("DELETE FROM sg_action_staging WHERE meeting_id = ?", (meeting_id,))

    checkpoint()

    # Generate circ form document and queue for secretariat review
    try:
        from services.pdf_generator import generate_circform_document
        doc_path, doc_type = generate_circform_document(meeting_id)
        subgroup_name = config.resolve_subgroup(meeting["body"])
        with get_db() as conn:
            conn.execute(queries.INSERT_CIRC_FORM, (
                meeting_id, meeting["track"], subgroup_name,
                meeting["body"], doc_path,
            ))
        checkpoint()
        logger.info(f"Circ form {doc_type.upper()} generated and queued for meeting {meeting_id}")
    except Exception as e:
        # Don't fail the send if document generation fails — actions are already committed
        logger.error(f"Failed to generate circ form for meeting {meeting_id}: {e}")
        import traceback
        traceback.print_exc()

    return RedirectResponse(url=f"/meeting/{meeting_id}/portal", status_code=303)
