"""Generate Word documents for agendas and circulation forms.
Uses python-docx for simplicity since these are straightforward table-based docs.
"""
import subprocess
import tempfile
import os
from pathlib import Path

# Directory containing node_modules/docx — used as cwd for Node.js subprocess
_WEB_DIR = str(Path(__file__).resolve().parent.parent)
_NODE_MODULES = str(Path(__file__).resolve().parent.parent / "node_modules")


def _node_env():
    """Return environment dict with NODE_PATH set so temp scripts find docx."""
    env = os.environ.copy()
    env["NODE_PATH"] = _NODE_MODULES
    return env


def _run_node_script(script_path: str) -> bytes:
    """Run a Node.js script that writes a docx buffer to stdout."""
    result = subprocess.run(
        ["node", script_path],
        capture_output=True,
        timeout=30,
        env=_node_env(),
    )
    if result.returncode != 0:
        raise RuntimeError(f"Doc generation failed: {result.stderr.decode()}")
    return result.stdout


def generate_agenda_docx(meeting: dict, agenda_items: list) -> bytes:
    """Generate a meeting agenda as a Word document.

    Args:
        meeting: dict with keys: body, meeting_date, meeting_time, track, phase
        agenda_items: list of dicts with keys: canonical_id, proponent, proponent_email, code_section
    Returns:
        bytes of the .docx file
    """
    # Build a Node script dynamically using docx-js
    items_js = []
    for i, item in enumerate(agenda_items):
        cid = _esc(item.get("canonical_id", ""))
        proponent = _esc(item.get("proponent", "—"))
        email = _esc(item.get("proponent_email", ""))
        section = _esc(item.get("code_section", ""))
        items_js.append(f'{{num: {i+1}, id: "{cid}", proponent: "{proponent}", email: "{email}", section: "{section}"}}')

    body = _esc(meeting.get("body", ""))
    date = _esc(meeting.get("meeting_date", ""))
    raw_time = meeting.get("meeting_time", "") or ""
    time = _esc(raw_time)
    date_line = f"{date} at {time}" if raw_time else date
    track = _esc(meeting.get("track", ""))

    script = f"""
const fs = require("fs");
const {{ Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
         AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType,
         LevelFormat, Header, Footer, PageNumber }} = require("docx");

const items = [{", ".join(items_js)}];

const border = {{ style: BorderStyle.SINGLE, size: 1, color: "999999" }};
const borders = {{ top: border, bottom: border, left: border, right: border }};
const cellMargins = {{ top: 60, bottom: 60, left: 100, right: 100 }};

function cell(text, opts = {{}}) {{
    return new TableCell({{
        borders,
        width: {{ size: opts.width || 2000, type: WidthType.DXA }},
        margins: cellMargins,
        shading: opts.header ? {{ fill: "1B3A5C", type: ShadingType.CLEAR }} : undefined,
        children: [new Paragraph({{
            spacing: {{ after: 0 }},
            children: [new TextRun({{
                text: text,
                font: "Arial",
                size: opts.size || 20,
                bold: opts.bold || false,
                color: opts.header ? "FFFFFF" : "000000"
            }})]
        }})]
    }});
}}

const headerRow = new TableRow({{
    children: [
        cell("#", {{ width: 600, header: true, bold: true }}),
        cell("Proposal", {{ width: 1800, header: true, bold: true }}),
        cell("Proponent", {{ width: 3200, header: true, bold: true }}),
        cell("Email", {{ width: 3760, header: true, bold: true }}),
    ]
}});

const dataRows = items.map(item => new TableRow({{
    children: [
        cell(String(item.num), {{ width: 600 }}),
        cell(item.id, {{ width: 1800, bold: true }}),
        cell(item.proponent, {{ width: 3200 }}),
        cell(item.email, {{ width: 3760, size: 18 }}),
    ]
}}));

const doc = new Document({{
    styles: {{
        default: {{ document: {{ run: {{ font: "Arial", size: 22 }} }} }}
    }},
    numbering: {{
        config: [{{
            reference: "agenda-nums",
            levels: [{{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
                style: {{ paragraph: {{ indent: {{ left: 360, hanging: 360 }} }} }} }}]
        }}]
    }},
    sections: [{{
        properties: {{
            page: {{
                size: {{ width: 12240, height: 15840 }},
                margin: {{ top: 1080, right: 1080, bottom: 1080, left: 1080 }}
            }}
        }},
        headers: {{
            default: new Header({{ children: [
                new Paragraph({{
                    alignment: AlignmentType.CENTER,
                    children: [new TextRun({{ text: "International Energy Conservation Code", font: "Arial", size: 20, color: "666666", italics: true }})]
                }})
            ] }})
        }},
        footers: {{
            default: new Footer({{ children: [
                new Paragraph({{
                    alignment: AlignmentType.CENTER,
                    children: [
                        new TextRun({{ text: "Page ", font: "Arial", size: 16, color: "999999" }}),
                        new TextRun({{ children: [PageNumber.CURRENT], font: "Arial", size: 16, color: "999999" }})
                    ]
                }})
            ] }})
        }},
        children: [
            new Paragraph({{
                alignment: AlignmentType.CENTER,
                spacing: {{ after: 40 }},
                children: [new TextRun({{ text: "International Energy Conservation Code", font: "Arial", size: 28, bold: true }})]
            }}),
            new Paragraph({{
                alignment: AlignmentType.CENTER,
                spacing: {{ after: 40 }},
                children: [new TextRun({{ text: "{body}", font: "Arial", size: 24, bold: true }})]
            }}),
            new Paragraph({{
                alignment: AlignmentType.CENTER,
                spacing: {{ after: 80 }},
                children: [new TextRun({{ text: "Meeting Agenda", font: "Arial", size: 24 }})]
            }}),
            new Paragraph({{
                alignment: AlignmentType.CENTER,
                spacing: {{ after: 40 }},
                children: [new TextRun({{ text: "{date_line}", font: "Arial", size: 22 }})]
            }}),
            new Paragraph({{ spacing: {{ after: 200 }}, children: [] }}),

            // Standard agenda items
            new Paragraph({{ numbering: {{ reference: "agenda-nums", level: 0 }}, spacing: {{ after: 80 }},
                children: [new TextRun({{ text: "Call to order", font: "Arial", size: 22 }})] }}),
            new Paragraph({{ numbering: {{ reference: "agenda-nums", level: 0 }}, spacing: {{ after: 80 }},
                children: [new TextRun({{ text: "Meeting conduct \\u2014 Identification of Representation / Conflict of Interest / Antitrust / Copyright", font: "Arial", size: 22 }})] }}),
            new Paragraph({{ numbering: {{ reference: "agenda-nums", level: 0 }}, spacing: {{ after: 80 }},
                children: [new TextRun({{ text: "Roll call (subcommittee members) \\u2014 interested parties sign in via chat", font: "Arial", size: 22 }})] }}),
            new Paragraph({{ numbering: {{ reference: "agenda-nums", level: 0 }}, spacing: {{ after: 80 }},
                children: [new TextRun({{ text: "Administrative items", font: "Arial", size: 22 }})] }}),
            new Paragraph({{ numbering: {{ reference: "agenda-nums", level: 0 }}, spacing: {{ after: 80 }},
                children: [new TextRun({{ text: "Modifications \\u2014 shall be submitted through cdpACCESS", font: "Arial", size: 22 }})] }}),
            new Paragraph({{ numbering: {{ reference: "agenda-nums", level: 0 }}, spacing: {{ after: 200 }},
                children: [new TextRun({{ text: "Proposal Deliberation", font: "Arial", size: 22, bold: true }})] }}),

            // Proposal table
            new Table({{
                width: {{ size: 9360, type: WidthType.DXA }},
                columnWidths: [600, 1800, 3200, 3760],
                rows: [headerRow, ...dataRows]
            }}),

            new Paragraph({{ spacing: {{ before: 200, after: 80 }}, children: [] }}),
            new Paragraph({{ numbering: {{ reference: "agenda-nums", level: 0 }}, spacing: {{ after: 80 }},
                children: [new TextRun({{ text: "Other business", font: "Arial", size: 22 }})] }}),
            new Paragraph({{ numbering: {{ reference: "agenda-nums", level: 0 }}, spacing: {{ after: 80 }},
                children: [new TextRun({{ text: "Adjournment", font: "Arial", size: 22 }})] }}),
        ]
    }}]
}});

Packer.toBuffer(doc).then(buf => {{
    process.stdout.write(buf);
}});
"""

    # Write script to temp file and run
    with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False,
                                      dir=tempfile.gettempdir()) as f:
        f.write(script)
        f.flush()
        try:
            result = subprocess.run(
                ["node", f.name],
                capture_output=True,
                timeout=30,
                cwd=_WEB_DIR,
                env=_node_env(),
            )
            if result.returncode != 0:
                raise RuntimeError(f"Agenda generation failed: {result.stderr.decode()[:500]}")
            return result.stdout
        finally:
            os.unlink(f.name)


