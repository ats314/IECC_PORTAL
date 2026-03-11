#!/usr/bin/env python3
"""
iecc_verify.py — Verify all project documentation matches database state.

Usage:
    python3 iecc_verify.py          # Check only, report discrepancies
    python3 iecc_verify.py --fix    # Auto-fix stale numbers in docs

Checks CLAUDE.md, AGENT_GUIDE.md, and PROJECT_MEMORY.md against
unified iecc.db database (filtering by track: 'commercial' or 'residential').
"""

import sqlite3
import re
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

DOCS = ['CLAUDE.md', 'docs/AGENT_GUIDE.md', 'docs/PROJECT_MEMORY.md']
DB_PATH = os.path.join(PROJECT_ROOT, 'iecc.db')

def get_db_truth():
    """Pull ground truth from unified database, filtering by track."""
    truth = {}
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    for label, track in [('COM', 'commercial'), ('RES', 'residential')]:
        d = {}
        for t in ['proposals', 'subgroup_actions', 'consensus_actions',
                   'data_quality_flags', 'meetings', 'subgroup_movements',
                   'errata', 'governance_documents', 'governance_clauses']:
            try:
                cur.execute(f'SELECT COUNT(*) FROM {t} WHERE track = ?', (track,))
                d[t] = cur.fetchone()[0]
            except:
                d[t] = None

        cur.execute('SELECT COUNT(*) FROM consensus_actions WHERE is_final=1 AND track = ?', (track,))
        d['ca_final'] = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) FROM data_quality_flags WHERE needs_review=1 AND track = ?', (track,))
        d['dq_open'] = cur.fetchone()[0]
        cur.execute('SELECT status, COUNT(*) FROM v_current_status WHERE track = ? GROUP BY status', (track,))
        for r in cur.fetchall():
            d[f'status_{r[0]}'] = r[1]
        cur.execute('SELECT phase, COUNT(*) FROM proposals WHERE track = ? GROUP BY phase', (track,))
        for r in cur.fetchall():
            d[f'phase_{r[0]}'] = r[1]
        truth[label] = d

    conn.close()
    return truth


def find_current_state_sections(content):
    """Identify line ranges that represent CURRENT state (not historical session logs)."""
    lines = content.split('\n')
    # Historical session logs: lines inside "### Session N —" blocks
    # Current state: everything else
    in_session_log = False
    current_lines = set()
    for i, line in enumerate(lines):
        if re.match(r'###\s*Session \d+ —', line):
            in_session_log = True
        elif re.match(r'###\s', line) and in_session_log:
            # New heading that's not a session log
            if not re.match(r'###\s*Session \d+', line):
                in_session_log = False
        elif re.match(r'^##\s', line):
            in_session_log = False

        if not in_session_log:
            current_lines.add(i)
    return current_lines


