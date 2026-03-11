#!/usr/bin/env python3
"""
populate_content.py — Scan IECC Standard folder, parse proposal DOCX files,
and populate the centralized content tables in iecc.db.

Tables populated:
  - documents    (file registry — every relevant file on disk)
  - proposal_text (extracted proposal language with HTML markup)
  - modifications (pre-submitted modification documents)

Usage:
  python3 populate_content.py              # Full scan + parse
  python3 populate_content.py --scan-only  # Just register files, don't parse
  python3 populate_content.py --stats      # Show current table stats
"""

import sqlite3
import os
import re
import hashlib
import sys
from datetime import datetime

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(_PROJECT_ROOT, 'iecc.db')
IECC_STD = os.path.join(_PROJECT_ROOT, 'IECC standard')
PROPOSAL_TEXT_SOURCES = os.path.join(_PROJECT_ROOT, 'Proposal_Text_Sources')
COMMERCIAL_2027 = os.path.join(_PROJECT_ROOT, '2027_COMMERCIAL')
RESIDENTIAL_2027 = os.path.join(_PROJECT_ROOT, '2027_RESIDENTIAL')
ARCHIVES = os.path.join(_PROJECT_ROOT, 'ARCHIVES')
ONEDRIVE_SYNC = os.path.join(_PROJECT_ROOT, 'OneDrive_1_3-9-2026')
PC_POSTING_JAN = os.path.join(_PROJECT_ROOT, '2026-01-23 Public Comment Posting')
PC_POSTING_FEB = os.path.join(_PROJECT_ROOT, '2026-02-13 Public Comment Posting')
PC_POSTING_MAR = os.path.join(_PROJECT_ROOT, '2026-03-07 Public Comment Posting')
# Residential public comment DOCX files (4 posting batches)
PC_DOCS_PARENT = os.path.join(_PROJECT_ROOT, '2027 IECC Public Comment Documents')
# OneDrive sync copies (may have additional files)
ONEDRIVE_2 = os.path.join(_PROJECT_ROOT, 'OneDrive_2_3-9-2026')
ONEDRIVE_3 = os.path.join(_PROJECT_ROOT, 'OneDrive_3_3-9-2026')
# FUSE folder
FUSE = os.path.join(_PROJECT_ROOT, 'FUSE')

# All source folders to scan (in priority order — later folders override earlier ones)
SOURCE_FOLDERS = [IECC_STD, PROPOSAL_TEXT_SOURCES, COMMERCIAL_2027, RESIDENTIAL_2027, ARCHIVES, ONEDRIVE_SYNC,
                  PC_POSTING_JAN, PC_POSTING_FEB, PC_POSTING_MAR,
                  PC_DOCS_PARENT, ONEDRIVE_2, ONEDRIVE_3, FUSE]

# ============================================================
# DOCX PARSER — Extract proposal language with formatting
# ============================================================

def parse_proposal_docx(file_path):
    """
    Parse a cdpACCESS proposal DOCX and extract structured content.
    Returns dict with proposal_html, proposal_plain, reason_text, cost_impact_text, code_section_text.
    """
    from docx import Document

    doc = Document(file_path)
    paragraphs = [p for p in doc.paragraphs]

    if not paragraphs:
        return None

    result = {
        'proposal_html': '',
        'proposal_plain': '',
        'reason_text': '',
        'cost_impact_text': '',
        'code_section_text': '',
    }

    # The cdpACCESS format is structured:
    # P0: Proposal ID (e.g., "CEPC18-25")
    # P1: Code section (e.g., "IECC: Table C407.2(2)")
    # P2: Proponents line
    # P3: Code title (e.g., "2027 International Energy Conservation Code (DRAFT)")
    # P4+: "Revise as follows:" then the actual code text with formatting
    # Eventually: "Reason:" section
    # Eventually: "Cost Impact:" section

    # Extract code section from early paragraphs
    for p in paragraphs[:5]:
        text = p.text.strip()
        if text.startswith('IECC:') or text.startswith('IECC-'):
            result['code_section_text'] = text
            break

    # Find key section boundaries
    in_code_text = False
    in_reason = False
    in_cost_impact = False
    code_html_parts = []
    code_plain_parts = []
    reason_parts = []
    cost_parts = []

    for p in paragraphs:
        text = p.text.strip()
        text_lower = text.lower()

        # Detect section transitions
        if text_lower.startswith('revise as follows') or text_lower.startswith('add new') or text_lower.startswith('delete and substitute') or text_lower.startswith('delete without substitution'):
            in_code_text = True
            in_reason = False
            in_cost_impact = False
            # Include the instruction line itself
            code_html_parts.append(f'<p><b>{_escape(text)}</b></p>')
            code_plain_parts.append(text)
            continue

        if text_lower.startswith('reason:') or text_lower == 'reason':
            in_code_text = False
            in_reason = True
            in_cost_impact = False
            # Don't include the "Reason:" label itself
            if text_lower != 'reason:' and text_lower != 'reason':
                reason_parts.append(text.replace('Reason:', '').strip())
            continue

        if text_lower.startswith('cost impact:') or text_lower == 'cost impact':
            in_code_text = False
            in_reason = False
            in_cost_impact = True
            if text_lower != 'cost impact:' and text_lower != 'cost impact':
                cost_parts.append(text.replace('Cost Impact:', '').strip())
            continue

        # Accumulate content
        if in_code_text and text:
            html = _paragraph_to_html(p)
            code_html_parts.append(html)
            code_plain_parts.append(text)
        elif in_reason and text:
            reason_parts.append(text)
        elif in_cost_impact and text:
            cost_parts.append(text)

    result['proposal_html'] = '\n'.join(code_html_parts)
    result['proposal_plain'] = '\n'.join(code_plain_parts)
    result['reason_text'] = '\n'.join(reason_parts)
    result['cost_impact_text'] = '\n'.join(cost_parts)

    return result


