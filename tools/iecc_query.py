#!/usr/bin/env python3
"""
IECC Unified Query Layer
========================
Single-database query interface for unified IECC database.
Provides unified views, status summaries, and crossover tracking.

All tables and views include 'track' column ('commercial' or 'residential').

Phase model:
  PUBLIC_INPUT  — RE/CE phase (closed). Proposals decided or did not advance.
  CODE_PROPOSAL — RECP/CECP phase. Proposals actively being heard.
  PUBLIC_COMMENT — REPC/CEPC phase. Proposals actively being heard.

Usage:
    python3 iecc_query.py                      # Full status summary
    python3 iecc_query.py --status CEPC28-25   # Full status for a single proposal
    python3 iecc_query.py --search RE114       # Search by ID
    python3 iecc_query.py --search Rosenstock  # Search by proponent name
    python3 iecc_query.py --pending            # All pending proposals across both tracks
    python3 iecc_query.py --crossovers         # Crossover proposal report
    python3 iecc_query.py --stats              # Coverage statistics
"""

import sqlite3
import argparse
from pathlib import Path

BASE = Path(__file__).parent.parent
DB_PATH = str(BASE / "iecc.db")

ACTIVE_PHASES = ('CODE_PROPOSAL', 'PUBLIC_COMMENT')
TRACKS = ('commercial', 'residential')

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def unified_status():
    """Print combined status across both tracks."""
    print("=" * 80)
    print("IECC 2027 — UNIFIED STATUS REPORT")
    print("=" * 80)

    conn = get_conn()
    total_all = 0
    decided_all = 0
    pending_all = 0

    for track in TRACKS:
        label = track.upper()

        total = conn.execute(
            "SELECT COUNT(*) FROM proposals WHERE track=?", (track,)
        ).fetchone()[0]
        withdrawn = conn.execute(
            "SELECT COUNT(*) FROM proposals WHERE track=? AND withdrawn=1", (track,)
        ).fetchone()[0]

        # Phase counts
        phases = {}
        for r in conn.execute(
            "SELECT phase, COUNT(*) FROM proposals WHERE track=? GROUP BY phase", (track,)
        ):
            phases[r[0]] = r[1]

        # Status from view
        statuses = {}
        for r in conn.execute(
            "SELECT status, COUNT(*) FROM v_current_status WHERE track=? GROUP BY status", (track,)
        ):
            statuses[r[0]] = r[1]

        decided = statuses.get('Decided', 0)
        pending = statuses.get('Pending', 0)
        phase_closed = statuses.get('Phase Closed', 0)

        # Active phase proposals
        active_total = sum(phases.get(p, 0) for p in ACTIVE_PHASES)
        active_decided = conn.execute("""
            SELECT COUNT(*) FROM proposals p
            JOIN consensus_actions ca ON p.proposal_uid = ca.proposal_uid AND ca.is_final=1
            WHERE p.track=? AND p.phase IN ('CODE_PROPOSAL', 'PUBLIC_COMMENT')
        """, (track,)).fetchone()[0]

        # Vote coverage
        sa = conn.execute(
            "SELECT COUNT(*) FROM subgroup_actions WHERE track=?", (track,)
        ).fetchone()[0]
        sa_votes = conn.execute(
            "SELECT COUNT(*) FROM subgroup_actions WHERE track=? AND vote_for IS NOT NULL", (track,)
        ).fetchone()[0]
        ca_final = conn.execute(
            "SELECT COUNT(*) FROM consensus_actions WHERE track=? AND is_final=1", (track,)
        ).fetchone()[0]
        ca_votes = conn.execute(
            "SELECT COUNT(*) FROM consensus_actions WHERE track=? AND is_final=1 AND vote_for IS NOT NULL", (track,)
        ).fetchone()[0]

        print(f"\n  {label}")
        print(f"  {'─' * 50}")
        print(f"    Total proposals:      {total}")
        print(f"      Public Input (closed):  {phases.get('PUBLIC_INPUT', 0):4d}  ({statuses.get('Decided', 0) - active_decided} decided, {phase_closed} no action)")
        print(f"      Code Proposal (active): {phases.get('CODE_PROPOSAL', 0):4d}")
        print(f"      Public Comment (active):{phases.get('PUBLIC_COMMENT', 0):4d}")
        print(f"    Withdrawn:            {withdrawn}")
        print(f"    Decided:              {decided}")
        print(f"    Pending (active):     {pending}")
        print(f"    Phase Closed:         {phase_closed}")
        print(f"    SG Actions:           {sa} ({sa_votes} with votes, {sa_votes*100//max(sa,1)}%)")
        print(f"    Final CA:             {ca_final} ({ca_votes} with votes, {ca_votes*100//max(ca_final,1)}%)")

        # Recommendation breakdown
        print(f"    Consensus decisions:")
        for row in conn.execute("""
            SELECT recommendation, COUNT(*) FROM consensus_actions
            WHERE track=? AND is_final=1 AND recommendation IS NOT NULL
            GROUP BY recommendation ORDER BY COUNT(*) DESC
        """, (track,)):
            print(f"      {row[0]:35s}: {row[1]}")

        total_all += total
        decided_all += decided
        pending_all += pending

    conn.close()

    print(f"\n  COMBINED")
    print(f"  {'─' * 50}")
    print(f"    Total proposals:    {total_all}")
    print(f"    Total decided:      {decided_all}")
    print(f"    Pending (active):   {pending_all}")
    print(f"    Decision rate:      {decided_all*100//max(total_all,1)}%")
    print()

