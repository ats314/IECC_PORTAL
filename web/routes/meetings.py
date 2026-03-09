"""Meeting management routes."""
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from db.connection import get_db, checkpoint
from db import queries
import config
from routes.helpers import render

router = APIRouter()


@router.get("/meetings")
async def meeting_list(request: Request):
    track = request.query_params.get("track", "")

    with get_db() as conn:
        if track:
            meetings = [dict(r) for r in conn.execute(
                "SELECT * FROM meetings WHERE track = ? ORDER BY meeting_date DESC", (track,)
            ).fetchall()]
        else:
            meetings = [dict(r) for r in conn.execute(queries.ALL_MEETINGS).fetchall()]

    return render(request, "meetings.html", {
        "meetings": meetings,
        "track_filter": track,
        "commercial_bodies": config.COMMERCIAL_BODIES,
        "residential_bodies": config.RESIDENTIAL_BODIES,
    })


@router.get("/meetings/{meeting_id}")
async def meeting_detail(request: Request, meeting_id: int):
    with get_db() as conn:
        meeting = conn.execute(
            "SELECT * FROM meetings WHERE id = ?", (meeting_id,)
        ).fetchone()
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        meeting = dict(meeting)

        # Get proposals for this meeting's subgroup (resolve body name to subgroup name)
        subgroup_name = config.resolve_subgroup(meeting["body"])
        proposals = [dict(r) for r in conn.execute(
            queries.MEETING_PROPOSALS, (meeting["track"], subgroup_name)
        ).fetchall()]

    return render(request, "meeting_detail.html", {
        "meeting": meeting,
        "proposals": proposals,
    })


@router.post("/meetings/{meeting_id}/delete")
async def delete_meeting(request: Request, meeting_id: int):
    """Delete a scheduled meeting (only if not completed)."""
    with get_db() as conn:
        meeting = conn.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,)).fetchone()
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        if meeting["status"] == "COMPLETED":
            raise HTTPException(status_code=400, detail="Cannot delete a completed meeting")

        # Clean up related data
        conn.execute("DELETE FROM meeting_agenda_items WHERE meeting_id = ?", (meeting_id,))
        conn.execute("DELETE FROM sg_action_staging WHERE meeting_id = ?", (meeting_id,))
        conn.execute("DELETE FROM meetings WHERE id = ?", (meeting_id,))
    checkpoint()
    return RedirectResponse(url="/meetings", status_code=303)


@router.post("/meetings/create")
async def create_meeting(
    request: Request,
    track: str = Form(...),
    meeting_date: str = Form(...),
    meeting_time: str = Form(""),
    body: str = Form(...),
    phase: str = Form("CODE_PROPOSAL"),
    notes: str = Form(""),
):
    with get_db() as conn:
        conn.execute(queries.INSERT_MEETING, (track, meeting_date, meeting_time, body, phase, notes))
    checkpoint()
    return RedirectResponse(url="/meetings", status_code=303)
