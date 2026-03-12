"""Circulation form review and approval routes (secretariat-only)."""
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import Response, RedirectResponse
from db.connection import get_db, checkpoint
from db import queries
from routes.helpers import render
import config
import logging
import shutil
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter()


def _copy_to_approved_folder(form: dict):
    """Copy approved circ form to organized folder matching SharePoint structure.

    Target: approved_circforms/{subgroup_folder}/{YY-MM-DD Meeting}/filename.ext
    """
    try:
        src = _resolve_doc_path(form)
        if not src.exists():
            logger.warning(f"Cannot copy circ form {form['id']}: source not found at {src}")
            return

        # Build destination path matching SharePoint folder structure
        sp_folder = config.subgroup_to_sp_folder(form["subgroup"])
        try:
            dt = datetime.strptime(form["meeting_date"], "%Y-%m-%d")
            meeting_folder = f"{dt.strftime('%y-%m-%d')} Meeting"
        except (ValueError, TypeError):
            meeting_folder = f"{form['meeting_date']} Meeting"

        dest_dir = config.APPROVED_CIRCFORMS_DIR / sp_folder / meeting_folder
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / src.name

        shutil.copy2(src, dest)
        logger.info(f"Circ form {form['id']} copied to {dest}")
    except Exception as e:
        logger.error(f"Failed to copy circ form {form['id']} to approved folder: {e}")

# MIME types for supported document formats
MIME_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def _resolve_doc_path(form: dict) -> Path:
    """Resolve the document path from the circ_forms record."""
    doc_path = Path(form["pdf_path"])
    if not doc_path.is_absolute():
        doc_path = Path(__file__).parent.parent / doc_path
    return doc_path


def _get_mime_type(path: Path) -> str:
    """Get the MIME type based on file extension."""
    return MIME_TYPES.get(path.suffix.lower(), "application/octet-stream")


@router.get("/circ-forms")
async def circ_forms_list(request: Request):
    """Show all circulation forms with their statuses."""
    with get_db() as conn:
        all_forms = [dict(r) for r in conn.execute(queries.ALL_CIRC_FORMS).fetchall()]
        pending = [f for f in all_forms if f["status"] == "pending_review"]
        reviewed = [f for f in all_forms if f["status"] != "pending_review"]

    return render(request, "circ_forms.html", {
        "pending_forms": pending,
        "reviewed_forms": reviewed,
        "sp_enabled": config.SP_ENABLED,
    })


@router.get("/circ-forms/{form_id}/preview")
async def preview_circ_form(request: Request, form_id: int):
    """Serve the generated document for preview in browser."""
    with get_db() as conn:
        form = conn.execute(queries.CIRC_FORM_BY_ID, (form_id,)).fetchone()
        if not form:
            raise HTTPException(status_code=404, detail="Circulation form not found")
        form = dict(form)

    doc_path = _resolve_doc_path(form)
    if not doc_path.exists():
        raise HTTPException(status_code=404, detail="Document file not found on disk")

    doc_bytes = doc_path.read_bytes()
    mime = _get_mime_type(doc_path)
    disposition = "inline" if doc_path.suffix == ".pdf" else "attachment"
    filename = f"circform_{form_id}{doc_path.suffix}"

    return Response(
        content=doc_bytes,
        media_type=mime,
        headers={"Content-Disposition": f'{disposition}; filename="{filename}"'},
    )


@router.get("/circ-forms/{form_id}/download")
async def download_circ_form(request: Request, form_id: int):
    """Download the generated document."""
    with get_db() as conn:
        form = conn.execute(queries.CIRC_FORM_BY_ID, (form_id,)).fetchone()
        if not form:
            raise HTTPException(status_code=404, detail="Circulation form not found")
        form = dict(form)

    doc_path = _resolve_doc_path(form)
    if not doc_path.exists():
        raise HTTPException(status_code=404, detail="Document file not found on disk")

    safe_body = form["body"].replace(" ", "_").replace("/", "-")
    ext = doc_path.suffix
    filename = f"{safe_body}_CircForm_{form['meeting_date']}{ext}"

    doc_bytes = doc_path.read_bytes()
    return Response(
        content=doc_bytes,
        media_type=_get_mime_type(doc_path),
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/circ-forms/{form_id}/approve")
async def approve_circ_form(request: Request, form_id: int):
    """Approve a circ form. Optionally upload to SharePoint if configured."""
    from routes.auth import get_current_user
    user = get_current_user(request)
    if not user or user["role"] != "secretariat":
        raise HTTPException(status_code=403, detail="Secretariat only")

    with get_db() as conn:
        form = conn.execute(queries.CIRC_FORM_BY_ID, (form_id,)).fetchone()
        if not form:
            raise HTTPException(status_code=404, detail="Circulation form not found")
        form = dict(form)

        if form["status"] != "pending_review":
            raise HTTPException(status_code=400, detail="Form is not pending review")

        # Mark as approved
        conn.execute(queries.APPROVE_CIRC_FORM, (user["name"], form_id))

    checkpoint()

    # Copy approved doc to organized local folder for easy SharePoint upload
    _copy_to_approved_folder(form)

    # Attempt SharePoint upload if configured
    sp_url = None
    if config.SP_ENABLED:
        try:
            from services.sharepoint import upload_circform_to_sharepoint
            sp_url = upload_circform_to_sharepoint(form)
            if sp_url:
                with get_db() as conn:
                    conn.execute(queries.UPLOAD_CIRC_FORM, (sp_url, form_id))
                checkpoint()
                logger.info(f"Circ form {form_id} uploaded to SharePoint: {sp_url}")
        except Exception as e:
            logger.error(f"SharePoint upload failed for circ form {form_id}: {e}")

    # Return HTMX partial if it's an HTMX request
    if request.headers.get("HX-Request"):
        templates = request.app.state.templates
        form["status"] = "uploaded" if sp_url else "approved"
        form["reviewed_by"] = user["name"]
        form["sharepoint_url"] = sp_url
        return templates.TemplateResponse("partials/circform_row.html", {
            "request": request,
            "form": form,
            "sp_enabled": config.SP_ENABLED,
        })

    return RedirectResponse(url="/circ-forms", status_code=303)


@router.post("/circ-forms/{form_id}/reject")
async def reject_circ_form(
    request: Request,
    form_id: int,
    reason: str = Form(""),
):
    """Reject a circ form with an optional reason."""
    from routes.auth import get_current_user
    user = get_current_user(request)
    if not user or user["role"] != "secretariat":
        raise HTTPException(status_code=403, detail="Secretariat only")

    with get_db() as conn:
        form = conn.execute(queries.CIRC_FORM_BY_ID, (form_id,)).fetchone()
        if not form:
            raise HTTPException(status_code=404, detail="Circulation form not found")
        form = dict(form)

        if form["status"] != "pending_review":
            raise HTTPException(status_code=400, detail="Form is not pending review")

        conn.execute(queries.REJECT_CIRC_FORM, (user["name"], reason.strip() or None, form_id))

    checkpoint()

    if request.headers.get("HX-Request"):
        templates = request.app.state.templates
        form["status"] = "rejected"
        form["reviewed_by"] = user["name"]
        form["rejection_reason"] = reason.strip() or None
        return templates.TemplateResponse("partials/circform_row.html", {
            "request": request,
            "form": form,
            "sp_enabled": config.SP_ENABLED,
        })

    return RedirectResponse(url="/circ-forms", status_code=303)
