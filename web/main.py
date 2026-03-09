"""ICC Code Development Platform — FastAPI Application."""
import sys
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
import config

# Ensure the web directory is in the path for imports
sys.path.insert(0, str(Path(__file__).parent))

from routes import auth, dashboard, proposals, meetings, subgroup_portal, exports, circforms

app = FastAPI(
    title=config.APP_TITLE,
    version=config.APP_VERSION,
)

# Static files
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

# Templates
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
app.state.templates = templates


# Custom Jinja2 filters
def format_time(time_str):
    """Convert 24h time string to 12h format with AM/PM.
    Handles: '14:00', '2:00 p.m. EST', None, empty string."""
    if not time_str:
        return ""
    time_str = str(time_str).strip()
    # Already formatted (contains 'a.m.' or 'p.m.')
    if "a.m." in time_str or "p.m." in time_str or "AM" in time_str or "PM" in time_str:
        return time_str
    # Try to parse HH:MM 24h format
    try:
        parts = time_str.split(":")
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
        suffix = "a.m." if hour < 12 else "p.m."
        display_hour = hour if 1 <= hour <= 12 else (hour - 12 if hour > 12 else 12)
        if minute == 0:
            return f"{display_hour}:{minute:02d} {suffix} EST"
        return f"{display_hour}:{minute:02d} {suffix} EST"
    except (ValueError, IndexError):
        return time_str


templates.env.filters["format_time"] = format_time


# --- Authentication middleware ---
# Public routes that don't need login
PUBLIC_PATHS = {"/login", "/health", "/static"}


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """Redirect to login if not authenticated. Enforce role-based access."""
    path = request.url.path

    # Allow public paths and static files
    if path in PUBLIC_PATHS or path.startswith("/static"):
        return await call_next(request)

    # Check if user is logged in
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    # Secretariat-only pages: dashboard, proposals list, meetings list
    secretariat_paths = {"/", "/proposals", "/meetings", "/meetings/create", "/circ-forms"}
    # Also match /meetings?... and /proposals?... and /circ-forms/...
    if path in secretariat_paths or path == "/meetings/create" or path.startswith("/circ-forms"):
        if user["role"] != "secretariat":
            # Chairs trying to access secretariat pages get bounced to their home
            return RedirectResponse(url="/home", status_code=303)

    # Chair-only pages
    if path == "/home":
        if user["role"] == "secretariat":
            return RedirectResponse(url="/", status_code=303)

    # Portal pages (/meeting/*/portal, etc.) — accessible to both roles
    # Export pages — accessible to both roles

    # Attach user to request state for templates
    request.state.user = user
    return await call_next(request)


# Routes — auth first (handles /login, /logout, /home)
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(proposals.router)
app.include_router(meetings.router)
app.include_router(subgroup_portal.router)
app.include_router(exports.router)
app.include_router(circforms.router)


@app.get("/health")
async def health():
    """Health check endpoint."""
    from db.connection import get_db
    with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) as c FROM proposals").fetchone()["c"]
    return {
        "status": "ok",
        "db": str(config.DB_PATH),
        "proposals": count,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=True,
    )
