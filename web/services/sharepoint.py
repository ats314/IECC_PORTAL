"""SharePoint Graph API integration for uploading circulation form PDFs.

This service is dormant by default — it only activates when Azure AD credentials
are configured via environment variables (SP_TENANT_ID, SP_CLIENT_ID, SP_CLIENT_SECRET).

Upload target:
  Shared Documents/.../Residential Subgroups/{subgroup folder}/{YY-MM-DD Meeting}/

Requires: pip install msal requests
"""
import os
import logging
from pathlib import Path
from datetime import datetime

import config

logger = logging.getLogger(__name__)

# Only import msal if SharePoint is enabled
_msal_app = None


def _get_msal_app():
    """Lazy-initialize the MSAL confidential client."""
    global _msal_app
    if _msal_app is None:
        try:
            from msal import ConfidentialClientApplication
            _msal_app = ConfidentialClientApplication(
                client_id=config.SP_CLIENT_ID,
                authority=f"https://login.microsoftonline.com/{config.SP_TENANT_ID}",
                client_credential=config.SP_CLIENT_SECRET,
            )
        except ImportError:
            raise RuntimeError(
                "msal package not installed. Run: pip install msal --break-system-packages"
            )
    return _msal_app


def _get_access_token() -> str:
    """Acquire an OAuth2 access token using client credentials flow."""
    app = _get_msal_app()
    result = app.acquire_token_for_client(
        scopes=["https://graph.microsoft.com/.default"]
    )
    if "access_token" not in result:
        error = result.get("error_description", result.get("error", "Unknown error"))
        raise RuntimeError(f"Failed to acquire token: {error}")
    return result["access_token"]


def _build_upload_path(form: dict) -> str:
    """Build the SharePoint folder path for a circ form.

    Target: {SP_DOC_LIBRARY_PATH}/{subgroup folder}/{YY-MM-DD Meeting}/

    Args:
        form: dict from circ_forms table with keys: subgroup, body, meeting_date

    Returns:
        The full path within the document library
    """
    subgroup = form["subgroup"]
    sp_folder = config.subgroup_to_sp_folder(subgroup)

    # Meeting date format in DB: 2026-03-03 → SharePoint folder: 26-03-03 Meeting
    meeting_date = form["meeting_date"]
    try:
        dt = datetime.strptime(meeting_date, "%Y-%m-%d")
        folder_name = f"{dt.strftime('%y-%m-%d')} Meeting"
    except (ValueError, TypeError):
        folder_name = f"{meeting_date} Meeting"

    return f"{config.SP_DOC_LIBRARY_PATH}/{sp_folder}/{folder_name}"


def upload_circform_to_sharepoint(form: dict) -> str | None:
    """Upload a circ form PDF to SharePoint.

    Args:
        form: dict from circ_forms table (needs: pdf_path, subgroup, body, meeting_date)

    Returns:
        The SharePoint web URL of the uploaded file, or None on failure
    """
    if not config.SP_ENABLED:
        logger.warning("SharePoint upload skipped: credentials not configured")
        return None

    import requests

    # Read the PDF file
    pdf_path = Path(form["pdf_path"])
    if not pdf_path.is_absolute():
        pdf_path = Path(__file__).parent.parent / pdf_path
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    pdf_bytes = pdf_path.read_bytes()
    filename = pdf_path.name

    # Get access token
    token = _get_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/octet-stream",
    }

    # Get site ID
    site_url = (
        f"https://graph.microsoft.com/v1.0/sites/"
        f"{config.SP_SITE_HOST}:{config.SP_SITE_PATH}"
    )
    resp = requests.get(site_url, headers={"Authorization": f"Bearer {token}"})
    resp.raise_for_status()
    site_id = resp.json()["id"]

    # Build the upload path
    folder_path = _build_upload_path(form)

    # Upload via PUT — Graph API auto-creates folders
    upload_url = (
        f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive/root:/"
        f"{folder_path}/{filename}:/content"
    )

    logger.info(f"Uploading {filename} to SharePoint: {folder_path}/")
    resp = requests.put(upload_url, data=pdf_bytes, headers=headers, timeout=60)
    resp.raise_for_status()

    result = resp.json()
    web_url = result.get("webUrl", "")
    logger.info(f"Upload successful: {web_url}")
    return web_url
