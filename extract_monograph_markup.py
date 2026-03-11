#!/usr/bin/env python3
"""
extract_monograph_markup.py — Extract proposal text with legislative markup
from the Public Comment Monograph PDF.

The monograph PDF renders underline and strikethrough as drawn lines.
This script correlates those lines with character positions to reconstruct
<ins>/<del> HTML tags, then updates proposal_text in iecc.db.

Usage:
  python3 extract_monograph_markup.py <monograph.pdf>
  python3 extract_monograph_markup.py <monograph.pdf> --dry-run   # Preview without writing DB
  python3 extract_monograph_markup.py <monograph.pdf> --proposal REPC33-25  # Single proposal
"""

import fitz  # pymupdf
import sqlite3
import sys
import os
import re
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'iecc.db')

# Proposal ID patterns in the monograph
PROPOSAL_ID_RE = re.compile(
    r'^(CEPC\d+-\d+(?:\s+Part\s+[IVX]+)?|REPC\d+-\d+|'
    r'CECP\d+-\d+|RECP\d+-\d+|REC\d+-\d+|CEC\d+-\d+|'
    r'CECC\d+-\d+|RECC\d+-\d+|IRCEPC\d+-\d+)$',
    re.IGNORECASE
)


def normalize_proposal_id(pid):
    """Normalize proposal IDs to match DB canonical_id format."""
    pid = pid.strip().upper()
    # REC -> RECP (proponent comments)
    if pid.startswith('REC') and not pid.startswith('RECC') and not pid.startswith('RECP') and not pid.startswith('REPC'):
        pid = 'RECP' + pid[3:]
    # CEC -> CECP
    if pid.startswith('CEC') and not pid.startswith('CECC') and not pid.startswith('CECP') and not pid.startswith('CEPC'):
        pid = 'CECP' + pid[3:]
    return pid


def get_page_markup(page):
    """
    Extract all horizontal drawn lines from a PDF page.
    Returns lists of strikethrough and underline line segments.
    """
    lines = []
    for d in page.get_drawings():
        for item in d['items']:
            if item[0] == 'l':  # line element
                p1, p2 = item[1], item[2]
                if abs(p1.y - p2.y) < 1:  # horizontal line
                    lines.append({
                        'y': p1.y,
                        'x0': min(p1.x, p2.x),
                        'x1': max(p1.x, p2.x),
                        'width': d.get('width', 0),
                        'color': d.get('color'),
                    })
    return lines


def classify_line_for_char(line_y, char_bbox, char_origin_y):
    """
    Determine if a horizontal line is a strikethrough or underline
    relative to a character.

    Strikethrough: line passes through the middle of the character
    Underline: line is at or below the baseline
    """
    mid_y = (char_bbox.y0 + char_bbox.y1) / 2

    # The line is a strikethrough if it's above the baseline and near the middle
    if line_y < char_origin_y - 0.5:
        return 'strike'
    else:
        return 'underline'


