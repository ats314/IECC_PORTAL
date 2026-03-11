#!/usr/bin/env python3
"""
iecc_preflight.py — Session start summary for new agents.

Usage:
    python3 iecc_preflight.py

Prints a compact briefing: DB state, pending proposals, upcoming meetings,
open DQ flags, and recent changes (if a snapshot exists).

Uses unified iecc.db with track-based filtering (commercial / residential).
"""

import sqlite3
import os
import sys
import json
import glob
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DB_PATH = os.path.join(PROJECT_ROOT, 'iecc.db')

TRACKS = {
    'Commercial': 'commercial',
    'Residential': 'residential',
}


def cleanup_vm_artifacts():
    """Remove .fuse_hidden* files and other VM junk from the workspace.
    These accumulate every session from the FUSE mount layer."""
    import fnmatch
    cleaned = 0
    for f in os.listdir(PROJECT_ROOT):
        if fnmatch.fnmatch(f, '.fuse_hidden*') or f == '__pycache__' or fnmatch.fnmatch(f, '~$*'):
            path = os.path.join(PROJECT_ROOT, f)
            try:
                if os.path.isdir(path):
                    import shutil
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                cleaned += 1
            except OSError:
                pass
    if cleaned:
        print(f"\n  🧹 Cleaned {cleaned} VM artifact(s) (.fuse_hidden, __pycache__, ~$ temp files)")


def repair_db_if_needed():
    """Auto-detect and fix DB corruption from stale journal/WAL files.

    This handles the recurring issue where the VM shuts down mid-write,
    leaving a stale -journal or -wal file that corrupts reads on next mount.
    Fix: dump to SQL from a clean read, delete the corrupt file + journals,
    rebuild fresh, set WAL mode.
    """
    journal = DB_PATH + '-journal'
    wal = DB_PATH + '-wal'
    shm = DB_PATH + '-shm'

    # Quick health check
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute('SELECT COUNT(*) FROM proposals')
        mode = conn.execute('PRAGMA journal_mode').fetchone()[0]
        conn.close()
        # If not WAL, upgrade silently
        if mode != 'wal':
            conn = sqlite3.connect(DB_PATH)
            conn.execute('PRAGMA journal_mode=WAL')
            conn.close()
        return  # DB is fine
    except Exception as e:
        print(f"\n  ⚠️  DB CORRUPTION DETECTED: {e}")
        print(f"  Auto-repairing...")

    # Try reading with immutable flag (ignores journal)
    try:
        uri = f"file:{DB_PATH}?immutable=1"
        conn = sqlite3.connect(uri, uri=True)
        dump = list(conn.iterdump())
        conn.close()
        print(f"  Extracted {len(dump)} SQL statements from corrupt DB")
    except Exception as e2:
        print(f"  FATAL: Cannot read DB even in immutable mode: {e2}")
        print(f"  Manual recovery needed. Check for backups in .snapshots/")
        sys.exit(1)

    # Remove corrupt files
    for f in [DB_PATH, journal, wal, shm]:
        if os.path.exists(f):
            try:
                os.remove(f)
            except OSError:
                pass

    # Rebuild
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA journal_mode=WAL')
    for stmt in dump:
        try:
            conn.execute(stmt)
        except Exception:
            pass
    conn.commit()

    # Verify
    count = conn.execute('SELECT COUNT(*) FROM proposals').fetchone()[0]
    integrity = conn.execute('PRAGMA integrity_check').fetchone()[0]
    conn.close()

    if integrity == 'ok':
        print(f"  ✅ DB REPAIRED: {count} proposals, integrity OK, WAL mode set")
    else:
        print(f"  ⚠️  DB rebuilt but integrity check reports: {integrity}")
        sys.exit(1)


def get_conn():
    """Open unified database connection."""
    if not os.path.exists(DB_PATH):
        print(f"ERROR: {DB_PATH} not found.")
        sys.exit(1)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def query(sql, params=()):
    """Execute query and return all rows."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def scalar(sql, params=()):
    """Execute query and return single scalar value."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params)
    val = cur.fetchone()[0]
    conn.close()
    return val


def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def db_summary(label, track):
    """Print status summary for one track."""
    total = scalar('SELECT COUNT(*) FROM proposals WHERE track=?', (track,))
    status_rows = query(
        'SELECT status, COUNT(*) as cnt FROM v_current_status WHERE track=? GROUP BY status ORDER BY cnt DESC',
        (track,)
    )
    ca_total = scalar('SELECT COUNT(*) FROM consensus_actions WHERE track=?', (track,))
    ca_final = scalar('SELECT COUNT(*) FROM consensus_actions WHERE track=? AND is_final=1', (track,))
    sa_total = scalar('SELECT COUNT(*) FROM subgroup_actions WHERE track=?', (track,))
    dq_total = scalar('SELECT COUNT(*) FROM data_quality_flags WHERE track=?', (track,))
    dq_open = scalar('SELECT COUNT(*) FROM data_quality_flags WHERE track=? AND needs_review=1', (track,))

    print(f"\n  {label}: {total} proposals")
    for r in status_rows:
        print(f"    {r['status']}: {r['cnt']}")
    print(f"    CA: {ca_total} ({ca_final} final), SA: {sa_total}, DQ: {dq_total} ({dq_open} open)")


