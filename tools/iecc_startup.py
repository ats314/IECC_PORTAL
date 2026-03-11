#!/usr/bin/env python3
"""IECC Project Startup — Full Knowledge Acquisition + System Verification.

Run this at the START of every new session. It:
1. Reads and summarizes all project documentation
2. Verifies database health (preflight)
3. Starts the web server and tests key routes
4. Reports a comprehensive status summary

Usage:
    python3 iecc_startup.py          # Full startup (docs + DB + server test)
    python3 iecc_startup.py --quick  # Docs + DB only (no server test)
"""

import sqlite3
import os
import sys
import json
import subprocess
import time
import signal
from pathlib import Path

# ============================================================
# CONFIG
# ============================================================
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "iecc.db"
WEB_DIR = BASE_DIR / "web"
PORT = 8080

# Documentation files to read (in order of priority)
DOCS = [
    ("CLAUDE.md", "Quick start, hard rules, project structure"),
    ("docs/AGENT_GUIDE.md", "Schema, domain knowledge, naming conventions, document chain"),
    ("docs/PROJECT_MEMORY.md", "Session history, decisions, known issues"),
    ("docs/QUERY_COOKBOOK.md", "Ready SQL queries"),
    ("docs/PORTAL_ROADMAP.md", "Three-phase portal plan (Phase 1 mostly complete)"),
    ("web/LLM_HANDOFF.md", "Web app handoff — rules, patterns, what to build next"),
    ("web/README.md", "Web app setup, file structure"),
    ("web/ARCHITECTURE.md", "Request lifecycle, auth system, template inheritance"),
    ("web/DEVELOPMENT.md", "What's built, what's NOT built, priorities"),
]

# Server routes to verify
TEST_ROUTES = [
    ("/health", None, "Health check"),
    ("/login", None, "Login page"),
    ("/", "icc_user=alex.smith", "Secretariat dashboard"),
    ("/proposals", "icc_user=alex.smith", "Proposals list"),
    ("/meetings", "icc_user=alex.smith", "Meetings list"),
    ("/circ-forms", "icc_user=alex.smith", "Circ forms"),
    ("/home", "icc_user=brian.shanks", "Chair home"),
]

# ============================================================
# COLORS
# ============================================================
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"

def ok(msg):
    print(f"  {GREEN}✓{RESET} {msg}")

def fail(msg):
    print(f"  {RED}✗{RESET} {msg}")

def warn(msg):
    print(f"  {YELLOW}⚠{RESET} {msg}")

def header(msg):
    print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
    print(f"{BOLD}{BLUE}  {msg}{RESET}")
    print(f"{BOLD}{BLUE}{'='*60}{RESET}")


# ============================================================
# PHASE 1: DOCUMENTATION INVENTORY
# ============================================================
def check_docs():
    header("PHASE 1: Documentation Inventory")
    total_lines = 0
    missing = []
    found = []

    for doc_file, desc in DOCS:
        path = BASE_DIR / doc_file
        if path.exists():
            lines = len(path.read_text(encoding="utf-8").splitlines())
            total_lines += lines
            ok(f"{doc_file} ({lines} lines) — {desc}")
            found.append((doc_file, lines))
        else:
            fail(f"{doc_file} — MISSING!")
            missing.append(doc_file)

    print(f"\n  Total documentation: {total_lines} lines across {len(found)} files")
    if missing:
        fail(f"Missing docs: {', '.join(missing)}")
    else:
        ok("All documentation files present")

    return len(missing) == 0


