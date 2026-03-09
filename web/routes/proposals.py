"""Proposal list and detail routes."""
from fastapi import APIRouter, Request, HTTPException
from db.connection import get_db
from db import queries
from routes.helpers import render

router = APIRouter()


@router.get("/proposals")
async def proposal_list(request: Request):
    track = request.query_params.get("track", "")
    status = request.query_params.get("status", "")
    subgroup = request.query_params.get("subgroup", "")
    phase = request.query_params.get("phase", "")
    q = request.query_params.get("q", "")

    sql = queries.PROPOSALS_LIST
    params = []

    if track:
        sql += " AND p.track = ?"
        params.append(track)
    if status:
        sql += " AND v.status = ?"
        params.append(status)
    if subgroup:
        sql += " AND p.current_subgroup = ?"
        params.append(subgroup)
    if phase:
        sql += " AND p.phase = ?"
        params.append(phase)
    if q:
        sql += " AND (p.canonical_id LIKE ? OR p.proponent LIKE ? OR p.code_section LIKE ?)"
        like = f"%{q}%"
        params.extend([like, like, like])

    sql += " ORDER BY p.track, p.canonical_id"

    with get_db() as conn:
        rows = [dict(r) for r in conn.execute(sql, params).fetchall()]

        # Get distinct subgroups for dropdown
        subgroups = [r["current_subgroup"] for r in conn.execute(
            "SELECT DISTINCT current_subgroup FROM proposals WHERE current_subgroup IS NOT NULL ORDER BY current_subgroup"
        ).fetchall()]

    # If HTMX request, return partial
    if request.headers.get("HX-Request"):
        templates = request.app.state.templates
        return templates.TemplateResponse("partials/proposal_rows.html", {
            "request": request, "proposals": rows
        })

    return render(request, "proposal_list.html", {
        "proposals": rows,
        "filters": {"track": track, "status": status, "subgroup": subgroup, "phase": phase, "q": q},
        "subgroups": subgroups,
    })


@router.get("/proposals/{canonical_id}")
async def proposal_detail(request: Request, canonical_id: str):
    with get_db() as conn:
        proposal = conn.execute(queries.PROPOSAL_DETAIL, (canonical_id,)).fetchone()
        if not proposal:
            raise HTTPException(status_code=404, detail=f"Proposal {canonical_id} not found")
        proposal = dict(proposal)

        uid = proposal["proposal_uid"]
        sg_actions = [dict(r) for r in conn.execute(queries.PROPOSAL_SG_ACTIONS, (uid,)).fetchall()]
        ca_actions = [dict(r) for r in conn.execute(queries.PROPOSAL_CA_ACTIONS, (uid,)).fetchall()]
        dq_flags = [dict(r) for r in conn.execute(queries.PROPOSAL_DQ_FLAGS, (uid,)).fetchall()]

    return render(request, "proposal_detail.html", {
        "proposal": proposal,
        "sg_actions": sg_actions,
        "ca_actions": ca_actions,
        "dq_flags": dq_flags,
    })
