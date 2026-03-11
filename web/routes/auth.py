"""Authentication routes — fake login system with preset accounts.

Roles:
  - 'secretariat': Full admin access. Sees dashboard, all proposals, all meetings.
  - 'chair': Subgroup chair. Sees only their subgroup's meetings and the portals.
"""
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from db.connection import get_db
from routes.helpers import render

router = APIRouter()

# Preset user accounts — will move to DB later
USERS = {
    # Secretariat staff
    "alex.smith": {
        "name": "Alex Smith",
        "role": "secretariat",
        "title": "Director of Energy Programs",
        "body": None,
        "track": None,
    },
    "jason.toves": {
        "name": "Jason Toves",
        "role": "secretariat",
        "title": "Senior Staff Secretary",
        "body": None,
        "track": None,
    },
    # ── Residential Chairs ──────────────────────────────────────────
    "brian.shanks": {
        "name": "Brian Shanks",
        "role": "chair",
        "title": "SG2 Chair — Modeling and Whole Building Metrics",
        "body": "Residential Modeling Subgroup",
        "track": "residential",
    },
    "rob.howard": {
        "name": "Robert Howard",
        "role": "chair",
        "title": "SG2 Vice Chair — Modeling and Whole Building Metrics",
        "body": "Residential Modeling Subgroup",
        "track": "residential",
    },
    "rick.madrid": {
        "name": "Rick Madrid",
        "role": "chair",
        "title": "SG6 Chair — HVAC and Water Heating",
        "body": "Residential HVAC Subgroup",
        "track": "residential",
    },
    "res.envelope.chair": {
        "name": "Envelope SG4 Chair",
        "role": "chair",
        "title": "SG4 Chair — Envelope",
        "body": "Residential Envelope Subgroup",
        "track": "residential",
    },
    "res.eplr.chair": {
        "name": "EPLR SG3 Chair",
        "role": "chair",
        "title": "SG3 Chair — EPLR",
        "body": "Residential EPLR Subgroup",
        "track": "residential",
    },
    "res.admin.chair": {
        "name": "Admin SG1 Chair",
        "role": "chair",
        "title": "SG1 Chair — Consistency and Administration",
        "body": "Residential Administration Subgroup",
        "track": "residential",
    },
    "res.existing.chair": {
        "name": "Existing Buildings SG5 Chair",
        "role": "chair",
        "title": "SG5 Chair — Existing Buildings",
        "body": "Residential Existing Building Subgroup",
        "track": "residential",
    },
    "res.consensus.chair": {
        "name": "Residential Consensus Chair",
        "role": "chair",
        "title": "Residential Consensus Committee Chair",
        "body": "Residential Consensus Committee",
        "track": "residential",
    },
    # ── Commercial Chairs ──────────────────────────────────────────
    "com.admin.chair": {
        "name": "Commercial Admin Chair",
        "role": "chair",
        "title": "Commercial Administration Subgroup Chair",
        "body": "Commercial Administration Subgroup",
        "track": "commercial",
    },
    "com.envelope.chair": {
        "name": "Commercial Envelope Chair",
        "role": "chair",
        "title": "Envelope and Embodied Energy Subgroup Chair",
        "body": "Envelope and Embodied Energy Subgroup",
        "track": "commercial",
    },
    "com.eplr.chair": {
        "name": "Commercial EPLR Chair",
        "role": "chair",
        "title": "Commercial EPLR Subgroup Chair",
        "body": "Commercial EPLR Subgroup",
        "track": "commercial",
    },
    "com.hvacr.chair": {
        "name": "Commercial HVACR Chair",
        "role": "chair",
        "title": "Commercial HVACR and Water Heating Subgroup Chair",
        "body": "Commercial HVACR and Water Heating Subgroup",
        "track": "commercial",
    },
    "com.modeling.chair": {
        "name": "Commercial Modeling Chair",
        "role": "chair",
        "title": "Commercial Modeling Subgroup Chair",
        "body": "Commercial Modeling Subgroup",
        "track": "commercial",
    },
    "duane.jonlin": {
        "name": "Duane Jonlin",
        "role": "chair",
        "title": "Commercial Consensus Committee Chair",
        "body": "Commercial Consensus Committee",
        "track": "commercial",
    },
}


def get_current_user(request: Request) -> dict | None:
    """Get current logged-in user from session cookie."""
    user_id = request.cookies.get("icc_user")
    if user_id and user_id in USERS:
        return {"user_id": user_id, **USERS[user_id]}
    return None


def require_login(request: Request):
    """Return user dict or None (caller should redirect to /login)."""
    return get_current_user(request)


def require_role(request: Request, role: str):
    """Return user if they have the required role, else None."""
    user = get_current_user(request)
    if user and user["role"] == role:
        return user
    return None


@router.get("/login")
async def login_page(request: Request):
    """Show login page with user selection."""
    templates = request.app.state.templates
    # Group users by role
    secretariat_users = {k: v for k, v in USERS.items() if v["role"] == "secretariat"}
    chair_users = {k: v for k, v in USERS.items() if v["role"] == "chair"}
    return templates.TemplateResponse("login.html", {
        "request": request,
        "secretariat_users": secretariat_users,
        "chair_users": chair_users,
    })


@router.post("/login")
async def do_login(request: Request, user_id: str = Form(...)):
    """Set session cookie and redirect to appropriate home."""
    user = USERS.get(user_id)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    # Redirect based on role
    if user["role"] == "secretariat":
        redirect_url = "/"
    else:
        redirect_url = "/home"

    response = RedirectResponse(url=redirect_url, status_code=303)
    response.set_cookie("icc_user", user_id, max_age=86400 * 7)  # 7 days
    return response


@router.get("/logout")
async def logout(request: Request):
    """Clear session and redirect to login."""
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("icc_user")
    return response


@router.get("/home")
async def chair_home(request: Request):
    """Chair's home page — shows their subgroup's meetings."""
    user = require_login(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if user["role"] == "secretariat":
        return RedirectResponse(url="/", status_code=303)

    import config
    with get_db() as conn:
        # Get this chair's meetings
        my_meetings = [dict(r) for r in conn.execute(
            """SELECT * FROM meetings
               WHERE body = ?
               ORDER BY meeting_date DESC""",
            (user["body"],)
        ).fetchall()]

        # Get pending proposal count for their subgroup
        subgroup_name = config.resolve_subgroup(user["body"])
        pending_count = conn.execute(
            """SELECT COUNT(*) as c FROM proposals p
               JOIN v_current_status v ON p.canonical_id = v.canonical_id
               WHERE p.track = ? AND p.current_subgroup = ? AND v.status IN ('Pending', 'Testing')""",
            (user["track"], subgroup_name)
        ).fetchone()["c"]

        # Get agenda/progress info for each meeting
        for m in my_meetings:
            agenda_count = conn.execute(
                "SELECT COUNT(*) as c FROM meeting_agenda_items WHERE meeting_id = ?",
                (m["id"],)
            ).fetchone()["c"]
            staged_count = conn.execute(
                "SELECT COUNT(*) as c FROM sg_action_staging WHERE meeting_id = ?",
                (m["id"],)
            ).fetchone()["c"]
            m["agenda_count"] = agenda_count
            m["staged_count"] = staged_count

    return render(request, "chair_home.html", {
        "meetings": my_meetings,
        "pending_count": pending_count,
    })