def generate_circform_docx(meeting: dict, actions: list) -> bytes:
    """Generate a circulation form as a Word document.

    Args:
        meeting: dict with keys: body, meeting_date, track
        actions: list of dicts with keys: canonical_id, recommendation, vote_for, vote_against,
                 vote_not_voting, reason, modification_text
    Returns:
        bytes of the .docx file
    """
    rows_js = []
    for a in actions:
        cid = _esc(a.get("canonical_id", ""))
        rec = _esc(a.get("recommendation", ""))
        vf = a.get("vote_for", "")
        va = a.get("vote_against", "")
        vnv = a.get("vote_not_voting", "")
        vote_str = f"{vf}-{va}-{vnv}" if vf is not None else ""
        reason = _esc(a.get("reason", "") or "")
        mod = _esc(a.get("modification_text", "") or "")
        section = _esc(a.get("code_section", "") or "")
        rows_js.append(f'{{id:"{cid}",rec:"{rec}",vote:"{vote_str}",reason:"{reason}",mod:"{mod}",section:"{section}"}}')

    body = _esc(meeting.get("body", ""))
    date = _esc(meeting.get("meeting_date", ""))
    track = _esc(meeting.get("track", ""))

    script = f"""
const fs = require("fs");
const {{ Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
         AlignmentType, BorderStyle, WidthType, ShadingType, PageBreak }} = require("docx");

const actions = [{", ".join(rows_js)}];

const border = {{ style: BorderStyle.SINGLE, size: 1, color: "999999" }};
const borders = {{ top: border, bottom: border, left: border, right: border }};
const margins = {{ top: 60, bottom: 60, left: 100, right: 100 }};

function labelCell(text, width) {{
    return new TableCell({{
        borders, margins, width: {{ size: width, type: WidthType.DXA }},
        shading: {{ fill: "E8E8E8", type: ShadingType.CLEAR }},
        children: [new Paragraph({{ spacing: {{ after: 0 }},
            children: [new TextRun({{ text, font: "Arial", size: 18, bold: true }})] }})]
    }});
}}

function valCell(text, width) {{
    return new TableCell({{
        borders, margins, width: {{ size: width, type: WidthType.DXA }},
        children: [new Paragraph({{ spacing: {{ after: 0 }},
            children: [new TextRun({{ text: text || "\\u2014", font: "Arial", size: 18 }})] }})]
    }});
}}

{PARSE_MOD_HTML_JS}

const children = [
    new Paragraph({{
        alignment: AlignmentType.CENTER, spacing: {{ after: 40 }},
        children: [new TextRun({{ text: "International Energy Conservation Code", font: "Arial", size: 24, bold: true }})]
    }}),
    new Paragraph({{
        alignment: AlignmentType.CENTER, spacing: {{ after: 40 }},
        children: [new TextRun({{ text: "Code Change Proposal Tracking Sheet", font: "Arial", size: 22 }})]
    }}),
    new Paragraph({{
        alignment: AlignmentType.CENTER, spacing: {{ after: 40 }},
        children: [new TextRun({{ text: "{body} \\u2014 {date}", font: "Arial", size: 20, color: "666666" }})]
    }}),
    new Paragraph({{ spacing: {{ after: 200 }}, children: [] }}),
];

actions.forEach((a, idx) => {{
    if (idx > 0) {{
        children.push(new Paragraph({{ spacing: {{ before: 200, after: 100 }}, children: [] }}));
    }}

    const rows = [
        new TableRow({{ children: [labelCell("Proposal #", 2400), valCell(a.id, 6960)] }}),
        new TableRow({{ children: [labelCell("Code", 2400), valCell("2027 IECC", 6960)] }}),
        new TableRow({{ children: [labelCell("Code Section(s)", 2400), valCell(a.section, 6960)] }}),
        new TableRow({{ children: [labelCell("Subcommittee", 2400), valCell("{body}", 6960)] }}),
        new TableRow({{ children: [labelCell("Recommendation", 2400), valCell(a.rec, 6960)] }}),
        new TableRow({{ children: [labelCell("Vote", 2400), valCell(a.vote, 6960)] }}),
        new TableRow({{ children: [labelCell("Reason Statement", 2400), valCell(a.reason, 6960)] }}),
    ];

    if (a.mod) {{
        rows.push(new TableRow({{ children: [labelCell("Modification", 2400), richModCell(a.mod, 6960)] }}));
    }}

    rows.push(new TableRow({{ children: [labelCell("Recommendation Date", 2400), valCell("{date}", 6960)] }}));

    children.push(new Table({{
        width: {{ size: 9360, type: WidthType.DXA }},
        columnWidths: [2400, 6960],
        rows: rows
    }}));
}});

const doc = new Document({{
    styles: {{ default: {{ document: {{ run: {{ font: "Arial", size: 20 }} }} }} }},
    sections: [{{
        properties: {{
            page: {{
                size: {{ width: 12240, height: 15840 }},
                margin: {{ top: 1080, right: 1080, bottom: 1080, left: 1080 }}
            }}
        }},
        children: children
    }}]
}});

Packer.toBuffer(doc).then(buf => process.stdout.write(buf));
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False,
                                      dir=tempfile.gettempdir()) as f:
        f.write(script)
        f.flush()
        try:
            result = subprocess.run(
                ["node", f.name],
                capture_output=True,
                timeout=30,
                cwd=_WEB_DIR,
                env=_node_env(),
            )
            if result.returncode != 0:
                raise RuntimeError(f"Circ form generation failed: {result.stderr.decode()[:500]}")
            return result.stdout
        finally:
            os.unlink(f.name)


def generate_modification_docx(meeting: dict, actions: list) -> bytes:
    """Generate a modification document for staff to reference when entering into cdpACCESS.

    Only includes proposals with 'Modified' recommendations. Each proposal gets a
    structured entry showing the proposal ID, code section, vote, and the modification
    text formatted for easy transcription into CDP.

    Args:
        meeting: dict with meeting metadata
        actions: list of action dicts (only those with modification_text will be included)
    Returns:
        bytes of the .docx file
    """
    # Filter to only modified proposals
    modified = [a for a in actions if a.get("modification_text") and "Modified" in (a.get("recommendation") or "")]
    if not modified:
        raise ValueError("No modifications to export.")

    rows_js = []
    for a in modified:
        cid = _esc(a.get("canonical_id", ""))
        rec = _esc(a.get("recommendation", ""))
        vf = a.get("vote_for", "")
        va = a.get("vote_against", "")
        vnv = a.get("vote_not_voting", "")
        vote_str = f"{vf}-{va}-{vnv}" if vf is not None else ""
        reason = _esc(a.get("reason", "") or "")
        mod = _esc(a.get("modification_text", "") or "")
        section = _esc(a.get("code_section", "") or "")
        proponent = _esc(a.get("proponent", "") or "")
        rows_js.append(
            f'{{id:"{cid}",rec:"{rec}",vote:"{vote_str}",reason:"{reason}",'
            f'mod:"{mod}",section:"{section}",proponent:"{proponent}"}}'
        )

    body = _esc(meeting.get("body", ""))
    date = _esc(meeting.get("meeting_date", ""))
    track = _esc(meeting.get("track", ""))

    script = f"""