def extract_page_text_with_markup(page):
    """
    Extract text from a page, with <ins> and <del> tags based on
    drawn underline/strikethrough lines.

    Returns HTML string.
    """
    # Get drawn lines
    markup_lines = get_page_markup(page)
    if not markup_lines:
        # No drawn lines = no markup, just return plain text
        return page.get_text(), False

    # Get character-level data
    blocks = page.get_text('rawdict')['blocks']

    # Build the page content with markup
    html_parts = []
    current_para = []
    last_y = None

    for block in blocks:
        if 'lines' not in block:
            continue
        for line in block['lines']:
            line_y_base = line['bbox'][1]

            # Detect paragraph break (significant Y jump)
            if last_y is not None and abs(line_y_base - last_y) > 3:
                if current_para:
                    html_parts.append(_flush_para(current_para))
                    current_para = []
            last_y = line['bbox'][3]  # bottom of line

            last_char_x1 = None  # Track rightmost x of last character for gap detection

            for span in line['spans']:
                if 'chars' not in span or not span['chars']:
                    # Fallback: use span text directly
                    text = span['text']
                    if text.strip():
                        font = span['font']
                        is_bold = 'Bold' in font or 'bold' in font
                        is_italic = 'Ital' in font or 'Obli' in font
                        # Check for x-gap indicating a space between spans
                        if last_char_x1 is not None and current_para and \
                           current_para[-1]['text'] and not current_para[-1]['text'][-1].isspace():
                            span_x0 = span['bbox'][0]
                            gap = span_x0 - last_char_x1
                            if gap > 2:  # More than 2px gap = space
                                current_para[-1]['text'] += ' '
                        current_para.append({
                            'text': text,
                            'bold': is_bold,
                            'italic': is_italic,
                            'strike': False,
                            'underline': False,
                        })
                    last_char_x1 = span['bbox'][2]  # right edge of span
                    continue

                # Detect space gap between this span and previous content
                first_char = span['chars'][0]
                first_char_x0 = first_char['bbox'][0]
                if last_char_x1 is not None and current_para and \
                   current_para[-1]['text'] and not current_para[-1]['text'][-1].isspace():
                    gap = first_char_x0 - last_char_x1
                    if gap > 2:  # More than 2px gap = space between spans
                        current_para[-1]['text'] += ' '

                # Process character by character
                char_groups = []
                current_group = None

                for ch in span['chars']:
                    char_bbox = fitz.Rect(ch['bbox'])
                    char_origin_y = ch['origin'][1]
                    char_x_mid = (char_bbox.x0 + char_bbox.x1) / 2

                    # Detect intra-span space gaps (e.g., space chars rendered as gaps)
                    if last_char_x1 is not None:
                        gap = char_bbox.x0 - last_char_x1
                        if gap > 2 and current_group and current_group['text'] and \
                           not current_group['text'][-1].isspace():
                            current_group['text'] += ' '

                    last_char_x1 = char_bbox.x1  # Track for next iteration

                    # Check if any markup line overlaps this character
                    is_strike = False
                    is_underline = False

                    for ml in markup_lines:
                        # Check horizontal overlap
                        if char_x_mid >= ml['x0'] - 0.5 and char_x_mid <= ml['x1'] + 0.5:
                            # Check vertical proximity
                            mid_y = (char_bbox.y0 + char_bbox.y1) / 2
                            if abs(ml['y'] - mid_y) < 5 or abs(ml['y'] - char_origin_y) < 3:
                                line_type = classify_line_for_char(ml['y'], char_bbox, char_origin_y)
                                if line_type == 'strike':
                                    is_strike = True
                                else:
                                    is_underline = True

                    font = span['font']
                    is_bold = 'Bold' in font or 'bold' in font
                    is_italic = 'Ital' in font or 'Obli' in font

                    # Group consecutive chars with same formatting
                    fmt = (is_bold, is_italic, is_strike, is_underline)
                    if current_group and current_group['fmt'] == fmt:
                        current_group['text'] += ch['c']
                    else:
                        if current_group:
                            char_groups.append(current_group)
                        current_group = {
                            'text': ch['c'],
                            'fmt': fmt,
                            'bold': is_bold,
                            'italic': is_italic,
                            'strike': is_strike,
                            'underline': is_underline,
                        }

                if current_group:
                    char_groups.append(current_group)

                current_para.extend(char_groups)

            # Insert space at PDF line boundary to prevent word fusion
            # when text wraps across visual lines within the same paragraph.
            # Without this, "performance" at end of line 1 and "path" at
            # start of line 2 would fuse into "performancepath".
            if current_para and current_para[-1]['text'] and \
               not current_para[-1]['text'][-1].isspace():
                current_para[-1]['text'] += ' '

    if current_para:
        html_parts.append(_flush_para(current_para))

    has_markup = any('<ins>' in p or '<del>' in p for p in html_parts)
    return '\n'.join(html_parts), has_markup


def _flush_para(groups):
    """Convert a list of formatted text groups into an HTML paragraph."""
    if not groups:
        return ''

    html = []
    for g in groups:
        text = _escape(g['text'])
        if not text:
            continue
        if g.get('strike'):
            text = f'<del>{text}</del>'
        if g.get('underline'):
            text = f'<ins>{text}</ins>'
        if g.get('bold'):
            text = f'<b>{text}</b>'
        if g.get('italic'):
            text = f'<i>{text}</i>'
        html.append(text)

    content = ''.join(html)
    if not content.strip():
        return ''
    return f'<p>{content}</p>'


