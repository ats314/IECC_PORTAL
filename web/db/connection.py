"""SQLite connection manager with WAL mode enforcement and schema initialization."""
import sqlite3
import logging
from pathlib import Path
from contextlib import contextmanager
from config import DB_PATH

logger = logging.getLogger(__name__)


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Get a SQLite connection with WAL mode and row factory."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db():
    """Context manager for database connections. Auto-commits on success, rolls back on error."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def checkpoint():
    """Run WAL checkpoint to flush writes to main DB file."""
    conn = get_connection()
    try:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    finally:
        conn.close()


def init_schema():
    """Ensure all tables, views, columns, and indexes exist.

    Called once at app startup. All DDL is idempotent — safe to run
    against an already-initialized database.
    """
    conn = get_connection()
    created = []
    try:
        # --- Web-app operational tables ---
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sg_action_staging (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meeting_id INTEGER NOT NULL,
                proposal_uid TEXT NOT NULL,
                canonical_id TEXT NOT NULL,
                subgroup TEXT NOT NULL,
                action_date TEXT NOT NULL,
                recommendation TEXT NOT NULL,
                vote_for INTEGER,
                vote_against INTEGER,
                vote_not_voting INTEGER,
                reason TEXT,
                modification_text TEXT,
                moved_by TEXT,
                seconded_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(meeting_id, proposal_uid)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS meeting_agenda_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meeting_id INTEGER NOT NULL,
                proposal_uid TEXT NOT NULL,
                sort_order INTEGER NOT NULL DEFAULT 0,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(meeting_id, proposal_uid),
                FOREIGN KEY (meeting_id) REFERENCES meetings(id),
                FOREIGN KEY (proposal_uid) REFERENCES proposals(proposal_uid)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS circ_forms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meeting_id INTEGER NOT NULL,
                track TEXT NOT NULL,
                subgroup TEXT NOT NULL,
                body TEXT NOT NULL,
                generated_at TEXT DEFAULT (datetime('now')),
                pdf_path TEXT,
                status TEXT NOT NULL DEFAULT 'pending_review',
                reviewed_by TEXT,
                reviewed_at TEXT,
                rejection_reason TEXT,
                sharepoint_url TEXT,
                FOREIGN KEY (meeting_id) REFERENCES meetings(id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS subgroup_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                body TEXT NOT NULL,
                first_name TEXT,
                last_name TEXT,
                display_name TEXT NOT NULL,
                email TEXT,
                role TEXT DEFAULT 'member'
            )
        """)

        # --- Content tables from migration 002 ---
        conn.execute("""
            CREATE TABLE IF NOT EXISTS proposal_text (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proposal_uid TEXT NOT NULL REFERENCES proposals(proposal_uid),
                source_type TEXT NOT NULL CHECK(source_type IN (
                    'cdpaccess_docx', 'monograph_pdf', 'manual_entry', 'transcript'
                )),
                source_path TEXT,
                proposal_html TEXT,
                proposal_plain TEXT,
                reason_text TEXT,
                cost_impact_text TEXT,
                code_section_text TEXT,
                extracted_at TEXT NOT NULL DEFAULT (datetime('now')),
                verified INTEGER DEFAULT 0,
                verified_by TEXT,
                verified_at TEXT,
                notes TEXT,
                UNIQUE(proposal_uid, source_type)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS modifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proposal_uid TEXT NOT NULL REFERENCES proposals(proposal_uid),
                track TEXT NOT NULL,
                submitted_by TEXT,
                submitted_date TEXT,
                source_path TEXT,
                modification_html TEXT,
                modification_plain TEXT,
                reason_text TEXT,
                status TEXT NOT NULL DEFAULT 'received' CHECK(status IN (
                    'received', 'posted_to_sharepoint', 'approved_by_committee',
                    'rejected_by_committee', 'further_modified', 'superseded', 'withdrawn'
                )),
                meeting_id INTEGER REFERENCES meetings(id),
                parent_modification_id INTEGER REFERENCES modifications(id),
                extracted_at TEXT DEFAULT (datetime('now')),
                notes TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS proposal_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proposal_uid_a TEXT NOT NULL REFERENCES proposals(proposal_uid),
                proposal_uid_b TEXT NOT NULL REFERENCES proposals(proposal_uid),
                link_type TEXT NOT NULL CHECK(link_type IN (
                    'combined_consideration', 'superseded_by', 'companion',
                    'depends_on', 'conflicts_with', 'same_section'
                )),
                created_by TEXT DEFAULT 'manual',
                notes TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                UNIQUE(proposal_uid_a, proposal_uid_b, link_type)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proposal_uid TEXT REFERENCES proposals(proposal_uid),
                meeting_id INTEGER REFERENCES meetings(id),
                track TEXT,
                doc_type TEXT NOT NULL CHECK(doc_type IN (
                    'proposal_docx', 'modification_docx', 'pnnl_analysis',
                    'circ_form_docx', 'circ_form_pdf', 'transcript_docx',
                    'transcript_vtt', 'agenda_pdf', 'agenda_docx',
                    'monograph_pdf', 'pcd_pdf', 'proponent_comment', 'other'
                )),
                file_name TEXT,
                file_path TEXT NOT NULL,
                file_size INTEGER,
                file_hash TEXT,
                discovered_at TEXT DEFAULT (datetime('now')),
                processed INTEGER DEFAULT 0,
                processed_at TEXT,
                notes TEXT,
                UNIQUE(file_path)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS meeting_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meeting_id INTEGER NOT NULL REFERENCES meetings(id),
                proposal_uid TEXT REFERENCES proposals(proposal_uid),
                event_type TEXT NOT NULL CHECK(event_type IN (
                    'motion', 'second', 'vote', 'amendment',
                    'further_modification', 'withdrawal', 'discussion',
                    'roll_call', 'agenda_change', 'combined_consideration',
                    'reason_statement', 'procedural'
                )),
                speaker TEXT,
                content TEXT,
                vote_for INTEGER,
                vote_against INTEGER,
                vote_abstain INTEGER,
                vote_outcome TEXT,
                timestamp_seconds INTEGER,
                source TEXT CHECK(source IN ('transcript_docx', 'transcript_vtt', 'manual', 'llm_extraction')),
                confidence REAL,
                verified INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)

        # --- Column additions (idempotent via try/except) ---
        for table, column, col_type in [
            ("subgroup_actions", "moved_by", "TEXT"),
            ("subgroup_actions", "seconded_by", "TEXT"),
            ("meetings", "transcript_path", "TEXT"),
            ("meetings", "recording_url", "TEXT"),
        ]:
            try:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
                created.append(f"column {table}.{column}")
            except sqlite3.OperationalError:
                pass  # Column already exists

        # --- Indexes from migration 002 ---
        conn.execute("CREATE INDEX IF NOT EXISTS idx_proposal_text_uid ON proposal_text(proposal_uid)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_modifications_uid ON modifications(proposal_uid)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_modifications_meeting ON modifications(meeting_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_proposal_links_a ON proposal_links(proposal_uid_a)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_proposal_links_b ON proposal_links(proposal_uid_b)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_uid ON documents(proposal_uid)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_meeting ON documents(meeting_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(doc_type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_processed ON documents(processed)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_meeting_events_meeting ON meeting_events(meeting_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_meeting_events_proposal ON meeting_events(proposal_uid)")

        # --- Fix v_current_status view ---
        # Build scripts create this with 'computed_status' but web app expects 'status'
        _fix_current_status_view(conn)

        conn.commit()
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")

        if created:
            logger.info(f"init_schema: created {', '.join(created)}")
        logger.info("init_schema: all tables, views, and indexes verified")

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _fix_current_status_view(conn):
    """Ensure v_current_status exists with 'status' column (not 'computed_status').

    The build scripts created the view with 'computed_status' as the alias,
    but web/db/queries.py references 'v.status' in 9 queries. This function
    drops and recreates the view with the correct alias if needed.
    """
    # Check if view exists and has the wrong column name
    view_info = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='view' AND name='v_current_status'"
    ).fetchone()

    if view_info:
        sql = view_info[0] or ""
        if "AS status" in sql and "computed_status" not in sql:
            return  # Already correct
        # Drop the old view with wrong column name
        conn.execute("DROP VIEW IF EXISTS v_current_status")
        logger.info("init_schema: recreating v_current_status (fixing column alias)")

    # Check that base tables exist before creating the view
    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    if "proposals" not in tables:
        logger.warning("init_schema: 'proposals' table not found — skipping v_current_status view")
        return

    conn.execute("""
        CREATE VIEW IF NOT EXISTS v_current_status AS
        SELECT
            p.proposal_uid,
            p.canonical_id,
            p.prefix,
            p.cycle,
            p.phase,
            p.part,
            p.proponent,
            p.proponent_email,
            p.code_section,
            p.initial_subgroup,
            p.current_subgroup,
            p.cdpaccess_id,
            p.cdpaccess_url,
            p.withdrawn,
            sa.subgroup AS sg_subgroup,
            sa.recommendation AS sg_recommendation,
            sa.action_date AS sg_action_date,
            sa.vote_for AS sg_vote_for,
            sa.vote_against AS sg_vote_against,
            sa.vote_not_voting AS sg_vote_not_voting,
            sa.reason AS sg_reason,
            sa.modification_text AS sg_modification,
            ca.recommendation AS consensus_recommendation,
            ca.action_date AS consensus_date,
            ca.vote_for AS cons_vote_for,
            ca.vote_against AS cons_vote_against,
            ca.vote_not_voting AS cons_vote_not_voting,
            ca.reason AS cons_reason,
            ca.modification_text AS cons_modification,
            ca.moved_by,
            ca.seconded_by,
            CASE
                WHEN p.withdrawn = 1 THEN 'WITHDRAWN'
                WHEN ca.recommendation IS NOT NULL THEN 'DECIDED'
                WHEN sa.recommendation IS NOT NULL THEN 'PENDING_CONSENSUS'
                ELSE 'PENDING'
            END AS status
        FROM proposals p
        LEFT JOIN (
            SELECT *, ROW_NUMBER() OVER (
                PARTITION BY proposal_uid ORDER BY action_date DESC, id DESC
            ) AS rn
            FROM subgroup_actions
        ) sa ON p.proposal_uid = sa.proposal_uid AND sa.rn = 1
        LEFT JOIN (
            SELECT *, ROW_NUMBER() OVER (
                PARTITION BY proposal_uid ORDER BY sequence DESC, id DESC
            ) AS rn
            FROM consensus_actions WHERE is_final = 1
        ) ca ON p.proposal_uid = ca.proposal_uid AND ca.rn = 1
    """)