def _escape(text):
    """HTML-escape text."""
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def _paragraph_to_html(paragraph):
    """
    Convert a python-docx Paragraph to HTML, preserving ICC formatting:
    - underline → <ins> (additions)
    - strikethrough → <del> (deletions)
    - bold → <b>
    - italic → <i>
    """
    runs_html = []
    for run in paragraph.runs:
        text = _escape(run.text)
        if not text:
            continue

        # Build nested tags
        if run.font.strike:
            text = f'<del>{text}</del>'
        if run.underline:
            text = f'<ins>{text}</ins>'
        if run.bold:
            text = f'<b>{text}</b>'
        if run.italic:
            text = f'<i>{text}</i>'

        runs_html.append(text)

    content = ''.join(runs_html)
    if not content.strip():
        return ''
    return f'<p>{content}</p>'


# ============================================================
# FILE SCANNER — Find and register all relevant files
# ============================================================

# Patterns for matching files to proposals
CDP_PROPOSAL_RE = re.compile(r'^proposal_([A-Z]+\d+-\d+)_(\d+)\.docx$', re.IGNORECASE)
CDP_PROPOSAL_NUMERIC_RE = re.compile(r'^proposal_(\d+)_(\d+)\.docx$', re.IGNORECASE)  # proposal_{cdpaccess_id}_{num}.docx
CDP_MOD_RE = re.compile(r'^proposal_([A-Z]+\d+-\d+)_(\d+)\s*-\s*modification\.docx$', re.IGNORECASE)
MOD_DOCX_RE = re.compile(r'_MOD\d?[_\.]', re.IGNORECASE)

# Comment Ready pattern: "proposal_CEPC10-25 (Comment Ready).docx" or "CECP1-25 (Comment Ready).docx"
COMMENT_READY_RE = re.compile(r'^(?:proposal_)?([A-Z]+\d+-\d+)\s*\(Comment Ready[^)]*\)\.docx$', re.IGNORECASE)

# Standalone modification pattern: "CEPC13-25 Modification.docx", "REPC18-25 (Modification).docx", "REPC36-25_MOD[4].docx"
STANDALONE_MOD_RE = re.compile(r'^(?:proposal_)?([A-Z]+\d+-\d+)\s*(?:\(|\s|_)(?:Modification|MOD)', re.IGNORECASE)

# Standalone circ form pattern: "Circ Form REPC21-25.docx", "RECP17-25 Circulation Form.docx"
STANDALONE_CIRC_RE = re.compile(r'([A-Z]+\d+-\d+).*(?:Circ|Circulation)\s*Form', re.IGNORECASE)
CIRC_FIRST_RE = re.compile(r'(?:Circ|Circulation)\s*Form.*?([A-Z]+\d+-\d+)', re.IGNORECASE)

# General proposal ID extraction from any filename
PROPOSAL_ID_RE = re.compile(r'((?:CEPC|CECP|REPC|RECP|CECC|RECC|IRCEPC|CE|RE)\d+-\d+)', re.IGNORECASE)