# ============================================================
# PHASE 2: DATABASE HEALTH
# ============================================================
def check_db():
    header("PHASE 2: Database Health")

    if not DB_PATH.exists():
        fail(f"Database not found: {DB_PATH}")
        return False

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    errors = []

    # Basic counts
    proposals = conn.execute("SELECT COUNT(*) as c FROM proposals").fetchone()["c"]
    res = conn.execute("SELECT COUNT(*) as c FROM proposals WHERE track='residential'").fetchone()["c"]
    com = conn.execute("SELECT COUNT(*) as c FROM proposals WHERE track='commercial'").fetchone()["c"]
    ok(f"Proposals: {proposals} total ({res} residential, {com} commercial)")

    # Status breakdown (computed via v_current_status view)
    try:
        for status in ["Pending", "Decided", "Withdrawn"]:
            count = conn.execute("SELECT COUNT(*) as c FROM v_current_status WHERE status=?", (status,)).fetchone()["c"]
            ok(f"  {status}: {count}")
    except Exception:
        # Fallback: use withdrawn column directly
        withdrawn = conn.execute("SELECT COUNT(*) as c FROM proposals WHERE withdrawn=1").fetchone()["c"]
        ok(f"  Withdrawn: {withdrawn}")
        ok(f"  Active: {proposals - withdrawn}")

    # Subgroup actions
    sa_total = conn.execute("SELECT COUNT(*) as c FROM subgroup_actions").fetchone()["c"]
    sa_res = conn.execute("SELECT COUNT(*) as c FROM subgroup_actions WHERE track='residential'").fetchone()["c"]
    sa_com = conn.execute("SELECT COUNT(*) as c FROM subgroup_actions WHERE track='commercial'").fetchone()["c"]
    ok(f"Subgroup actions: {sa_total} ({sa_res} residential, {sa_com} commercial)")

    # Consensus actions
    ca_total = conn.execute("SELECT COUNT(*) as c FROM consensus_actions").fetchone()["c"]
    ok(f"Consensus actions: {ca_total}")

    # Meetings
    meetings = conn.execute("SELECT COUNT(*) as c FROM meetings").fetchone()["c"]
    scheduled = conn.execute("SELECT COUNT(*) as c FROM meetings WHERE status='SCHEDULED'").fetchone()["c"]
    completed = conn.execute("SELECT COUNT(*) as c FROM meetings WHERE status='COMPLETED'").fetchone()["c"]
    ok(f"Meetings: {meetings} total ({scheduled} scheduled, {completed} completed)")

    # Circ forms
    try:
        cf = conn.execute("SELECT COUNT(*) as c FROM circ_forms").fetchone()["c"]
        cf_pending = conn.execute("SELECT COUNT(*) as c FROM circ_forms WHERE status='pending_review'").fetchone()["c"]
        ok(f"Circ forms: {cf} total ({cf_pending} pending review)")
    except Exception:
        warn("circ_forms table not found (may need creation)")

    # Staging tables
    try:
        staged = conn.execute("SELECT COUNT(*) as c FROM sg_action_staging").fetchone()["c"]
        if staged > 0:
            warn(f"Staged actions: {staged} (meetings in progress)")
        else:
            ok("No staged actions (clean state)")
    except Exception:
        ok("sg_action_staging table not yet created (created on first portal use)")

    # Data quality flags
    try:
        dq = conn.execute("SELECT COUNT(*) as c FROM data_quality_flags WHERE needs_review=1").fetchone()["c"]
        if dq > 0:
            warn(f"Unresolved data quality flags: {dq}")
        else:
            ok("No unresolved data quality flags")
    except Exception:
        pass

    # WAL mode check
    journal = conn.execute("PRAGMA journal_mode").fetchone()[0]
    if journal == "wal":
        ok("WAL mode enabled")
    else:
        warn(f"Journal mode: {journal} (expected 'wal')")

    conn.close()
    return len(errors) == 0


# ============================================================
# PHASE 2B: DB-vs-REALITY CROSS-CHECK
# ============================================================
def cross_check_db():
    """Catch stale data: past-date scheduled meetings, orphaned staging, etc."""
    header("PHASE 2B: DB Cross-Check (stale data detection)")

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    issues = []

    from datetime import date
    today = date.today().isoformat()

    # 1. Past-date SCHEDULED meetings (should be COMPLETED or CANCELLED)
    stale_meetings = conn.execute(
        "SELECT id, meeting_date, body, track FROM meetings "
        "WHERE status='SCHEDULED' AND meeting_date < ?", (today,)
    ).fetchall()
    if stale_meetings:
        for m in stale_meetings:
            fail(f"Past-date SCHEDULED meeting: id={m['id']} {m['meeting_date']} "
                 f"{m['body']} ({m['track']}) — should be COMPLETED or CANCELLED")
            issues.append(f"meeting {m['id']}")
    else:
        ok("No past-date SCHEDULED meetings")

    # 2. Orphaned staging data (staging rows for meetings that are COMPLETED or don't exist)
    orphan_staging = conn.execute(
        "SELECT s.meeting_id, COUNT(*) as cnt FROM sg_action_staging s "
        "LEFT JOIN meetings m ON s.meeting_id = m.id "
        "WHERE m.id IS NULL OR m.status != 'SCHEDULED' "
        "GROUP BY s.meeting_id"
    ).fetchall()
    if orphan_staging:
        for row in orphan_staging:
            warn(f"Orphaned staging data: {row['cnt']} rows for meeting_id={row['meeting_id']}")
            issues.append(f"staging for meeting {row['meeting_id']}")
    else:
        ok("No orphaned staging data")

    # 3. Open DQ flags summary
    dq_open = conn.execute(
        "SELECT flag_type, COUNT(*) as cnt FROM data_quality_flags "
        "WHERE needs_review=1 GROUP BY flag_type"
    ).fetchall()
    if dq_open:
        for row in dq_open:
            warn(f"Open DQ: {row['cnt']}x {row['flag_type']}")
    else:
        ok("No open data quality flags")

    # 4. Proposals with SG action but no consensus action and not withdrawn (ready for consensus)
    ready = conn.execute(
        "SELECT COUNT(*) as c FROM v_current_status WHERE status='Pending' "
        "AND sg_recommendation IS NOT NULL"
    ).fetchone()["c"]
    if ready > 0:
        ok(f"Proposals ready for consensus (pending + have SG action): {ready}")

    # 5. Next upcoming meetings
    upcoming = conn.execute(
        "SELECT meeting_date, body, track FROM meetings "
        "WHERE status='SCHEDULED' AND meeting_date >= ? "
        "ORDER BY meeting_date LIMIT 5", (today,)
    ).fetchall()
    if upcoming:
        print(f"\n  {BLUE}Upcoming meetings:{RESET}")
        for m in upcoming:
            print(f"    {m['meeting_date']} — {m['body']} ({m['track']})")
    else:
        warn("No upcoming SCHEDULED meetings found")

    conn.close()

    if issues:
        warn(f"Cross-check found {len(issues)} issue(s) — resolve before doing work")
    else:
        ok("Cross-check passed — DB state is clean")

    return len(issues) == 0