def pending_proposals(label, track):
    """List all pending proposals."""
    rows = query("""
        SELECT canonical_id, proponent, current_subgroup,
               sg_recommendation, sg_date
        FROM v_current_status
        WHERE track=? AND status='Pending'
        ORDER BY current_subgroup, canonical_id
    """, (track,))
    if not rows:
        print(f"\n  {label}: No pending proposals.")
        return
    print(f"\n  {label} — {len(rows)} pending:")
    current_sg = None
    for r in rows:
        sg = r['current_subgroup'] or 'Unassigned'
        if sg != current_sg:
            current_sg = sg
            print(f"    [{sg}]")
        sg_note = f" (SG: {r['sg_recommendation']})" if r['sg_recommendation'] else " (no SG action)"
        print(f"      {r['canonical_id']} — {r['proponent'] or '?'}{sg_note}")


def upcoming_meetings(label, track):
    """Show next 5 scheduled meetings."""
    rows = query("""
        SELECT meeting_date, body, notes
        FROM meetings
        WHERE track=?
          AND meeting_date >= date('now')
          AND (status='SCHEDULED' OR status IS NULL)
        ORDER BY meeting_date
        LIMIT 5
    """, (track,))
    if not rows:
        print(f"\n  {label}: No scheduled meetings.")
        return
    print(f"\n  {label} — upcoming meetings:")
    for r in rows:
        notes = f" — {r['notes']}" if r['notes'] else ""
        print(f"    {r['meeting_date']}  {r['body']}{notes}")


def open_dq_flags(label, track):
    """Summarize open DQ flags by type."""
    rows = query("""
        SELECT flag_type, COUNT(*) as cnt
        FROM data_quality_flags
        WHERE track=? AND needs_review=1
        GROUP BY flag_type
        ORDER BY cnt DESC
    """, (track,))
    if not rows:
        print(f"\n  {label}: No open DQ flags.")
        return
    total = sum(r['cnt'] for r in rows)
    print(f"\n  {label} — {total} open DQ flags:")
    for r in rows:
        print(f"    {r['flag_type']}: {r['cnt']}")


def recent_snapshot():
    """Find and summarize most recent snapshot."""
    snap_dir = os.path.join(PROJECT_ROOT, '.snapshots')
    if not os.path.isdir(snap_dir):
        print("\n  No snapshots directory found.")
        return

    snaps = sorted(glob.glob(os.path.join(snap_dir, 'snap_*.json')), reverse=True)
    if not snaps:
        print("\n  No snapshots found.")
        return

    latest = snaps[0]
    basename = os.path.basename(latest)
    # Parse timestamp from filename: snap_YYYYMMDD_HHMMSS.json
    try:
        ts = basename.replace('snap_', '').replace('.json', '')
        dt = datetime.strptime(ts, '%Y%m%d_%H%M%S')
        print(f"\n  Latest snapshot: {basename} ({dt.strftime('%Y-%m-%d %H:%M')})")
    except ValueError:
        print(f"\n  Latest snapshot: {basename}")

    if len(snaps) >= 2:
        print(f"  Total snapshots on disk: {len(snaps)}")
        print(f"  Run `python3 iecc_snapshot.py compare` to see changes since last save.")


def doc_verification():
    """Run quick verification check."""
    # Import the verify module
    verify_path = os.path.join(SCRIPT_DIR, 'iecc_verify.py')
    if not os.path.exists(verify_path):
        print("\n  iecc_verify.py not found — skipping doc check.")
        return

    import importlib.util
    spec = importlib.util.spec_from_file_location("iecc_verify", verify_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    truth = mod.get_db_truth()
    errors = mod.check_docs(truth)
    if errors:
        print(f"\n  ⚠️  DOC VERIFICATION: {len(errors)} issues found!")
        for e in errors[:5]:
            print(f"    {e}")
        if len(errors) > 5:
            print(f"    ... and {len(errors)-5} more. Run `python3 iecc_verify.py` for full list.")
    else:
        print(f"\n  ✅ DOC VERIFICATION: All docs match DB. Zero discrepancies.")


def main():
    print_header("IECC 2027 PREFLIGHT BRIEFING")
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # Check DB exists
    if not os.path.exists(DB_PATH):
        print(f"\nERROR: {DB_PATH} not found.")
        sys.exit(1)

    # Clean VM junk first
    cleanup_vm_artifacts()

    # Auto-repair if corrupted
    repair_db_if_needed()

    # DB Summaries
    print_header("DATABASE STATE")
    for label, track in TRACKS.items():
        db_summary(label, track)

    # Pending
    print_header("PENDING PROPOSALS")
    for label, track in TRACKS.items():
        pending_proposals(label, track)

    # Upcoming meetings
    print_header("UPCOMING MEETINGS")
    for label, track in TRACKS.items():
        upcoming_meetings(label, track)

    # Open DQ
    print_header("OPEN DATA QUALITY FLAGS")
    for label, track in TRACKS.items():
        open_dq_flags(label, track)

    # Snapshot
    print_header("CHANGE TRACKING")
    recent_snapshot()

    # Doc verification
    print_header("DOCUMENTATION CHECK")
    doc_verification()

    print(f"\n{'='*60}")
    print("  PREFLIGHT COMPLETE — Read CLAUDE.md, AGENT_GUIDE.md,")
    print("  PROJECT_MEMORY.md, then confirm: 'Ready to work.'")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
