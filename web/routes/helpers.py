"""Shared route helpers."""
from fastapi import Request
from fastapi.responses import HTMLResponse


def render(request: Request, template: str, context: dict = None) -> HTMLResponse:
    """Render a template with user auto-injected from middleware."""
    ctx = {"request": request}
    ctx["user"] = getattr(request.state, "user", None)

    # Choose base template: chairs get chair_base, secretariat gets base
    if ctx["user"] and ctx["user"]["role"] == "chair":
        ctx["base_template"] = "chair_base.html"
    else:
        ctx["base_template"] = "base.html"

    if context:
        ctx.update(context)
    return request.app.state.templates.TemplateResponse(template, ctx)