# ============================================================
# PHASE 3: SERVER VERIFICATION
# ============================================================
def check_server():
    header("PHASE 3: Server Verification")

    # Check if server is already running
    try:
        import urllib.request
        urllib.request.urlopen(f"http://localhost:{PORT}/health", timeout=2)
        ok(f"Server already running on port {PORT}")
        return test_routes(already_running=True)
    except Exception:
        pass

    # Start server
    print(f"  Starting server on port {PORT}...")
    main_py = WEB_DIR / "main.py"
    if not main_py.exists():
        fail(f"web/main.py not found")
        return False

    proc = subprocess.Popen(
        [sys.executable, str(main_py)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(WEB_DIR),
    )

    # Wait for startup
    import urllib.request
    started = False
    for i in range(15):
        time.sleep(1)
        try:
            resp = urllib.request.urlopen(f"http://localhost:{PORT}/health", timeout=2)
            data = json.loads(resp.read())
            if data.get("status") == "ok":
                ok(f"Server started (PID {proc.pid})")
                started = True
                break
        except Exception:
            pass

    if not started:
        fail("Server failed to start within 15 seconds")
        proc.terminate()
        stderr = proc.stderr.read().decode()[:500]
        if stderr:
            print(f"    stderr: {stderr}")
        return False

    # Test routes
    success = test_routes(already_running=False)

    # Shut down
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
    ok("Server shut down cleanly")

    return success


def test_routes(already_running=False):
    import urllib.request
    all_ok = True

    for route, cookie, desc in TEST_ROUTES:
        try:
            req = urllib.request.Request(f"http://localhost:{PORT}{route}")
            if cookie:
                req.add_header("Cookie", cookie)
            resp = urllib.request.urlopen(req, timeout=5)
            code = resp.getcode()
            length = len(resp.read())
            if code == 200 and length > 50:
                ok(f"{route} → {code} ({length:,} bytes) — {desc}")
            else:
                warn(f"{route} → {code} ({length} bytes) — {desc}")
        except Exception as e:
            fail(f"{route} → {e} — {desc}")
            all_ok = False

    return all_ok


# ============================================================
# PHASE 4: SUMMARY
# ============================================================
def print_summary(docs_ok, db_ok, crosscheck_ok, server_ok, quick_mode):
    header("STARTUP SUMMARY")

    if docs_ok:
        ok("Documentation: All files present and readable")
    else:
        fail("Documentation: Missing files — check output above")

    if db_ok:
        ok("Database: Healthy")
    else:
        fail("Database: Issues detected — check output above")

    if crosscheck_ok:
        ok("Cross-check: DB state is clean")
    else:
        warn("Cross-check: Stale data detected — review issues above")

    if quick_mode:
        warn("Server: Skipped (--quick mode)")
    elif server_ok:
        ok("Server: All routes verified")
    else:
        fail("Server: Issues detected — check output above")

    print()
    print(f"  {YELLOW}{BOLD}REMINDER: The DB is the sole source of truth.{RESET}")
    print(f"  {YELLOW}Docs teach you HOW to query — never cite doc numbers as fact without verifying.{RESET}")
    print()
    all_ok = docs_ok and db_ok and crosscheck_ok and (quick_mode or server_ok)
    if all_ok:
        print(f"  {GREEN}{BOLD}STATUS: READY TO WORK{RESET}")
        print(f"  {GREEN}All systems operational. Read the docs, then ask Alex what to do.{RESET}")
    else:
        print(f"  {YELLOW}{BOLD}STATUS: ISSUES DETECTED{RESET}")
        print(f"  {YELLOW}Fix the issues above before proceeding.{RESET}")

    print()
    print(f"  {BLUE}Reminder: Tell Alex 'I've completed startup. Ready to work.'{RESET}")
    print()


# ============================================================
# MAIN
# ============================================================
def main():
    quick_mode = "--quick" in sys.argv

    print(f"\n{BOLD}IECC Project Startup{RESET}")
    print(f"{'Quick mode' if quick_mode else 'Full stack check'}")
    print(f"Database: {DB_PATH}")
    print(f"Web app: {WEB_DIR}")

    os.chdir(str(BASE_DIR))

    docs_ok = check_docs()
    db_ok = check_db()
    crosscheck_ok = cross_check_db()

    if quick_mode:
        server_ok = None
    else:
        server_ok = check_server()

    print_summary(docs_ok, db_ok, crosscheck_ok, server_ok, quick_mode)


if __name__ == "__main__":
    main()