def crossover_report():
    """Show proposals where canonical_id suggests one track but appears in another."""
    print("=" * 80)
    print("CROSSOVER PROPOSALS (Commercial ↔ Residential)")
    print("=" * 80)

    conn = get_conn()

    # CE/CEPC in residential track (should be in commercial)
    res_crossovers = conn.execute("""
        SELECT p.canonical_id, p.current_subgroup, p.track,
               ca.recommendation AS consensus_rec,
               ca.vote_for, ca.vote_against, ca.vote_not_voting
        FROM proposals p
        LEFT JOIN consensus_actions ca ON p.proposal_uid = ca.proposal_uid AND ca.is_final = 1
        WHERE p.track='residential' AND p.prefix IN ('CE', 'CEPC')
        ORDER BY p.canonical_id
    """).fetchall()

    print(f"\n  CE/CEPC proposals in Residential track: {len(res_crossovers)}")
    for r in res_crossovers:
        canon = r['canonical_id']
        comm_row = conn.execute("""
            SELECT p.canonical_id, ca.recommendation, ca.vote_for, ca.vote_against, ca.vote_not_voting
            FROM proposals p
            LEFT JOIN consensus_actions ca ON p.proposal_uid = ca.proposal_uid AND ca.is_final = 1
            WHERE p.track='commercial' AND p.canonical_id = ?
        """, (canon,)).fetchone()

        res_status = r['consensus_rec'] or 'No action'
        comm_status = comm_row['recommendation'] if comm_row and comm_row['recommendation'] else 'Not in commercial track'

        print(f"\n    {canon}")
        print(f"      Residential: {res_status}")
        if r['vote_for'] is not None:
            print(f"        Vote: {r['vote_for']}-{r['vote_against']}-{r['vote_not_voting']}")
        print(f"      Commercial:  {comm_status}")
        if comm_row and comm_row['vote_for'] is not None:
            print(f"        Vote: {comm_row['vote_for']}-{comm_row['vote_against']}-{comm_row['vote_not_voting']}")

    # RE/RECP in commercial track (should be in residential)
    comm_crossovers = conn.execute("""
        SELECT p.canonical_id, p.current_subgroup, p.track,
               ca.recommendation AS consensus_rec,
               ca.vote_for, ca.vote_against, ca.vote_not_voting
        FROM proposals p
        LEFT JOIN consensus_actions ca ON p.proposal_uid = ca.proposal_uid AND ca.is_final = 1
        WHERE p.track='commercial' AND p.prefix IN ('RE', 'RECP')
        ORDER BY p.canonical_id
    """).fetchall()

    print(f"\n  RE/RECP proposals in Commercial track: {len(comm_crossovers)}")
    for r in comm_crossovers:
        canon = r['canonical_id']
        res_row = conn.execute("""
            SELECT p.canonical_id, ca.recommendation, ca.vote_for, ca.vote_against, ca.vote_not_voting
            FROM proposals p
            LEFT JOIN consensus_actions ca ON p.proposal_uid = ca.proposal_uid AND ca.is_final = 1
            WHERE p.track='residential' AND p.canonical_id = ?
        """, (canon,)).fetchone()

        comm_status = r['consensus_rec'] or 'No action'
        res_status = res_row['recommendation'] if res_row and res_row['recommendation'] else 'Not in residential track'

        print(f"\n    {canon}")
        print(f"      Commercial: {comm_status}")
        if r['vote_for'] is not None:
            print(f"        Vote: {r['vote_for']}-{r['vote_against']}-{r['vote_not_voting']}")
        print(f"      Residential: {res_status}")
        if res_row and res_row['vote_for'] is not None:
            print(f"        Vote: {res_row['vote_for']}-{res_row['vote_against']}-{res_row['vote_not_voting']}")

    conn.close()