const fs = require("fs");
const {{ Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
         AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType,
         Header, Footer, PageNumber, PageBreak, TabStopType, TabStopPosition }} = require("docx");

const mods = [{", ".join(rows_js)}];

{PARSE_MOD_HTML_JS}

const border = {{ style: BorderStyle.SINGLE, size: 1, color: "BBBBBB" }};
const borders = {{ top: border, bottom: border, left: border, right: border }};
const noBorder = {{ style: BorderStyle.NONE, size: 0 }};
const noBorders = {{ top: noBorder, bottom: noBorder, left: noBorder, right: noBorder }};
const cellMargins = {{ top: 80, bottom: 80, left: 120, right: 120 }};

// Helper: label-value row for metadata table
function metaRow(label, value, labelW, valW) {{
    return new TableRow({{
        children: [
            new TableCell({{
                borders,
                width: {{ size: labelW, type: WidthType.DXA }},
                margins: cellMargins,
                shading: {{ fill: "1B3A5C", type: ShadingType.CLEAR }},
                children: [new Paragraph({{
                    spacing: {{ after: 0 }},
                    children: [new TextRun({{ text: label, font: "Arial", size: 18, bold: true, color: "FFFFFF" }})]
                }})]
            }}),
            new TableCell({{
                borders,
                width: {{ size: valW, type: WidthType.DXA }},
                margins: cellMargins,
                children: [new Paragraph({{
                    spacing: {{ after: 0 }},
                    children: [new TextRun({{ text: value || "\\u2014", font: "Arial", size: 18 }})]
                }})]
            }})
        ]
    }});
}}

