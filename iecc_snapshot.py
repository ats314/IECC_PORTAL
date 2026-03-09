#!/usr/bin/env python3
"""IECC 2027 — Change detection between database snapshots.

Usage:
  python3 iecc_snapshot.py save              # Save current state as snapshot
  python3 iecc_snapshot.py compare           # Compare current state to last snapshot
  python3 iecc_snapshot.py compare --detail  # Include per-proposal changes
"""
import sqlite3, json, sys, os
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent
DB_PATH = str(BASE / "iecc.db")
SNAP_DIR = BASE / ".snapshots"

def get_state(db_path, track_name):
    """Extract a comparable state dict from unified database, filtered by track."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    state = {"label": track_name, "proposals": {}, "stats": {}}

    # Stats
    state["stats"]["total_proposals"] = conn.execute(
        "SELECT COUNT(*) FROM proposals WHERE track=?", (track_name,)
    ).fetchone()[0]
    state["stats"]["sg_actions"] = conn.execute(
        "SELECT COUNT(*) FROM subgroup_actions WHERE proposal_uid IN (SELECT proposal_uid FROM proposals WHERE track=?)",
        (track_name,)
    ).fetchone()[0]
    state["stats"]["ca_total"] = conn.execute(
        "SELECT COUNT(*) FROM consensus_actions WHERE proposal_uid IN (SELECT proposal_uid FROM proposals WHERE track=?)",
        (track_name,)
    ).fetchone()[0]
    state["stats"]["ca_final"] = conn.execute(
        "SELECT COUNT(*) FROM consensus_actions WHERE is_final=1 AND proposal_uid IN (SELECT proposal_uid FROM proposals WHERE track=?)",
        (track_name,)
    ).fetchone()[0]
    state["stats"]["sg_with_votes"] = conn.execute(
        "SELECT COUNT(*) FROM subgroup_actions WHERE vote_for IS NOT NULL AND proposal_uid IN (SELECT proposal_uid FROM proposals WHERE track=?)",
        (track_name,)
    ).fetchone()[0]
    state["stats"]["ca_with_votes"] = conn.execute(
        "SELECT COUNT(*) FROM consensus_actions WHERE is_final=1 AND vote_for IS NOT NULL AND proposal_uid IN (SELECT proposal_uid FROM proposals WHERE track=?)",
        (track_name,)
    ).fetchone()[0]
    state["stats"]["withdrawn"] = conn.execute(
        "SELECT COUNT(*) FROM proposals WHERE withdrawn=1 AND track=?", (track_name,)
    ).fetchone()[0]

    # Per-proposal snapshot
    for p in conn.execute(
        "SELECT proposal_uid, canonical_id, withdrawn FROM proposals WHERE track=? ORDER BY canonical_id",
        (track_name,)
    ):
        pid = p["canonical_id"]
        sa = conn.execute("""
            SELECT recommendation, vote_for, vote_against, action_date
            FROM subgroup_actions WHERE proposal_uid=? ORDER BY action_date DESC, id DESC LIMIT 1
        """, (p["proposal_uid"],)).fetchone()
        ca = conn.execute("""
            SELECT recommendation, vote_for, vote_against, action_date
            FROM consensus_actions WHERE proposal_uid=? AND is_final=1 ORDER BY action_date DESC, id DESC LIMIT 1
        """, (p["proposal_uid"],)).fetchone()
        state["proposals"][pid] = {
            "withdrawn": bool(p["withdrawn"]),
            "sg_rec": sa["recommendation"] if sa else None,
            "sg_vote": f"{sa['vote_for']}-{sa['vote_against']}" if sa and sa["vote_for"] is not None else None,
            "ca_rec": ca["recommendation"] if ca else None,
            "ca_vote": f"{ca['vote_for']}-{ca['vote_against']}" if ca and ca["vote_for"] is not None else None,
        }
    conn.close()
    return state

def save_snapshot():
    SNAP_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    snap = {
        "timestamp": ts,
        "saved_at": datetime.now().isoformat(),
        "commercial": get_state(DB_PATH, "commercial"),
        "residential": get_state(DB_PATH, "residential"),
    }
    path = SNAP_DIR / f"snap_{ts}.json"
    with open(path, "w") as f:
        json.dump(snap, f, indent=2)
    print(f"Snapshot saved: {path.name}")
    print(f"  Commercial: {snap['commercial']['stats']['total_proposals']} proposals, {snap['commercial']['stats']['ca_final']} final CA")
    print(f"  Residential: {snap['residential']['stats']['total_proposals']} proposals, {snap['residential']['stats']['ca_final']} final CA")
    return path

def load_latest_snapshot():
    if not SNAP_DIR.exists():
        return None
    files = sorted(SNAP_DIR.glob("snap_*.json"))
    if not files:
        return None
    with open(files[-1]) as f:
        return json.load(f)

def compare(detail=False):
    prev = load_latest_snapshot()
    if not prev:
        print("No previous snapshot found. Run 'python3 iecc_snapshot.py save' first.")
        return

    print(f"Comparing against snapshot from {prev['saved_at']}")
    print("=" * 70)

    for track_name in ["commercial", "residential"]:
        old = prev[track_name]
        cur = get_state(DB_PATH, track_name)

        print(f"\n  {track_name.upper()}")
        print("  " + "─" * 40)

        # Stat diffs
        for key in cur["stats"]:
            o = old["stats"].get(key, 0)
            n = cur["stats"][key]
            delta = n - o
            marker = f"  (+{delta})" if delta > 0 else f"  ({delta})" if delta < 0 else ""
            print(f"    {key:20s}: {n:5d}{marker}")

        # Proposal-level changes
        old_ids = set(old["proposals"].keys())
        cur_ids = set(cur["proposals"].keys())
        new_props = sorted(cur_ids - old_ids)
        removed_props = sorted(old_ids - cur_ids)

        changes = []
        for pid in sorted(cur_ids & old_ids):
            op = old["proposals"][pid]
            cp = cur["proposals"][pid]
            diffs = []
            if op["sg_rec"] != cp["sg_rec"]:
                diffs.append(f"SG rec: {op['sg_rec']} → {cp['sg_rec']}")
            if op["sg_vote"] != cp["sg_vote"]:
                diffs.append(f"SG vote: {op['sg_vote']} → {cp['sg_vote']}")
            if op["ca_rec"] != cp["ca_rec"]:
                diffs.append(f"CA rec: {op['ca_rec']} → {cp['ca_rec']}")
            if op["ca_vote"] != cp["ca_vote"]:
                diffs.append(f"CA vote: {op['ca_vote']} → {cp['ca_vote']}")
            if op["withdrawn"] != cp["withdrawn"]:
                diffs.append(f"withdrawn: {op['withdrawn']} → {cp['withdrawn']}")
            if diffs:
                changes.append((pid, diffs))

        print(f"\n    New proposals:     {len(new_props)}")
        print(f"    Removed proposals: {len(removed_props)}")
        print(f"    Changed proposals: {len(changes)}")

        if detail:
            if new_props:
                print(f"\n    ── New ──")
                for pid in new_props:
                    cp = cur["proposals"][pid]
                    print(f"      {pid}: CA={cp['ca_rec'] or '—'}, SG={cp['sg_rec'] or '—'}")
            if changes:
                print(f"\n    ── Changed ──")
                for pid, diffs in changes:
                    print(f"      {pid}:")
                    for d in diffs:
                        print(f"        {d}")

    print("\n" + "=" * 70)
    print("Done. Run 'python3 iecc_snapshot.py save' to update the baseline.")

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] == "compare":
        compare(detail="--detail" in args)
    elif args[0] == "save":
        save_snapshot()
    else:
        print(__doc__)