def single_status(query):
    """Full status for a single proposal (exact or partial ID match)."""
    print(f"Looking up '{query}'...\n")

    conn = get_conn()
    rows = conn.execute("""
        SELECT * FROM v_current_status WHERE canonical_id LIKE ?
        ORDER BY track, canonical_id
    """, (f"%{query}%",)).fetchall()

    if rows:
        current_track = None
        for r in rows:
            track_label = r['track'].upper()
            if track_label != current_track:
                current_track = track_label
                print(f"  {track_label}:")

            print(f"    {r['canonical_id']}  ({r['proponent'] or 'Unknown'})")
            print(f"      Phase:      {r['phase']}")
            print(f"      Subgroup:   {r['current_subgroup'] or 'Unassigned'}")
            print(f"      Section:    {r['code_section'] or 'N/A'}")
            print(f"      Status:     {r['status']}")
            if r['sg_recommendation']:
                sg_vote = f"{r['sg_vote_for']}-{r['sg_vote_against']}" if r['sg_vote_for'] is not None else "no vote"
                print(f"      SG Rec:     {r['sg_recommendation']} ({sg_vote}) {r['sg_date'] or ''}")
            if r['ca_recommendation']:
                ca_vote = f"{r['ca_vote_for']}-{r['ca_vote_against']}" if r['ca_vote_for'] is not None else "no vote"
                print(f"      CA Decision: {r['ca_recommendation']} ({ca_vote}) {r['ca_date'] or ''}")
            if r['withdrawn']:
                print(f"      *** WITHDRAWN ***")

            # Also show full action history if multiple CAs
            actions = conn.execute("""
                SELECT ca.sequence, ca.action_date, ca.recommendation, ca.vote_for, ca.vote_against,
                       ca.vote_not_voting, ca.reason, ca.moved_by, ca.seconded_by, ca.is_final
                FROM consensus_actions ca
                JOIN proposals p ON ca.proposal_uid = p.proposal_uid
                WHERE p.canonical_id = ? AND p.track = ?
                ORDER BY ca.sequence
            """, (r['canonical_id'], r['track'])).fetchall()
            if len(actions) > 1:
                print(f"      Action chain ({len(actions)} actions):")
                for a in actions:
                    vote_str = f"{a['vote_for']}-{a['vote_against']}-{a['vote_not_voting']}" if a['vote_for'] is not None else "no vote"
                    final_tag = " [FINAL]" if a['is_final'] else ""
                    print(f"        #{a['sequence']}: {a['recommendation']} ({vote_str}) {a['action_date'] or ''}{final_tag}")
            print()
    else:
        print(f"  No matches found")

    conn.close()