const children = [];

// Title block
children.push(
    new Paragraph({{
        alignment: AlignmentType.CENTER,
        spacing: {{ after: 60 }},
        children: [new TextRun({{ text: "INTERNATIONAL ENERGY CONSERVATION CODE", font: "Arial", size: 26, bold: true, color: "1B3A5C" }})]
    }}),
    new Paragraph({{
        alignment: AlignmentType.CENTER,
        spacing: {{ after: 60 }},
        children: [new TextRun({{ text: "Modification Document", font: "Arial", size: 24, bold: true }})]
    }}),
    new Paragraph({{
        alignment: AlignmentType.CENTER,
        spacing: {{ after: 40 }},
        children: [new TextRun({{ text: "{body}", font: "Arial", size: 22 }})]
    }}),
    new Paragraph({{
        alignment: AlignmentType.CENTER,
        spacing: {{ after: 40 }},
        children: [new TextRun({{ text: "Meeting Date: {date}", font: "Arial", size: 20, color: "666666" }})]
    }}),
    new Paragraph({{
        alignment: AlignmentType.CENTER,
        spacing: {{ after: 200 }},
        children: [new TextRun({{ text: mods.length + " proposal(s) with modifications", font: "Arial", size: 20, italics: true, color: "888888" }})]
    }})
);