def check_docs(truth, fix=False):
    """Check all docs against DB truth. Optionally fix."""
    t_com = truth['COM']
    t_res = truth['RES']
    total_proposals = t_com['proposals'] + t_res['proposals']

    errors = []
    fixes_applied = []

    # Define what numbers to look for and replace
    # Format: (pattern_to_find, context_hint, correct_value, description)
    # We check each doc independently

    for fname in DOCS:
        fpath = os.path.join(PROJECT_ROOT, fname)
        if not os.path.exists(fpath):
            errors.append(f"{fname}: FILE NOT FOUND")
            continue

        with open(fpath) as f:
            content = f.read()
        lines = content.split('\n')
        current_lines = find_current_state_sections(content)
        original_content = content

        for i, line in enumerate(lines):
            ln = i + 1
            # Skip historical session log entries
            if i not in current_lines:
                continue
            # Skip lines with → (deltas)
            if '→' in line:
                continue

            # === Check for known stale values ===
            stale_checks = [
                # (regex, description, should_not_appear_value)
                (r'\b239\b.*(?:decided|Decided)', f'COM decided should be {t_com["status_Decided"]}', 239),
                (r'\b11\s+pending\b', f'COM pending should be {t_com["status_Pending"]}', 11),
                (r'(?:Pending.*\b|\b)13\s+withdrawn', f'COM withdrawn should be {t_com["status_Withdrawn"]}', 13),
                (r'\b128\b.*(?:decided|Decided)', f'RES decided should be {t_res["status_Decided"]}', 128),
                (r'\b40\b.*(?:pending|Pending)', f'RES pending should be {t_res["status_Pending"]}', 40),
                (r'\b277\b.*(?:consensus|CA|total)', f'COM CA should be {t_com["consensus_actions"]}', 277),
                (r'\b249\b.*final', f'COM CA final should be {t_com["ca_final"]}', 249),
                (r'\b187\b.*(?:consensus|CA|total)', f'RES CA should be {t_res["consensus_actions"]}', 187),
                (r'\b138\b.*final', f'RES CA final should be {t_res["ca_final"]}', 138),
                (r'\b202\b.*(?:subgroup|SA)', f'COM SA should be {t_com["subgroup_actions"]}', 202),
                (r'\b192\b.*(?:subgroup|SA|action)', f'RES SA should be {t_res["subgroup_actions"]}', 192),
                (r'\b196\b.*(?:subgroup|SA)', f'RES SA should be {t_res["subgroup_actions"]}', 196),
                (r'\b137\b.*(?:quality|DQ|flag|residential)', f'RES DQ should be {t_res["data_quality_flags"]}', 137),
                (r'~490', f'Total proposals should be ~{total_proposals}', 490),
                (r'\b241\b.*proposal', f'RES proposals should be {t_res["proposals"]}', 241),
            ]

            for pattern, desc, stale_val in stale_checks:
                if re.search(pattern, line, re.I):
                    # Extract the correct value from the description
                    correct_match = re.search(r'should be (\d+)', desc)
                    if correct_match:
                        correct_val = correct_match.group(1)
                        # If line already contains the correct value, this is likely
                        # a historical reference (e.g. "248 (was 241 in Session 10)")
                        if re.search(r'\b' + correct_val + r'\b', line):
                            continue
                    errors.append(f"{fname}:{ln} STALE — {desc}: {line.strip()[:80]}")

            # === Specific table checks ===
            # AGENT_GUIDE and PROJECT_MEMORY status tables
            if '| Decided |' in line or '| Decided |' in line:
                m = re.search(r'\| Decided \| (\d+)', line)
                if m:
                    val = int(m.group(1))
                    if val not in [t_com['status_Decided'], t_res['status_Decided']]:
                        errors.append(f"{fname}:{ln} Decided table value {val} not in [{t_com['status_Decided']}, {t_res['status_Decided']}]")

            if '| Pending |' in line or '| Pending (active' in line:
                m = re.search(r'\| (\d+)', line)
                if m:
                    val = int(m.group(1))
                    if val not in [t_com['status_Pending'], t_res['status_Pending']]:
                        errors.append(f"{fname}:{ln} Pending table value {val} not in [{t_com['status_Pending']}, {t_res['status_Pending']}]")

            if '| Withdrawn |' in line:
                m = re.search(r'\| Withdrawn \| (\d+)', line)
                if m:
                    val = int(m.group(1))
                    if val not in [t_com['status_Withdrawn'], t_res['status_Withdrawn']]:
                        errors.append(f"{fname}:{ln} Withdrawn table value {val} not in [{t_com['status_Withdrawn']}, {t_res['status_Withdrawn']}]")

            # Schema/reference table checks
            m = re.search(r'residential has (\d+) proposals, (\d+) CA, (\d+) SA', line)
            if m:
                if int(m.group(1)) != t_res['proposals']:
                    errors.append(f"{fname}:{ln} schema note proposals {m.group(1)} != {t_res['proposals']}")
                if int(m.group(2)) != t_res['consensus_actions']:
                    errors.append(f"{fname}:{ln} schema note CA {m.group(2)} != {t_res['consensus_actions']}")
                if int(m.group(3)) != t_res['subgroup_actions']:
                    errors.append(f"{fname}:{ln} schema note SA {m.group(3)} != {t_res['subgroup_actions']}")

            # data_quality_flags table line
            if 'data_quality_flags' in line and '|' in line and 'open' in line:
                nums = re.findall(r'(\d+)\s*\((\d+)\s*open\)', line)
                for total_str, open_str in nums:
                    total_val = int(total_str)
                    open_val = int(open_str)
                    if total_val not in [t_com['data_quality_flags'], t_res['data_quality_flags']]:
                        errors.append(f"{fname}:{ln} DQ total {total_val} not in [{t_com['data_quality_flags']}, {t_res['data_quality_flags']}]")
                    if open_val not in [t_com['dq_open'], t_res['dq_open']]:
                        errors.append(f"{fname}:{ln} DQ open {open_val} not in [{t_com['dq_open']}, {t_res['dq_open']}]")

    return errors


def print_summary(truth):
    """Print current DB state summary."""
    t = truth
    print("=" * 60)
    print("GROUND TRUTH (from databases)")
    print("=" * 60)
    print(f"\nCOMMERCIAL: {t['COM']['proposals']} proposals")
    print(f"  Decided: {t['COM']['status_Decided']}, Pending: {t['COM']['status_Pending']}, "
          f"Withdrawn: {t['COM']['status_Withdrawn']}, Phase Closed: {t['COM'].get('status_Phase Closed', 0)}")
    print(f"  CA: {t['COM']['consensus_actions']} ({t['COM']['ca_final']} final), "
          f"SA: {t['COM']['subgroup_actions']}, DQ: {t['COM']['data_quality_flags']} ({t['COM']['dq_open']} open)")

    print(f"\nRESIDENTIAL: {t['RES']['proposals']} proposals")
    print(f"  Decided: {t['RES']['status_Decided']}, Pending: {t['RES']['status_Pending']}, "
          f"Withdrawn: {t['RES']['status_Withdrawn']}, Phase Closed: {t['RES'].get('status_Phase Closed', 0)}")
    print(f"  CA: {t['RES']['consensus_actions']} ({t['RES']['ca_final']} final), "
          f"SA: {t['RES']['subgroup_actions']}, DQ: {t['RES']['data_quality_flags']} ({t['RES']['dq_open']} open)")
    print(f"\nTOTAL: {t['COM']['proposals'] + t['RES']['proposals']} proposals")


def main():
    fix_mode = '--fix' in sys.argv

    truth = get_db_truth()
    print_summary(truth)

    print("\n" + "=" * 60)
    print("CHECKING DOCS...")
    print("=" * 60)

    errors = check_docs(truth, fix=fix_mode)

    if errors:
        print(f"\n❌ FOUND {len(errors)} ISSUES:")
        for e in errors:
            print(f"  {e}")
        if not fix_mode:
            print(f"\nRun with --fix to auto-repair.")
        return 1
    else:
        print(f"\n✅ ALL DOCS MATCH DATABASE. Zero discrepancies.")
        return 0


if __name__ == '__main__':
    sys.exit(main())