DOC_TYPE_PATTERNS = {
    'transcript_docx': re.compile(r'(subgroup|committee)\s+meeting\.docx$', re.IGNORECASE),
    'transcript_vtt': re.compile(r'\.(vtt)$', re.IGNORECASE),
    'agenda_pdf': re.compile(r'agenda.*\.pdf$', re.IGNORECASE),
    'agenda_docx': re.compile(r'agenda.*\.docx$', re.IGNORECASE),
    'pnnl_analysis': re.compile(r'pnnl.*\.(docx|pdf)$', re.IGNORECASE),
    'circ_form_docx': re.compile(r'circ.*form.*\.docx$', re.IGNORECASE),
    'circ_form_pdf': re.compile(r'circ.*form.*\.pdf$', re.IGNORECASE),
    'ballot_pdf': re.compile(r'ballot.*\.pdf$', re.IGNORECASE),
    'proponent_comment': re.compile(r'proponent.*comment.*\.(docx|pdf)$', re.IGNORECASE),
}


def _normalize_proposal_id(pid):
    """Normalize proposal ID: REC→RECP, CEC→CECP."""
    pid = pid.upper()
    if pid.startswith('REC') and not pid.startswith('RECC') and not pid.startswith('RECP'):
        pid = 'RECP' + pid[3:]
    if pid.startswith('CEC') and not pid.startswith('CECC') and not pid.startswith('CECP'):
        pid = 'CECP' + pid[3:]
    return pid


def _match_proposal_uid(f, fl, proposals, cdp_id_lookup):
    """Determine doc_type and proposal_uid for a file. Returns (doc_type, proposal_uid)."""
    doc_type = None
    proposal_uid = None

    # --- Priority 1: Comment Ready files (these are proposal text, best quality) ---
    m = COMMENT_READY_RE.match(f)
    if m:
        doc_type = 'proposal_docx'
        pid = _normalize_proposal_id(m.group(1))
        if pid in proposals:
            proposal_uid = proposals[pid]['uid']
        return doc_type, proposal_uid

    # --- Priority 2: cdpACCESS proposal pattern ---
    m = CDP_PROPOSAL_RE.match(f)
    if m and 'modification' not in fl:
        doc_type = 'proposal_docx'
        pid = _normalize_proposal_id(m.group(1))
        if pid in proposals:
            proposal_uid = proposals[pid]['uid']
        return doc_type, proposal_uid

    # --- Priority 3: Numeric cdpACCESS pattern ---
    m = CDP_PROPOSAL_NUMERIC_RE.match(f)
    if m and 'modification' not in fl:
        doc_type = 'proposal_docx'
        cdp_id = m.group(1)
        if cdp_id in cdp_id_lookup:
            proposal_uid = cdp_id_lookup[cdp_id]['uid']
        return doc_type, proposal_uid

    # --- Priority 4: cdpACCESS modification ---
    m = CDP_MOD_RE.match(f)
    if m:
        doc_type = 'modification_docx'
        pid = _normalize_proposal_id(m.group(1))
        if pid in proposals:
            proposal_uid = proposals[pid]['uid']
        return doc_type, proposal_uid

    # --- Priority 5: Standalone modification files ---
    m = STANDALONE_MOD_RE.match(f)
    if m and fl.endswith('.docx'):
        doc_type = 'modification_docx'
        pid = _normalize_proposal_id(m.group(1))
        if pid in proposals:
            proposal_uid = proposals[pid]['uid']
        return doc_type, proposal_uid

    # --- Priority 6: MOD pattern in filename ---
    if MOD_DOCX_RE.search(f) and fl.endswith('.docx'):
        doc_type = 'modification_docx'
        # Try to extract proposal ID
        m = PROPOSAL_ID_RE.search(f)
        if m:
            pid = _normalize_proposal_id(m.group(1))
            if pid in proposals:
                proposal_uid = proposals[pid]['uid']
        return doc_type, proposal_uid

    # --- Priority 7: Circ form files ---
    for circ_re in [STANDALONE_CIRC_RE, CIRC_FIRST_RE]:
        m = circ_re.search(f)
        if m and fl.endswith('.docx'):
            doc_type = 'circ_form_docx'
            pid = _normalize_proposal_id(m.group(1))
            if pid in proposals:
                proposal_uid = proposals[pid]['uid']
            return doc_type, proposal_uid

    # --- Priority 8: Other doc types by pattern ---
    for dtype, pattern in DOC_TYPE_PATTERNS.items():
        if pattern.search(f):
            doc_type = dtype
            # Try to match a proposal ID from filename
            m = PROPOSAL_ID_RE.search(f)
            if m:
                pid = _normalize_proposal_id(m.group(1))
                if pid in proposals:
                    proposal_uid = proposals[pid]['uid']
            return doc_type, proposal_uid

    # --- Priority 9: Monograph/PCD PDFs ---
    if fl.endswith('.pdf'):
        if 'public comment' in fl and 'monograph' in fl:
            return 'monograph_pdf', None
        elif 'public comment draft' in fl:
            return 'pcd_pdf', None
        elif 'committee action' in fl or ' car ' in fl.replace('(', ' ').replace(')', ' '):
            return 'committee_action_report', None
        elif 'ballot' in fl:
            return 'ballot_pdf', None

    # --- Priority 10: Generic DOCX/PDF with a proposal ID ---
    if fl.endswith('.docx') or fl.endswith('.pdf'):
        m = PROPOSAL_ID_RE.search(f)
        if m:
            pid = _normalize_proposal_id(m.group(1))
            if pid in proposals:
                proposal_uid = proposals[pid]['uid']
                doc_type = 'other'
                return doc_type, proposal_uid

    return None, None