// Instruction block
children.push(
    new Paragraph({{
        spacing: {{ after: 60 }},
        shading: {{ type: ShadingType.CLEAR, fill: "FFF3CD" }},
        children: [new TextRun({{ text: "Instructions for cdpACCESS Entry:", font: "Arial", size: 18, bold: true }})]
    }}),
    new Paragraph({{
        spacing: {{ after: 60 }},
        shading: {{ type: ShadingType.CLEAR, fill: "FFF3CD" }},
        children: [new TextRun({{ text: "For each proposal below, open the proposal in cdpACCESS Build view. In the Content field, enter the modification text shown below. Use ", font: "Arial", size: 18 }}),
                   new TextRun({{ text: "strikethrough", font: "Arial", size: 18, strike: true }}),
                   new TextRun({{ text: " for deleted text and ", font: "Arial", size: 18 }}),
                   new TextRun({{ text: "underline", font: "Arial", size: 18, underline: {{ type: "single" }} }}),
                   new TextRun({{ text: " for new/added text. The modification language below shows the final text as approved by the subcommittee.", font: "Arial", size: 18 }})]
    }}),
    new Paragraph({{ spacing: {{ after: 300 }}, children: [] }})
);

// Each modified proposal
mods.forEach((m, idx) => {{
    if (idx > 0) {{
        children.push(new Paragraph({{ spacing: {{ before: 100, after: 100 }}, children: [new PageBreak()] }}));
    }}

    // Proposal header bar
    children.push(
        new Paragraph({{
            spacing: {{ after: 120 }},
            shading: {{ type: ShadingType.CLEAR, fill: "1B3A5C" }},
            children: [
                new TextRun({{ text: "  " + m.id, font: "Arial", size: 28, bold: true, color: "FFFFFF" }}),
                new TextRun({{ text: "    " + m.rec, font: "Arial", size: 22, color: "90CAF9" }})
            ]
        }})
    );

    // Metadata table
    const metaTableWidth = 9360;
    const labelW = 2200;
    const valW = metaTableWidth - labelW;
    const metaRows = [
        metaRow("Code Section(s)", m.section, labelW, valW),
        metaRow("Proponent", m.proponent, labelW, valW),
        metaRow("Recommendation", m.rec, labelW, valW),
        metaRow("Vote (F-A-NV)", m.vote, labelW, valW),
    ];
    if (m.reason) {{
        metaRows.push(metaRow("Reason", m.reason, labelW, valW));
    }}

    children.push(new Table({{
        width: {{ size: metaTableWidth, type: WidthType.DXA }},
        columnWidths: [labelW, valW],
        rows: metaRows
    }}));

    children.push(new Paragraph({{ spacing: {{ after: 200 }}, children: [] }}));

    // Modification text heading
    children.push(
        new Paragraph({{
            spacing: {{ after: 100 }},
            children: [new TextRun({{ text: "Modification Language", font: "Arial", size: 22, bold: true, color: "1B3A5C" }})]
        }}),
        new Paragraph({{
            spacing: {{ after: 60 }},
            border: {{ bottom: {{ style: BorderStyle.SINGLE, size: 2, color: "1B3A5C", space: 4 }} }},
            children: [new TextRun({{ text: "Enter the following into cdpACCESS (Build tab \\u2192 Content field):", font: "Arial", size: 16, italics: true, color: "888888" }})]
        }})
    );

    // The actual modification text in a styled box
    // Parse HTML from Quill editor (or plain text fallback) into rich TextRuns
    const modParas = modParagraphs(m.mod, "Courier New", 22);
    modParas.forEach(p => children.push(p));

    children.push(new Paragraph({{ spacing: {{ after: 100 }}, children: [] }}));

    // CDP entry checklist
    children.push(
        new Paragraph({{
            spacing: {{ after: 60 }},
            border: {{ top: {{ style: BorderStyle.SINGLE, size: 1, color: "CCCCCC", space: 4 }} }},
            children: [new TextRun({{ text: "cdpACCESS Entry Checklist:", font: "Arial", size: 18, bold: true, color: "666666" }})]
        }}),
        new Paragraph({{
            spacing: {{ after: 40 }},
            indent: {{ left: 360 }},
            children: [new TextRun({{ text: "\\u2610  Opened proposal " + m.id + " in cdpACCESS Build view", font: "Arial", size: 18 }})]
        }}),
        new Paragraph({{
            spacing: {{ after: 40 }},
            indent: {{ left: 360 }},
            children: [new TextRun({{ text: "\\u2610  Selected correct Instruction type", font: "Arial", size: 18 }})]
        }}),
        new Paragraph({{
            spacing: {{ after: 40 }},
            indent: {{ left: 360 }},
            children: [new TextRun({{ text: "\\u2610  Entered Section Number: " + (m.section || "(see proposal)"), font: "Arial", size: 18 }})]
        }}),
        new Paragraph({{
            spacing: {{ after: 40 }},
            indent: {{ left: 360 }},
            children: [new TextRun({{ text: "\\u2610  Entered modification text with proper legislative markup", font: "Arial", size: 18 }})]
        }}),
        new Paragraph({{
            spacing: {{ after: 40 }},
            indent: {{ left: 360 }},
            children: [new TextRun({{ text: "\\u2610  Verified strikethrough/underline formatting in Preview", font: "Arial", size: 18 }})]
        }}),
        new Paragraph({{
            spacing: {{ after: 40 }},
            indent: {{ left: 360 }},
            children: [new TextRun({{ text: "\\u2610  Saved changes", font: "Arial", size: 18 }})]
        }})
    );
}});

