"""Teams integration routes — config page for meeting tab setup."""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("/config", response_class=HTMLResponse)
async def teams_config(request: Request):
    """Teams tab configuration page. Loaded when a user adds the app to a meeting."""
    templates = request.app.state.templates
    return templates.TemplateResponse("teams_config.html", {"request": request})
