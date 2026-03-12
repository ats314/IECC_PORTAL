"""Shared route helpers."""
from fastapi import Request
from fastapi.responses import HTMLResponse


def is_teams_embedded(request: Request) -> bool:
    """Check if the request is from a Teams iframe (?embedded=teams)."""
    return request.query_params.get("embedded") == "teams"


def render(request: Request, template: str, context: dict = None) -> HTMLResponse:
    """Render a template with user auto-injected from middleware."""
    ctx = {"request": request}
    ctx["user"] = getattr(request.state, "user", None)
    ctx["teams_embedded"] = is_teams_embedded(request)

    # Choose base template: Teams embedded overrides role-based selection
    if ctx["teams_embedded"]:
        ctx["base_template"] = "teams_base.html"
    elif ctx["user"] and ctx["user"]["role"] == "chair":
        ctx["base_template"] = "chair_base.html"
    else:
        ctx["base_template"] = "base.html"

    if context:
        ctx.update(context)
    return request.app.state.templates.TemplateResponse(template, ctx)
