"""Meeting Documents — upload, manage, and serve reference documents for meetings.

Chairs can upload PDFs and images to display during meetings via the Go Live view.
Documents are stored per-meeting and served through authenticated routes.
"""
from fastapi import APIRouter, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse, FileResponse
from db.connection import get_db, checkpoint
import config
import logging
import mimetypes
from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter()

ALLOWED_EXTENSIONS = config.ALLOWED_DOC_EXTENSIONS
MAX_SIZE = config.MAX_DOC_SIZE_MB * 1024 * 1024  # Convert to bytes


def _get_meeting_docs(conn, meeting_id: int) -> list:
    """Get all documents for a meeting, ordered by sort_order."""
    return [dict(r) for r in conn.execute(
        "SELECT * FROM meeting_documents WHERE meeting_id = ? ORDER BY sort_order, uploaded_at",
        (meeting_id,)
    ).fetchall()]


@router.post("/meeting/{meeting_id}/documents/upload")
async def upload_document(
    request: Request,
    meeting_id: int,
    file: UploadFile = File(...),
    display_name: str = Form(""),
):
    """Upload a document for a meeting."""
    # Validate file extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' not allowed. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    # Read file content
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {config.MAX_DOC_SIZE_MB} MB."
        )

    # Create meeting-specific directory
    meeting_dir = config.MEETING_DOCS_DIR / str(meeting_id)
    meeting_dir.mkdir(parents=True, exist_ok=True)

    # Generate safe filename (avoid collisions)
    safe_name = file.filename.replace(" ", "_")
    file_path = meeting_dir / safe_name
    counter = 1
    while file_path.exists():
        stem = Path(safe_name).stem
        file_path = meeting_dir / f"{stem}_{counter}{ext}"
        counter += 1

    # Write file
    file_path.write_bytes(content)

    # Determine display name
    if not display_name.strip():
        display_name = Path(file.filename).stem.replace("_", " ").replace("-", " ")

    # Determine MIME type
    mime_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"

    # Get next sort order
    with get_db() as conn:
        row = conn.execute(
            "SELECT COALESCE(MAX(sort_order), 0) + 10 as next_order FROM meeting_documents WHERE meeting_id = ?",
            (meeting_id,)
        ).fetchone()
        next_order = row["next_order"]

        user = getattr(request.state, "user", None)
        username = user.get("name", "") if user else ""

        conn.execute("""
            INSERT INTO meeting_documents
                (meeting_id, display_name, file_name, file_path, file_size, mime_type, sort_order, uploaded_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            meeting_id, display_name.strip(), file_path.name,
            str(file_path), len(content), mime_type, next_order, username,
        ))
    checkpoint()

    logger.info(f"Document uploaded: {file_path.name} for meeting {meeting_id}")
    return RedirectResponse(url=f"/meeting/{meeting_id}/portal#documents-section", status_code=303)


@router.post("/meeting/{meeting_id}/documents/{doc_id}/delete")
async def delete_document(request: Request, meeting_id: int, doc_id: int):
    """Delete a document from a meeting."""
    with get_db() as conn:
        doc = conn.execute(
            "SELECT * FROM meeting_documents WHERE id = ? AND meeting_id = ?",
            (doc_id, meeting_id)
        ).fetchone()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Delete file from disk
        file_path = Path(doc["file_path"])
        if file_path.exists():
            file_path.unlink()

        # Delete DB record
        conn.execute("DELETE FROM meeting_documents WHERE id = ?", (doc_id,))
    checkpoint()

    logger.info(f"Document deleted: {doc['file_name']} from meeting {meeting_id}")
    return RedirectResponse(url=f"/meeting/{meeting_id}/portal#documents-section", status_code=303)


@router.post("/meeting/{meeting_id}/documents/{doc_id}/rename")
async def rename_document(
    request: Request,
    meeting_id: int,
    doc_id: int,
    display_name: str = Form(...),
):
    """Rename a document's display name."""
    with get_db() as conn:
        conn.execute(
            "UPDATE meeting_documents SET display_name = ? WHERE id = ? AND meeting_id = ?",
            (display_name.strip(), doc_id, meeting_id)
        )
    checkpoint()
    return RedirectResponse(url=f"/meeting/{meeting_id}/portal#documents-section", status_code=303)


@router.get("/meeting/{meeting_id}/documents/{doc_id}/view")
async def view_document(request: Request, meeting_id: int, doc_id: int):
    """Serve a document file for viewing."""
    with get_db() as conn:
        doc = conn.execute(
            "SELECT * FROM meeting_documents WHERE id = ? AND meeting_id = ?",
            (doc_id, meeting_id)
        ).fetchone()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = Path(doc["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Document file not found on disk")

    return FileResponse(
        path=str(file_path),
        media_type=doc["mime_type"],
        filename=doc["file_name"],
        headers={"Content-Disposition": "inline"},
    )


@router.get("/meeting/{meeting_id}/documents/list")
async def list_documents_json(request: Request, meeting_id: int):
    """Return documents list as JSON (for HTMX/JS consumers)."""
    with get_db() as conn:
        docs = _get_meeting_docs(conn, meeting_id)
    return JSONResponse([{
        "id": d["id"],
        "display_name": d["display_name"],
        "file_name": d["file_name"],
        "mime_type": d["mime_type"],
        "file_size": d["file_size"],
        "view_url": f"/meeting/{meeting_id}/documents/{d['id']}/view",
    } for d in docs])