def scan_files(conn, source_folders=None):
    """Scan source folders and register files in documents table."""
    if source_folders is None:
        source_folders = SOURCE_FOLDERS

    cur = conn.cursor()

    # Load proposal registry for matching
    cur.execute("SELECT proposal_uid, canonical_id, track, cdpaccess_id FROM proposals")
    proposals = {}
    cdp_id_lookup = {}  # cdpaccess_id → proposal info
    for uid, cid, track, cdp_id in cur.fetchall():
        proposals[cid.upper()] = {'uid': uid, 'track': track, 'cdp_id': cdp_id}
        # Also index without the -25 suffix for looser matching
        base = cid.upper().split('-')[0]
        if base not in proposals:
            proposals[base] = {'uid': uid, 'track': track, 'cdp_id': cdp_id}
        # Index by cdpaccess_id for numeric-pattern files
        if cdp_id:
            cdp_id_lookup[str(cdp_id)] = {'uid': uid, 'track': track}

    registered = 0
    skipped = 0

    for source_folder in source_folders:
        if not os.path.exists(source_folder):
            print(f"  SKIP folder (not found): {source_folder}")
            continue

        folder_name = os.path.basename(source_folder)
        folder_registered = 0

        for root, dirs, files in os.walk(source_folder):
            # Determine track from path
            rel_path = root.replace(source_folder, '').lstrip(os.sep).lower()
            if rel_path.startswith('commercial') or '/commercial' in rel_path:
                track = 'commercial'
            elif rel_path.startswith('residential') or '/residential' in rel_path:
                track = 'residential'
            else:
                track = None

            for f in files:
                if f.startswith('~$'):  # Skip temp files
                    continue

                path = os.path.join(root, f)
                fl = f.lower()

                if not (fl.endswith('.docx') or fl.endswith('.pdf') or fl.endswith('.vtt') or fl.endswith('.xlsx')):
                    continue

                # Classify the file
                doc_type, proposal_uid = _match_proposal_uid(f, fl, proposals, cdp_id_lookup)

                if not doc_type:
                    # For xlsx files, classify generically if in a meaningful folder
                    if fl.endswith('.xlsx'):
                        doc_type = 'spreadsheet'
                    elif fl.endswith('.vtt'):
                        doc_type = 'transcript_vtt'
                    else:
                        continue  # Skip unclassifiable files

                # Register the file
                try:
                    file_size = os.path.getsize(path)
                    cur.execute("""
                        INSERT OR IGNORE INTO documents
                        (proposal_uid, track, doc_type, file_name, file_path, file_size)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (proposal_uid, track, doc_type, f, path, file_size))
                    if cur.rowcount > 0:
                        registered += 1
                        folder_registered += 1
                    else:
                        skipped += 1
                except Exception as e:
                    print(f"  ERROR registering {f}: {e}")

        print(f"  {folder_name}: {folder_registered} new files registered")

    conn.commit()
    return registered, skipped


# ============================================================
# CONTENT EXTRACTION — Parse registered DOCX files
# ============================================================

def extract_proposals(conn):
    """Parse all unprocessed proposal DOCX files and populate proposal_text."""
    cur = conn.cursor()

    # Find unprocessed proposal DOCX files that have a matched proposal_uid
    cur.execute("""
        SELECT d.id, d.proposal_uid, d.file_path, d.file_name
        FROM documents d
        WHERE d.doc_type = 'proposal_docx'
          AND d.processed = 0
          AND d.proposal_uid IS NOT NULL
    """)
    rows = cur.fetchall()

    extracted = 0
    errors = 0

    for doc_id, proposal_uid, file_path, file_name in rows:
        try:
            result = parse_proposal_docx(file_path)
            if not result:
                print(f"  SKIP (empty): {file_name}")
                continue

            # Insert into proposal_text
            cur.execute("""
                INSERT OR REPLACE INTO proposal_text
                (proposal_uid, source_type, source_path, proposal_html, proposal_plain,
                 reason_text, cost_impact_text, code_section_text)
                VALUES (?, 'cdpaccess_docx', ?, ?, ?, ?, ?, ?)
            """, (
                proposal_uid, file_path,
                result['proposal_html'], result['proposal_plain'],
                result['reason_text'], result['cost_impact_text'],
                result['code_section_text']
            ))

            # Mark document as processed
            cur.execute("UPDATE documents SET processed = 1, processed_at = datetime('now') WHERE id = ?", (doc_id,))

            extracted += 1
        except Exception as e:
            print(f"  ERROR parsing {file_name}: {e}")
            errors += 1

    conn.commit()
    return extracted, errors


def extract_modifications(conn):
    """Parse all unprocessed modification DOCX files and populate modifications table."""
    cur = conn.cursor()

    cur.execute("""
        SELECT d.id, d.proposal_uid, d.file_path, d.file_name, d.track
        FROM documents d
        WHERE d.doc_type = 'modification_docx'
          AND d.processed = 0
          AND d.proposal_uid IS NOT NULL
    """)
    rows = cur.fetchall()

    extracted = 0
    errors = 0

    for doc_id, proposal_uid, file_path, file_name, track in rows:
        try:
            result = parse_proposal_docx(file_path)  # Same format as proposals
            if not result:
                print(f"  SKIP (empty mod): {file_name}")
                continue

            cur.execute("""
                INSERT INTO modifications
                (proposal_uid, track, source_path, modification_html, modification_plain,
                 reason_text, status)
                VALUES (?, ?, ?, ?, ?, ?, 'received')
            """, (
                proposal_uid, track or 'commercial', file_path,
                result['proposal_html'], result['proposal_plain'],
                result['reason_text']
            ))

            cur.execute("UPDATE documents SET processed = 1, processed_at = datetime('now') WHERE id = ?", (doc_id,))

            extracted += 1
        except Exception as e:
            print(f"  ERROR parsing mod {file_name}: {e}")
            errors += 1

    conn.commit()
    return extracted, errors


# ============================================================
# AUTO-LINK — Detect cross-references between proposals
# ============================================================

def auto_link_same_section(conn):
    """Create 'same_section' links between proposals modifying the same code section."""
    cur = conn.cursor()

    # Find proposals with the same code_section that aren't already linked
    cur.execute("""
        SELECT a.proposal_uid, b.proposal_uid, a.code_section
        FROM proposals a
        JOIN proposals b ON a.code_section = b.code_section
            AND a.proposal_uid < b.proposal_uid
            AND a.track = b.track
        WHERE a.code_section IS NOT NULL
          AND a.code_section != ''
          AND NOT EXISTS (
            SELECT 1 FROM proposal_links
            WHERE (proposal_uid_a = a.proposal_uid AND proposal_uid_b = b.proposal_uid)
               OR (proposal_uid_a = b.proposal_uid AND proposal_uid_b = a.proposal_uid)
          )
    """)
    rows = cur.fetchall()

    linked = 0
    for uid_a, uid_b, section in rows:
        try:
            cur.execute("""
                INSERT OR IGNORE INTO proposal_links
                (proposal_uid_a, proposal_uid_b, link_type, created_by, notes)
                VALUES (?, ?, 'same_section', 'auto_scanner', ?)
            """, (uid_a, uid_b, f"Both modify {section}"))
            if cur.rowcount > 0:
                linked += 1
        except Exception:
            pass

    conn.commit()
    return linked


# ============================================================
# STATS — Report on current state
# ============================================================

def print_stats(conn):
    """Print current state of all content tables."""
    cur = conn.cursor()

    print("=" * 60)
    print("CENTRALIZED CONTENT DATABASE STATUS")
    print("=" * 60)

    # Documents
    cur.execute("SELECT COUNT(*) FROM documents")
    total_docs = cur.fetchone()[0]
    cur.execute("SELECT doc_type, COUNT(*), SUM(processed) FROM documents GROUP BY doc_type ORDER BY COUNT(*) DESC")
    print(f"\n📁 documents: {total_docs} files registered")
    for dtype, count, processed in cur.fetchall():
        processed = processed or 0
        print(f"   {dtype}: {count} ({processed} processed)")

    # Proposal text
    cur.execute("SELECT COUNT(*) FROM proposal_text")
    total_pt = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM proposals")
    total_p = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM proposal_text WHERE proposal_html != '' AND proposal_html IS NOT NULL")
    with_html = cur.fetchone()[0]
    print(f"\n📝 proposal_text: {total_pt} / {total_p} proposals have extracted text")
    print(f"   {with_html} have HTML markup")

    # Show coverage by track
    cur.execute("""
        SELECT p.track, COUNT(DISTINCT p.proposal_uid) as total,
               COUNT(DISTINCT pt.proposal_uid) as extracted
        FROM proposals p
        LEFT JOIN proposal_text pt ON p.proposal_uid = pt.proposal_uid
        GROUP BY p.track
    """)
    for track, total, extracted in cur.fetchall():
        pct = (extracted / total * 100) if total > 0 else 0
        print(f"   {track}: {extracted}/{total} ({pct:.0f}%)")

    # Modifications
    cur.execute("SELECT COUNT(*) FROM modifications")
    total_mods = cur.fetchone()[0]
    print(f"\n📋 modifications: {total_mods} pre-submitted modifications tracked")

    # Proposal links
    cur.execute("SELECT link_type, COUNT(*) FROM proposal_links GROUP BY link_type")
    links = cur.fetchall()
    total_links = sum(c for _, c in links)
    print(f"\n🔗 proposal_links: {total_links} cross-references")
    for ltype, count in links:
        print(f"   {ltype}: {count}")

    # Meeting events
    cur.execute("SELECT COUNT(*) FROM meeting_events")
    total_events = cur.fetchone()[0]
    print(f"\n🎯 meeting_events: {total_events} events recorded")

    # Unmatched documents (no proposal_uid)
    cur.execute("SELECT COUNT(*) FROM documents WHERE proposal_uid IS NULL AND doc_type IN ('proposal_docx', 'modification_docx')")
    unmatched = cur.fetchone()[0]
    if unmatched > 0:
        print(f"\n⚠️  {unmatched} proposal/modification files couldn't be matched to a proposal in the database")

    print()


# ============================================================
# MAIN
# ============================================================

def main():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        sys.exit(1)

    # Check which source folders exist
    available_folders = [f for f in SOURCE_FOLDERS if os.path.exists(f)]
    if not available_folders:
        print("ERROR: No source folders found. Expected at least one of:")
        for f in SOURCE_FOLDERS:
            print(f"  {f}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")

    if '--stats' in sys.argv:
        print_stats(conn)
        conn.close()
        return

    print("=" * 60)
    print("IECC Content Population Pipeline")
    print(f"Database: {DB_PATH}")
    print(f"Sources:")
    for f in SOURCE_FOLDERS:
        exists = "✓" if os.path.exists(f) else "✗"
        print(f"  [{exists}] {os.path.basename(f)}")
    print(f"Time:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Step 1: Scan files
    print("\n[1/4] Scanning source folders...")
    registered, skipped = scan_files(conn)
    print(f"  Total: {registered} new files ({skipped} already known)")

    if '--scan-only' in sys.argv:
        print_stats(conn)
        conn.close()
        return

    # Step 2: Extract proposal language
    print("\n[2/4] Extracting proposal language from DOCX files...")
    extracted, errors = extract_proposals(conn)
    print(f"  Extracted {extracted} proposals ({errors} errors)")

    # Step 3: Extract modifications
    print("\n[3/4] Extracting modification language from DOCX files...")
    mod_extracted, mod_errors = extract_modifications(conn)
    print(f"  Extracted {mod_extracted} modifications ({mod_errors} errors)")

    # Step 4: Auto-link proposals
    print("\n[4/4] Auto-linking proposals by code section...")
    linked = auto_link_same_section(conn)
    print(f"  Created {linked} cross-reference links")

    # Final stats
    print_stats(conn)

    conn.close()
    print("Done!")


if __name__ == '__main__':
    main()