const doc = new Document({{
    styles: {{
        default: {{ document: {{ run: {{ font: "Arial", size: 20 }} }} }},
        paragraphStyles: [
            {{ id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
               run: {{ size: 32, bold: true, font: "Arial", color: "1B3A5C" }},
               paragraph: {{ spacing: {{ before: 240, after: 120 }}, outlineLevel: 0 }} }},
        ]
    }},
    sections: [{{
        properties: {{
            page: {{
                size: {{ width: 12240, height: 15840 }},
                margin: {{ top: 1080, right: 1080, bottom: 1080, left: 1080 }}
            }}
        }},
        headers: {{
            default: new Header({{ children: [
                new Paragraph({{
                    children: [
                        new TextRun({{ text: "IECC Modification Document", font: "Arial", size: 16, color: "999999", italics: true }}),
                        new TextRun({{ text: "\\t{body} \\u2014 {date}", font: "Arial", size: 16, color: "999999", italics: true }})
                    ],
                    tabStops: [{{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }}],
                    border: {{ bottom: {{ style: BorderStyle.SINGLE, size: 1, color: "CCCCCC", space: 4 }} }}
                }})
            ] }})
        }},
        footers: {{
            default: new Footer({{ children: [
                new Paragraph({{
                    alignment: AlignmentType.CENTER,
                    children: [
                        new TextRun({{ text: "Page ", font: "Arial", size: 16, color: "999999" }}),
                        new TextRun({{ children: [PageNumber.CURRENT], font: "Arial", size: 16, color: "999999" }}),
                        new TextRun({{ text: " \\u2014 For cdpACCESS entry use only \\u2014 Confidential", font: "Arial", size: 16, color: "999999" }})
                    ]
                }})
            ] }})
        }},
        children: children
    }}]
}});

