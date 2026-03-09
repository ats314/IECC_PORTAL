"""Secretariat dashboard routes."""
from fastapi import APIRouter, Request
from db.connection import get_db
from db import queries
import config
from routes.helpers import render

router = APIRouter()


def _fetch_dashboard_data(track_filter=None):
    """Fetch all dashboard data."""
    with get_db() as conn:
        # Counts by track
        counts = {}
        for row in conn.execute(queries.DASHBOARD_COUNTS).fetchall():
            counts[row["track"]] = dict(row)

        # Pending by subgroup
        pending_sg = {}
        for row in conn.execute(queries.PENDING_BY_SUBGROUP).fetchall():
            t = row["track"]
            if t not in pending_sg:
                pending_sg[t] = []
            pending_sg[t].append(dict(row))

        # Upcoming meetings
        meetings = [dict(r) for r in conn.execute(queries.UPCOMING_MEETINGS).fetchall()]

        # Recent SG actions
        recent = [dict(r) for r in conn.execute(queries.RECENT_SUBGROUP_ACTIONS).fetchall()]

        # Open DQ flags
        flags = [dict(r) for r in conn.execute(queries.OPEN_DQ_FLAGS).fetchall()]

        # In-progress meetings (have agenda + staged actions)
        in_progress = [dict(r) for r in conn.execute(queries.IN_PROGRESS_MEETINGS).fetchall()]

        # Pending circ forms for secretariat review
        pending_circforms = [dict(r) for r in conn.execute(queries.PENDING_CIRC_FORMS).fetchall()]

    return {
        "counts": counts,
        "pending_by_subgroup": pending_sg,
        "upcoming_meetings": meetings,
        "recent_actions": recent,
        "open_flags": flags,
        "in_progress_meetings": in_progress,
        "pending_circforms": pending_circforms,
        "track_filter": track_filter,
        "sp_enabled": config.SP_ENABLED,
    }


@router.get("/")
async def dashboard(request: Request):
    track = request.query_params.get("track")
    data = _fetch_dashboard_data(track)
    return render(request, "dashboard.html", data)
