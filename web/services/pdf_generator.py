"""Generate circulation form documents from meeting data.

Flow:
1. Uses existing generate_circform_docx() to create the Word doc
2. Attempts PDF conversion via LibreOffice CLI (headless)
3. Falls back to DOCX if LibreOffice is not available
4. Saves to generated/circforms/{meeting_id}/ directory
5. Returns the path for storage in circ_forms table
"""
import os
import shutil
import subprocess
import logging
from pathlib import Path

import config
from db.connection import get_db
from db import queries
from services.doc_generator import generate_circform_docx

logger = logging.getLogger(__name__)


def _has_libreoffice() -> bool:
    """Check if LibreOffice is available on the system."""
    # Check common names: libreoffice, soffice, and Windows paths
    for cmd in ["libreoffice", "soffice"]:
        if shutil.which(cmd):
            return True
    # Check common Windows install paths
    for path in [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ]:
        if os.path.exists(path):
            return True
    return False


def _get_libreoffice_cmd() -> str:
    """Get the LibreOffice command path."""
    for cmd in ["libreoffice", "soffice"]:
        path = shutil.which(cmd)
        if path:
            return path
    for path in [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ]:
        if os.path.exists(path):
            return path
    raise RuntimeError("LibreOffice not found")


def _ensure_dirs(meeting_id: int) -> Path:
    """Create the output directory for a meeting's circ form."""
    out_dir = config.CIRCFORMS_DIR / str(meeting_id)
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def _docx_to_pdf(docx_bytes: bytes, output_dir: Path, filename_stem: str) -> Path:
    """Convert a DOCX buffer to PDF using LibreOffice headless.

    Returns:
        Path to the generated PDF file

    Raises:
        RuntimeError if conversion fails
    """
    docx_path = output_dir / f"{filename_stem}.docx"
    docx_path.write_bytes(docx_bytes)

    try:
        lo_cmd = _get_libreoffice_cmd()
        result = subprocess.run(
            [lo_cmd, "--headless", "--convert-to", "pdf",
             "--outdir", str(output_dir), str(docx_path)],
            capture_output=True,
            timeout=60,
        )
        if result.returncode != 0:
            stderr = result.stderr.decode(errors="replace")[:500]
            logger.error(f"LibreOffice conversion failed: {stderr}")
            raise RuntimeError(f"PDF conversion failed: {stderr[:200]}")

        pdf_path = output_dir / f"{filename_stem}.pdf"
        if not pdf_path.exists():
            raise RuntimeError(f"PDF not found at expected path: {pdf_path}")

        return pdf_path

    finally:
        # Clean up the intermediate DOCX only if PDF was created
        pdf_check = output_dir / f"{filename_stem}.pdf"
        if pdf_check.exists() and docx_path.exists():
            docx_path.unlink()


def generate_circform_document(meeting_id: int) -> tuple[str, str]:
    """Generate a circulation form document for a completed meeting.

    Tries PDF first (via LibreOffice), falls back to DOCX if unavailable.

    Args:
        meeting_id: The meeting ID to generate the circ form for

    Returns:
        Tuple of (absolute_path, file_type) where file_type is 'pdf' or 'docx'

    Raises:
        ValueError: If meeting has no committed actions
    """
    with get_db() as conn:
        meeting = conn.execute(
            "SELECT * FROM meetings WHERE id = ?", (meeting_id,)
        ).fetchone()
        if not meeting:
            raise ValueError(f"Meeting {meeting_id} not found")
        meeting = dict(meeting)

        # Get committed actions for this meeting
        actions = [dict(r) for r in conn.execute(
            """SELECT sa.*, p.canonical_id, p.code_section
               FROM subgroup_actions sa
               JOIN proposals p ON sa.proposal_uid = p.proposal_uid
               WHERE sa.source_file = ?
               ORDER BY p.canonical_id""",
            (f"web_portal/{meeting_id}",)
        ).fetchall()]

    if not actions:
        raise ValueError(f"No committed actions found for meeting {meeting_id}")

    # Generate the DOCX
    docx_bytes = generate_circform_docx(meeting, actions)

    out_dir = _ensure_dirs(meeting_id)
    safe_body = meeting["body"].replace(" ", "_").replace("/", "-")
    filename_stem = f"{safe_body}_CircForm_{meeting['meeting_date']}"

    # Try PDF conversion
    if _has_libreoffice():
        try:
            pdf_path = _docx_to_pdf(docx_bytes, out_dir, filename_stem)
            abs_path = str(pdf_path.resolve())
            logger.info(f"Generated circ form PDF for meeting {meeting_id}: {abs_path}")
            return abs_path, "pdf"
        except Exception as e:
            logger.warning(f"PDF conversion failed, falling back to DOCX: {e}")

    # Fallback: save as DOCX
    docx_path = out_dir / f"{filename_stem}.docx"
    docx_path.write_bytes(docx_bytes)
    abs_path = str(docx_path.resolve())
    logger.info(f"Generated circ form DOCX for meeting {meeting_id}: {abs_path}")
    return abs_path, "docx"