def search_proposal(query):
    """Search for a proposal by ID or proponent across both tracks."""
    print(f"Searching for '{query}' across both tracks...\n")

    conn = get_conn()
    results = conn.execute("""
        SELECT p.canonical_id, p.prefix, p.phase, p.proponent, p.current_subgroup,
               p.withdrawn, p.code_section, p.track
        FROM proposals p
        WHERE p.canonical_id LIKE ? OR p.proponent LIKE ?
        ORDER BY p.track, p.canonical_id
    """, (f"%{query}%", f"%{query}%")).fetchall()

    if results:
        current_track = None
        for r in results:
            track_label = r['track'].upper()
            if track_label != current_track:
                current_track = track_label
                result_count = sum(1 for x in results if x['track'] == r['track'])
                print(f"  {track_label} ({result_count} match{'es' if result_count > 1 else ''}):")

            phase_tag = f"[{r['phase']}]" if r['phase'] else ""
            print(f"    {r['canonical_id']:25s} {r['prefix'] or '?':8s} {phase_tag:20s} {r['proponent'] or 'Unknown':25s}")

            sa = conn.execute("""
                SELECT recommendation, vote_for, vote_against, vote_not_voting, action_date
                FROM subgroup_actions sa
                JOIN proposals p ON sa.proposal_uid = p.proposal_uid
                WHERE p.canonical_id = ? AND p.track = ?
            """, (r['canonical_id'], r['track'])).fetchall()
            for a in sa:
                vote = f"{a['vote_for']}-{a['vote_against']}-{a['vote_not_voting']}" if a['vote_for'] is not None else "no vote"
                print(f"      SG:  {a['recommendation'] or 'None':25s} {vote:10s} {a['action_date'] or ''}")

            ca = conn.execute("""
                SELECT recommendation, vote_for, vote_against, vote_not_voting, action_date, is_final
                FROM consensus_actions ca
                JOIN proposals p ON ca.proposal_uid = p.proposal_uid
                WHERE p.canonical_id = ? AND p.track = ?
                ORDER BY ca.action_date, ca.id
            """, (r['canonical_id'], r['track'])).fetchall()
            for a in ca:
                vote = f"{a['vote_for']}-{a['vote_against']}-{a['vote_not_voting']}" if a['vote_for'] is not None else "no vote"
                final = " [FINAL]" if a['is_final'] else ""
                print(f"      CA:  {a['recommendation'] or 'None':25s} {vote:10s} {a['action_date'] or ''}{final}")
    else:
        print(f"  No matches found")

    conn.close()

def pending_report():
    """Show all truly pending proposals (active phases only)."""
    print("=" * 80)
    print("PENDING PROPOSALS — ACTIVE PHASES ONLY")
    print("=" * 80)

    conn = get_conn()

    for track in TRACKS:
        label = track.upper()
        pending = conn.execute("""
            SELECT canonical_id, prefix, phase, current_subgroup, sg_recommendation, track
            FROM v_current_status
            WHERE status = 'Pending' AND track = ?
            ORDER BY current_subgroup, canonical_id
        """, (track,)).fetchall()

        print(f"\n  {label} — {len(pending)} pending proposals")
        by_sg = {}
        for r in pending:
            sg = r['current_subgroup'] or 'Unassigned'
            by_sg.setdefault(sg, []).append(r)

        for sg in sorted(by_sg.keys()):
            items = by_sg[sg]
            print(f"\n    {sg} ({len(items)}):")
            for r in items:
                rec = r['sg_recommendation'] or ''
                print(f"      {r['canonical_id']:25s} [{r['phase']}] {rec}")

    conn.close()