def _escape(text):
    """HTML-escape text."""
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def split_monograph_into_proposals(pdf_path):
    """
    Split the monograph PDF into per-proposal page ranges.
    Returns list of (canonical_id, start_page, end_page).
    """
    doc = fitz.open(pdf_path)
    proposals = []

    for page_num in range(doc.page_count):
        page = doc[page_num]
        blocks = page.get_text('dict')['blocks']

        # Check first few text blocks for a proposal ID
        for block in blocks[:5]:
            if 'lines' not in block:
                continue
            for line in block['lines']:
                for span in line['spans']:
                    text = span['text'].strip()
                    size = span['size']
                    # Proposal IDs are large font (>12pt) at top of page
                    if size > 12 and PROPOSAL_ID_RE.match(text):
                        normalized = normalize_proposal_id(text)
                        proposals.append({
                            'raw_id': text,
                            'canonical_id': normalized,
                            'start_page': page_num,
                        })

    # Set end pages
    for i in range(len(proposals) - 1):
        proposals[i]['end_page'] = proposals[i + 1]['start_page'] - 1
    if proposals:
        proposals[-1]['end_page'] = doc.page_count - 1

    doc.close()
    return proposals


def extract_proposal_from_pages(pdf_path, start_page, end_page):
    """
    Extract a single proposal's content from a range of pages.
    Returns dict with proposal_html, proposal_plain, reason_text, cost_impact_text.
    """
    doc = fitz.open(pdf_path)

    all_html = []
    has_any_markup = False

    for page_num in range(start_page, end_page + 1):
        page = doc[page_num]
        page_html, has_markup = extract_page_text_with_markup(page)
        if has_markup:
            has_any_markup = True
        if isinstance(page_html, str) and '<p>' not in page_html:
            # Plain text fallback - wrap in paragraphs
            for line in page_html.split('\n'):
                line = line.strip()
                if line:
                    all_html.append(f'<p>{_escape(line)}</p>')
        else:
            all_html.append(page_html)

    doc.close()

    full_html = '\n'.join(all_html)

    # Extract plain text
    plain = re.sub(r'<[^>]+>', '', full_html)

    # Split into sections: code language, reason, cost impact
    result = {
        'proposal_html': '',
        'proposal_plain': '',
        'reason_text': '',
        'cost_impact_text': '',
        'has_markup': has_any_markup,
    }

    # Find section boundaries in the HTML
    html_lines = full_html.split('\n')

    in_code = False
    in_reason = False
    in_cost = False
    code_parts = []
    reason_parts = []
    cost_parts = []

    for line in html_lines:
        text = re.sub(r'<[^>]+>', '', line).strip().lower()

        if text.startswith('revise as follows') or text.startswith('add new') or \
           text.startswith('delete and substitute') or text.startswith('delete without'):
            in_code = True
            in_reason = False
            in_cost = False
            code_parts.append(line)
            continue

        if text.startswith('reason:') or text == 'reason':
            in_code = False
            in_reason = True
            in_cost = False
            continue

        if text.startswith('cost impact') or text.startswith('justification:'):
            in_code = False
            in_reason = False
            in_cost = True
            continue

        if in_code:
            code_parts.append(line)
        elif in_reason:
            reason_parts.append(re.sub(r'<[^>]+>', '', line).strip())
        elif in_cost:
            cost_parts.append(re.sub(r'<[^>]+>', '', line).strip())

    result['proposal_html'] = '\n'.join(code_parts)
    result['proposal_plain'] = re.sub(r'<[^>]+>', '', result['proposal_html'])
    result['reason_text'] = '\n'.join(p for p in reason_parts if p)
    result['cost_impact_text'] = '\n'.join(p for p in cost_parts if p)

    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 extract_monograph_markup.py <monograph.pdf> [--dry-run] [--proposal ID]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    dry_run = '--dry-run' in sys.argv
    single_proposal = None
    if '--proposal' in sys.argv:
        idx = sys.argv.index('--proposal')
        single_proposal = sys.argv[idx + 1].upper()

    if not os.path.exists(pdf_path):
        print(f"ERROR: PDF not found: {pdf_path}")
        sys.exit(1)

    print("=" * 60)
    print("MONOGRAPH MARKUP EXTRACTOR")
    print(f"PDF: {os.path.basename(pdf_path)}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE — will update iecc.db'}")
    if single_proposal:
        print(f"Single proposal: {single_proposal}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Step 1: Split monograph into proposals
    print("\n[1/3] Scanning monograph for proposal boundaries...")
    proposals = split_monograph_into_proposals(pdf_path)
    print(f"  Found {len(proposals)} proposals")

    if single_proposal:
        proposals = [p for p in proposals if p['canonical_id'] == single_proposal]
        if not proposals:
            print(f"  ERROR: Proposal {single_proposal} not found in monograph")
            sys.exit(1)

    # Step 2: Connect to DB and check which proposals need updating
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row

    # Build proposal_uid lookup
    uid_lookup = {}
    for row in conn.execute("SELECT proposal_uid, canonical_id FROM proposals").fetchall():
        uid_lookup[row['canonical_id'].upper()] = row['proposal_uid']

    # Step 3: Extract and update
    print(f"\n[2/3] Extracting proposal text with markup...")
    extracted = 0
    upgraded = 0
    skipped = 0
    errors = 0

    for p in proposals:
        cid = p['canonical_id']
        uid = uid_lookup.get(cid)

        if not uid:
            # Try without Part suffix
            base_cid = re.sub(r'\s+Part\s+.*$', '', cid, flags=re.IGNORECASE)
            uid = uid_lookup.get(base_cid)

        if not uid:
            skipped += 1
            continue

        try:
            result = extract_proposal_from_pages(pdf_path, p['start_page'], p['end_page'])

            if not result['proposal_html'].strip():
                skipped += 1
                continue

            # Check if this would be an upgrade (PDF→markup)
            existing = conn.execute(
                "SELECT source_type, proposal_html FROM proposal_text WHERE proposal_uid = ?",
                (uid,)
            ).fetchone()

            is_upgrade = False
            if existing:
                if existing['source_type'] == 'cdpaccess_docx':
                    # Already have good DOCX source, skip
                    skipped += 1
                    continue
                if result['has_markup']:
                    is_upgrade = True
                elif not result['has_markup'] and existing['source_type'] in ('monograph_pdf', 'cdpaccess_pdf'):
                    # No improvement
                    skipped += 1
                    continue

            marker = "UPGRADE" if is_upgrade else "NEW" if not existing else "REPLACE"
            markup_str = "WITH MARKUP" if result['has_markup'] else "no markup"
            print(f"  {marker}: {cid} (pages {p['start_page']+1}-{p['end_page']+1}) [{markup_str}]")

            if not dry_run:
                conn.execute("""
                    INSERT OR REPLACE INTO proposal_text
                    (proposal_uid, source_type, source_path, proposal_html, proposal_plain,
                     reason_text, cost_impact_text, code_section_text, notes)
                    VALUES (?, 'monograph_markup', ?, ?, ?, ?, ?, '',
                            'Extracted from Public Comment Monograph with underline/strikethrough markup detection.')
                """, (
                    uid, pdf_path,
                    result['proposal_html'], result['proposal_plain'],
                    result['reason_text'], result['cost_impact_text'],
                ))

            if is_upgrade:
                upgraded += 1
            extracted += 1

        except Exception as e:
            print(f"  ERROR on {cid}: {e}")
            errors += 1

    if not dry_run:
        conn.commit()
        conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')

    conn.close()

    print(f"\n[3/3] Summary")
    print(f"  Extracted: {extracted} proposals")
    print(f"  Upgraded (PDF→markup): {upgraded}")
    print(f"  Skipped: {skipped}")
    print(f"  Errors: {errors}")
    print("Done!")


if __name__ == '__main__':
    main()
