"""Document export routes — agenda and circulation form generation."""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import Response
from db.connection import get_db
from db import queries
from services.doc_generator import generate_agenda_docx, generate_circform_docx, generate_modification_docx

router = APIRouter()


@router.get("/meeting/{meeting_id}/export-agenda")
async def export_agenda(request: Request, meeting_id: int):
    """Generate and download a meeting agenda as a Word document."""
    with get_db() as conn:
        meeting = conn.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,)).fetchone()
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        meeting = dict(meeting)

        # Get agenda items in order
        agenda = [dict(r) for r in conn.execute(queries.AGENDA_ITEMS, (meeting_id,)).fetchall()]

    if not agenda:
        raise HTTPException(status_code=400, detail="No agenda items to export. Populate the agenda first.")

    docx_bytes = generate_agenda_docx(meeting, agenda)

    # Filename: Body_Date_Agenda.docx
    safe_body = meeting["body"].replace(" ", "_").replace("/", "-")
    filename = f"{safe_body}_{meeting['meeting_date']}_Agenda.docx"

    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/meeting/{meeting_id}/export-circform")
async def export_circform(request: Request, meeting_id: int):
    """Generate and download a circulation form from completed meeting actions."""
    with get_db() as conn:
        meeting = conn.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,)).fetchone()
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        meeting = dict(meeting)

        # Try staged actions first (pre-send), then committed actions
        actions = [dict(r) for r in conn.execute(
            """SELECT s.*, p.code_section
               FROM sg_action_staging s
               JOIN proposals p ON s.proposal_uid = p.proposal_uid
               WHERE s.meeting_id = ?
               ORDER BY s.canonical_id""",
            (meeting_id,)
        ).fetchall()]

        if not actions:
            # Fall back to committed actions from this meeting
            actions = [dict(r) for r in conn.execute(
                """SELECT sa.*, p.canonical_id, p.code_section
                   FROM subgroup_actions sa
                   JOIN proposals p ON sa.proposal_uid = p.proposal_uid
                   WHERE sa.source_file = ?
                   ORDER BY p.canonical_id""",
                (f"web_portal/{meeting_id}",)
            ).fetchall()]

    if not actions:
        raise HTTPException(status_code=400, detail="No actions recorded for this meeting.")

    docx_bytes = generate_circform_docx(meeting, actions)

    safe_body = meeting["body"].replace(" ", "_").replace("/", "-")
    filename = f"{safe_body}_CircForm_{meeting['meeting_date']}.docx"

    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/meeting/{meeting_id}/export-modifications")
async def export_modifications(request: Request, meeting_id: int):
    """Generate a Word document with modification language for cdpACCESS entry.

    Only includes proposals with 'Modified' recommendations. Each proposal gets
    a structured entry with metadata, the modification text, and a CDP entry checklist.
    """
    with get_db() as conn:
        meeting = conn.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,)).fetchone()
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        meeting = dict(meeting)

        # Try staged actions first (pre-send), then committed actions
        actions = [dict(r) for r in conn.execute(
            """SELECT s.*, p.code_section, p.proponent
               FROM sg_action_staging s
               JOIN proposals p ON s.proposal_uid = p.proposal_uid
               WHERE s.meeting_id = ?
               ORDER BY s.canonical_id""",
            (meeting_id,)
        ).fetchall()]

        if not actions:
            actions = [dict(r) for r in conn.execute(
                """SELECT sa.*, p.canonical_id, p.code_section, p.proponent
                   FROM subgroup_actions sa
                   JOIN proposals p ON sa.proposal_uid = p.proposal_uid
                   WHERE sa.source_file = ?
                   ORDER BY p.canonical_id""",
                (f"web_portal/{meeting_id}",)
            ).fetchall()]

    # Filter to modified only
    modified = [a for a in actions if a.get("modification_text") and "Modified" in (a.get("recommendation") or "")]
    if not modified:
        raise HTTPException(status_code=400, detail="No modifications found for this meeting.")

    docx_bytes = generate_modification_docx(meeting, modified)

    safe_body = meeting["body"].replace(" ", "_").replace("/", "-")
    filename = f"{safe_body}_Modifications_{meeting['meeting_date']}.docx"

    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
