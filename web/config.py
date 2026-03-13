"""Configuration for ICC Code Development Platform."""
from pathlib import Path
import os

# Database
DB_PATH = Path(os.environ.get(
    "IECC_DB_PATH",
    Path(__file__).parent.parent / "iecc.db"
))

# Server
HOST = "0.0.0.0"
PORT = int(os.environ.get("IECC_PORT", 8080))

# Application
APP_TITLE = "ICC Code Development Platform"
APP_VERSION = "0.1.0"

# Domain constants
TRACKS = ["commercial", "residential"]

PHASES = ["PUBLIC_INPUT", "CODE_PROPOSAL", "PUBLIC_COMMENT"]

RECOMMENDATIONS = [
    "Approved as Submitted",
    "Approved as Modified",
    "Approved as Modified (Further)",
    "Disapproved",
    "Withdrawn",
    "Do Not Process",
    "Postponed",
    "Reconsider",
]

# Meeting body names (how they appear in the meetings table)
COMMERCIAL_BODIES = [
    "Commercial Administration Subgroup",
    "Envelope and Embodied Energy Subgroup",
    "Commercial EPLR Subgroup",
    "Commercial HVACR and Water Heating Subgroup",
    "Commercial Modeling Subgroup",
    "Commercial Consensus Committee",
]
RESIDENTIAL_BODIES = [
    "Residential Administration Subgroup",
    "Residential Envelope Subgroup",
    "Residential EPLR Subgroup",
    "Residential HVAC Subgroup",
    "Residential Modeling Subgroup",
    "Residential Existing Building Subgroup",
    "Residential Consensus Committee",
]

# Short names for the create-meeting form
COMMERCIAL_SUBGROUPS = ["Admin", "Envelope", "EPLR", "HVACR", "Modeling", "Cost"]
RESIDENTIAL_SUBGROUPS = ["Admin", "Envelope", "EPLR", "HVAC", "Modeling", "Existing Building"]

SUBGROUPS_BY_TRACK = {
    "commercial": COMMERCIAL_SUBGROUPS,
    "residential": RESIDENTIAL_SUBGROUPS,
}

# Map meeting body names -> proposal current_subgroup values
# Commercial side matches 1:1, residential uses abbreviated names
BODY_TO_SUBGROUP = {
    # Commercial (these match directly)
    "Commercial Administration Subgroup": "Commercial Administration Subgroup",
    "Envelope and Embodied Energy Subgroup": "Envelope and Embodied Energy Subgroup",
    "Commercial EPLR Subgroup": "Commercial EPLR Subgroup",
    "Commercial HVACR and Water Heating Subgroup": "Commercial HVACR and Water Heating Subgroup",
    "Commercial Modeling Subgroup": "Commercial Modeling Subgroup",
    "Commercial Consensus Committee": "Commercial Consensus Committee",
    # Residential (meeting body -> proposal subgroup)
    # Note: DB has meetings under BOTH "Residential Administration Subgroup" AND
    # "Consistency and Administration (SG1)" — both map to the same proposal subgroup
    "Residential Administration Subgroup": "Consistency and Administration (SG1)",
    "Consistency and Administration (SG1)": "Consistency and Administration (SG1)",
    "Residential Envelope Subgroup": "Envelope (SG4)",
    "Residential EPLR Subgroup": "EPLR (SG3)",
    "Residential HVAC Subgroup": "HVACR (SG6)",
    "Residential Modeling Subgroup": "Modeling (SG2)",
    "Residential Existing Building Subgroup": "Existing Buildings (SG5)",
    "Residential Consensus Committee": "Residential Consensus Committee",
}


# Map proposal subgroup names -> SharePoint folder names
SUBGROUP_TO_SP_FOLDER = {
    "Consistency and Administration (SG1)": "Admin Subgroup",
    "Modeling (SG2)": "Modeling Subgroup",
    "EPLR (SG3)": "Residential EPLR",
    "Envelope (SG4)": "Envelope and Embodied Carbon Subgroup",
    "Existing Buildings (SG5)": "Residential Existing Buildings",
    "HVACR (SG6)": "HVAC & Water Heating",
}

# SharePoint configuration (from environment variables)
SP_TENANT_ID = os.environ.get("SP_TENANT_ID")
SP_CLIENT_ID = os.environ.get("SP_CLIENT_ID")
SP_CLIENT_SECRET = os.environ.get("SP_CLIENT_SECRET")
SP_SITE_HOST = "2023701800.sharepoint.com"
SP_SITE_PATH = "/sites/ICC-CS_AETECHNICALSERVICESGROUP"
SP_DOC_LIBRARY_PATH = (
    "Shared Documents/Committees/Cmtes-Public/Codes/Energy/"
    "Residential (RECDC)/Meeting Minutes & Agendas/2027 IECC/Residential Subgroups"
)
SP_ENABLED = bool(SP_TENANT_ID and SP_CLIENT_ID and SP_CLIENT_SECRET)

# Generated files directory — use a writable location
# On production (Windows), this will be inside the web/ folder
# In sandboxed environments, fall back to a temp directory
_web_dir = Path(__file__).parent
_default_gen_dir = _web_dir / "generated"
try:
    _default_gen_dir.mkdir(parents=True, exist_ok=True)
    (_default_gen_dir / ".test").touch()
    (_default_gen_dir / ".test").unlink()
except (PermissionError, OSError):
    import tempfile
    _default_gen_dir = Path(tempfile.gettempdir()) / "iecc_generated"
    _default_gen_dir.mkdir(parents=True, exist_ok=True)

GENERATED_DIR = _default_gen_dir
CIRCFORMS_DIR = GENERATED_DIR / "circforms"

# Approved circ forms — organized by subgroup/meeting for easy SharePoint upload
# Structure: {APPROVED_CIRCFORMS_DIR}/{subgroup_folder}/{YY-MM-DD Meeting}/filename.docx
# Default: OneDrive for Business sync folder → Power Automate picks up and uploads to SharePoint
_default_approved_dir = Path(os.path.expanduser(
    "~/OneDrive - International Code Council/IECC_Approved_CircForms"
))
if not _default_approved_dir.exists():
    _default_approved_dir = Path(__file__).parent.parent / "approved_circforms"
APPROVED_CIRCFORMS_DIR = Path(os.environ.get("IECC_APPROVED_DIR", _default_approved_dir))


def resolve_subgroup(body: str) -> str:
    """Convert a meeting body name to the proposal subgroup name used in the DB."""
    return BODY_TO_SUBGROUP.get(body, body)


def subgroup_to_sp_folder(subgroup: str) -> str:
    """Convert a proposal subgroup name to the SharePoint folder name."""
    return SUBGROUP_TO_SP_FOLDER.get(subgroup, subgroup)