def coverage_stats():
    """Print detailed coverage statistics for both tracks."""
    print("=" * 80)
    print("DATA QUALITY & COVERAGE STATISTICS")
    print("=" * 80)

    conn = get_conn()

    for track in TRACKS:
        label = track.upper()
        total = conn.execute(
            "SELECT COUNT(*) FROM proposals WHERE track=?", (track,)
        ).fetchone()[0]
        sa = conn.execute(
            "SELECT COUNT(*) FROM subgroup_actions WHERE track=?", (track,)
        ).fetchone()[0]
        ca = conn.execute(
            "SELECT COUNT(*) FROM consensus_actions WHERE track=? AND is_final=1", (track,)
        ).fetchone()[0]

        sa_v = conn.execute(
            "SELECT COUNT(*) FROM subgroup_actions WHERE track=? AND vote_for IS NOT NULL", (track,)
        ).fetchone()[0]
        sa_r = conn.execute(
            "SELECT COUNT(*) FROM subgroup_actions WHERE track=? AND reason IS NOT NULL AND reason != ''", (track,)
        ).fetchone()[0]
        ca_v = conn.execute(
            "SELECT COUNT(*) FROM consensus_actions WHERE track=? AND is_final=1 AND vote_for IS NOT NULL", (track,)
        ).fetchone()[0]
        emails = conn.execute(
            "SELECT COUNT(*) FROM proposals WHERE track=? AND proponent_email IS NOT NULL", (track,)
        ).fetchone()[0]
        dq = conn.execute(
            "SELECT COUNT(*) FROM data_quality_flags WHERE track=?", (track,)
        ).fetchone()[0]
        dq_review = conn.execute(
            "SELECT COUNT(*) FROM data_quality_flags WHERE track=? AND needs_review=1", (track,)
        ).fetchone()[0]

        # Phase breakdown
        phase_closed = conn.execute(
            "SELECT COUNT(*) FROM proposals WHERE track=? AND phase='PUBLIC_INPUT'", (track,)
        ).fetchone()[0]
        active = total - phase_closed

        print(f"\n  {label}")
        print(f"  {'─' * 50}")
        print(f"    Proposals:            {total} ({phase_closed} public input closed, {active} active)")
        print(f"    SG vote coverage:     {sa_v:3d}/{sa:3d} ({sa_v*100//max(sa,1)}%)")
        print(f"    SG reason coverage:   {sa_r:3d}/{sa:3d} ({sa_r*100//max(sa,1)}%)")
        print(f"    CA vote coverage:     {ca_v:3d}/{ca:3d} ({ca_v*100//max(ca,1)}%)")
        print(f"    Email coverage:       {emails:3d}/{total:3d} ({emails*100//max(total,1)}%)")
        print(f"    Data quality flags:   {dq} ({dq_review} need review)")

        for row in conn.execute("""
            SELECT flag_type, COUNT(*) FROM data_quality_flags
            WHERE track=?
            GROUP BY flag_type ORDER BY COUNT(*) DESC LIMIT 5
        """, (track,)):
            print(f"      {row[0]:40s}: {row[1]}")

    conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IECC Unified Query Tool")
    parser.add_argument("--crossovers", action="store_true", help="Crossover proposal report")
    parser.add_argument("--search", type=str, help="Search by proposal ID or proponent name")
    parser.add_argument("--status", type=str, help="Full status for a single proposal (exact or partial ID)")
    parser.add_argument("--pending", action="store_true", help="Pending proposals (active phases only)")
    parser.add_argument("--stats", action="store_true", help="Coverage statistics")
    args = parser.parse_args()

    if args.crossovers:
        crossover_report()
    elif args.search:
        search_proposal(args.search)
    elif args.status:
        single_status(args.status)
    elif args.pending:
        pending_report()
    elif args.stats:
        coverage_stats()
    else:
        unified_status()