Packer.toBuffer(doc).then(buf => process.stdout.write(buf));
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False,
                                      dir=tempfile.gettempdir()) as f:
        f.write(script)
        f.flush()
        try:
            result = subprocess.run(
                ["node", f.name],
                capture_output=True,
                timeout=30,
                cwd=_WEB_DIR,
                env=_node_env(),
            )
            if result.returncode != 0:
                raise RuntimeError(f"Modification doc generation failed: {result.stderr.decode()[:500]}")
            return result.stdout
        finally:
            os.unlink(f.name)


def _esc(s):
    """Escape string for JavaScript embedding."""
    if not s:
        return ""
    return str(s).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "")


def _strip_html(s):
    """Strip HTML tags for plain text fallback."""
    import re
    if not s:
        return ""
    return re.sub(r'<[^>]+>', '', str(s)).strip()


# JavaScript helper function for parsing Quill HTML into docx TextRuns.
# Handles: <p>, <u> (underline=additions), <s> (strikethrough=deletions), <strong>, <em>
# Falls back to plain text split by \n if no HTML tags detected.
PARSE_MOD_HTML_JS = """
function parseModHtml(html) {
    if (!html) return [[{text: ""}]];
    // Check if it's HTML or plain text
    if (!html.includes('<')) {
        // Plain text — split by newlines, each line is a paragraph
        return html.split("\\n").filter(s => s.trim()).map(line => [{text: line}]);
    }
    // Split into paragraph blocks
    const pBlocks = html.replace(/<br\\s*\\/?>/g, '\\n')
        .split(/<\\/?p[^>]*>/g)
        .filter(s => s.trim());
    if (pBlocks.length === 0) return [[{text: html.replace(/<[^>]+>/g, '')}]];
    return pBlocks.map(block => {
        const runs = [];
        // Match: tagged content OR plain text between tags
        const pattern = /(<(?:u|s|strong|em|b|i)>.*?<\\/(?:u|s|strong|em|b|i)>|[^<]+|<[^>]+>)/gs;
        let m;
        while ((m = pattern.exec(block)) !== null) {
            const chunk = m[0].trim();
            if (!chunk) continue;
            if (chunk.startsWith('<u>')) {
                runs.push({text: chunk.replace(/<\\/?u>/g, ''), underline: true});
            } else if (chunk.startsWith('<s>')) {
                runs.push({text: chunk.replace(/<\\/?s>/g, ''), strike: true});
            } else if (chunk.startsWith('<strong>') || chunk.startsWith('<b>')) {
                runs.push({text: chunk.replace(/<\\/?(?:strong|b)>/g, ''), bold: true});
            } else if (chunk.startsWith('<em>') || chunk.startsWith('<i>')) {
                runs.push({text: chunk.replace(/<\\/?(?:em|i)>/g, ''), italics: true});
            } else if (!chunk.startsWith('<')) {
                runs.push({text: chunk});
            }
        }
        return runs.length > 0 ? runs : [{text: block.replace(/<[^>]+>/g, '')}];
    });
}

function modParagraphs(html, font, size) {
    font = font || "Courier New";
    size = size || 22;
    const parsed = parseModHtml(html);
    return parsed.map(runs => new Paragraph({
        spacing: { after: 80, line: 300 },
        indent: { left: 360, right: 360 },
        children: runs.map(r => new TextRun({
            text: r.text,
            font: font,
            size: size,
            bold: r.bold || false,
            italics: r.italics || false,
            underline: r.underline ? { type: "single" } : undefined,
            strike: r.strike || false
        }))
    }));
}

function richModCell(html, width) {
    const paras = modParagraphs(html, "Arial", 18);
    if (paras.length === 0) paras.push(new Paragraph({ spacing: { after: 0 }, children: [new TextRun({ text: "\\u2014", font: "Arial", size: 18 })] }));
    return new TableCell({
        borders, margins, width: { size: width, type: WidthType.DXA },
        children: paras
    });
}
"""
