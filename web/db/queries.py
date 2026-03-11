"""Named SQL query constants. Reuses existing DB views where possible."""

# === DASHBOARD ===

DASHBOARD_COUNTS = """
SELECT
    track,
    COUNT(*) as total,
    SUM(CASE WHEN status = 'Decided' THEN 1 ELSE 0 END) as decided,
    SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END) as pending,
    SUM(CASE WHEN status = 'Withdrawn' THEN 1 ELSE 0 END) as withdrawn,
    SUM(CASE WHEN status = 'Phase Closed' THEN 1 ELSE 0 END) as phase_closed,
    SUM(CASE WHEN status = 'Testing' THEN 1 ELSE 0 END) as testing
FROM v_current_status
GROUP BY track
"""

PENDING_BY_SUBGROUP = """
SELECT
    track, current_subgroup, COUNT(*) as count
FROM v_current_status
WHERE status IN ('Pending', 'Testing')
GROUP BY track, current_subgroup
ORDER BY track, count DESC
"""

UPCOMING_MEETINGS = """
SELECT *
FROM meetings
WHERE meeting_date >= date('now')
  AND status = 'SCHEDULED'
ORDER BY meeting_date ASC
LIMIT 20
"""

RECENT_SUBGROUP_ACTIONS = """
SELECT sa.*, p.canonical_id, p.track
FROM subgroup_actions sa
JOIN proposals p ON sa.proposal_uid = p.proposal_uid
ORDER BY sa.action_date DESC
LIMIT 20
"""

IN_PROGRESS_MEETINGS = """
SELECT m.*,
    (SELECT COUNT(*) FROM meeting_agenda_items WHERE meeting_id = m.id) as agenda_count,
    (SELECT COUNT(*) FROM sg_action_staging WHERE meeting_id = m.id) as staged_count
FROM meetings m
WHERE m.status = 'SCHEDULED'
  AND EXISTS (SELECT 1 FROM meeting_agenda_items WHERE meeting_id = m.id)
  AND EXISTS (SELECT 1 FROM sg_action_staging WHERE meeting_id = m.id)
ORDER BY m.meeting_date ASC
"""

OPEN_DQ_FLAGS = """
SELECT dqf.*, p.canonical_id, p.track
FROM data_quality_flags dqf
JOIN proposals p ON dqf.proposal_uid = p.proposal_uid
WHERE dqf.needs_review = 1
ORDER BY p.track, p.canonical_id
"""

# === PROPOSALS ===

PROPOSALS_LIST = """
SELECT
    p.proposal_uid,
    p.canonical_id,
    p.prefix,
    p.track,
    p.phase,
    p.proponent,
    p.code_section,
    p.current_subgroup,
    p.withdrawn,
    p.cdpaccess_url,
    v.status,
    v.ca_recommendation,
    v.ca_date
FROM proposals p
JOIN v_current_status v ON p.canonical_id = v.canonical_id
WHERE 1=1
"""

PROPOSAL_DETAIL = """
SELECT
    p.*,
    v.status,
    v.ca_recommendation,
    v.ca_date,
    v.sg_recommendation,
    v.sg_date
FROM proposals p
JOIN v_current_status v ON p.canonical_id = v.canonical_id
WHERE p.canonical_id = ?
"""

PROPOSAL_SG_ACTIONS = """
SELECT *
FROM subgroup_actions
WHERE proposal_uid = ?
ORDER BY action_date ASC
"""

PROPOSAL_CA_ACTIONS = """
SELECT *
FROM consensus_actions
WHERE proposal_uid = ?
ORDER BY sequence ASC
"""

PROPOSAL_DQ_FLAGS = """
SELECT *
FROM data_quality_flags
WHERE proposal_uid = ?
ORDER BY needs_review DESC
"""

# === MEETINGS ===

ALL_MEETINGS = """
SELECT *
FROM meetings
ORDER BY meeting_date DESC
"""

MEETING_BY_ID = """
SELECT *
FROM meetings
WHERE id = ?
"""

MEETING_PROPOSALS = """
SELECT
    p.proposal_uid,
    p.canonical_id,
    p.prefix,
    p.track,
    p.proponent,
    p.code_section,
    p.current_subgroup,
    p.cdpaccess_url,
    v.status,
    v.ca_recommendation
FROM proposals p
JOIN v_current_status v ON p.canonical_id = v.canonical_id
WHERE p.track = ?
  AND p.current_subgroup = ?
  AND v.status IN ('Pending', 'Testing')
ORDER BY p.canonical_id
"""

# === SEARCH ===

SEARCH_PROPOSALS = """
SELECT
    p.proposal_uid,
    p.canonical_id,
    p.track,
    p.phase,
    p.proponent,
    p.code_section,
    p.current_subgroup,
    v.status,
    v.ca_recommendation
FROM proposals p
JOIN v_current_status v ON p.canonical_id = v.canonical_id
WHERE p.canonical_id LIKE ?
   OR p.proponent LIKE ?
   OR p.code_section LIKE ?
ORDER BY p.track, p.canonical_id
LIMIT 50
"""

# === SUBGROUP PORTAL ===

INSERT_SG_ACTION = """
INSERT INTO subgroup_actions (
    track, proposal_uid, subgroup, action_date, recommendation,
    vote_for, vote_against, vote_not_voting,
    reason, modification_text, source_file,
    moved_by, seconded_by
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

INSERT_MEETING = """
INSERT INTO meetings (track, meeting_date, meeting_time, body, phase, status, notes)
VALUES (?, ?, ?, ?, ?, 'SCHEDULED', ?)
"""

UPDATE_MEETING_STATUS = """
UPDATE meetings
SET status = ?, action_count = ?
WHERE id = ?
"""

PROPOSAL_UID_BY_CANONICAL = """
SELECT proposal_uid FROM proposals WHERE canonical_id = ?
"""

# === AGENDA ===

AGENDA_ITEMS = """
SELECT
    a.id as agenda_item_id,
    a.sort_order,
    p.proposal_uid,
    p.canonical_id,
    p.prefix,
    p.track,
    p.proponent,
    p.proponent_email,
    p.code_section,
    p.current_subgroup,
    p.cdpaccess_url,
    v.status,
    v.sg_recommendation,
    v.ca_recommendation
FROM meeting_agenda_items a
JOIN proposals p ON a.proposal_uid = p.proposal_uid
JOIN v_current_status v ON p.canonical_id = v.canonical_id
WHERE a.meeting_id = ?
ORDER BY a.sort_order ASC
"""

AVAILABLE_FOR_AGENDA = """
SELECT
    p.proposal_uid,
    p.canonical_id,
    p.proponent,
    p.proponent_email,
    p.code_section,
    v.status
FROM proposals p
JOIN v_current_status v ON p.canonical_id = v.canonical_id
WHERE p.track = ?
  AND p.current_subgroup = ?
  AND v.status IN ('Pending', 'Testing')
  AND p.proposal_uid NOT IN (
      SELECT proposal_uid FROM meeting_agenda_items WHERE meeting_id = ?
  )
ORDER BY p.canonical_id
"""

INSERT_AGENDA_ITEM = """
INSERT OR IGNORE INTO meeting_agenda_items (meeting_id, proposal_uid, sort_order)
VALUES (?, ?, ?)
"""

DELETE_AGENDA_ITEM = """
DELETE FROM meeting_agenda_items WHERE meeting_id = ? AND proposal_uid = ?
"""

UPDATE_AGENDA_ORDER = """
UPDATE meeting_agenda_items SET sort_order = ? WHERE meeting_id = ? AND proposal_uid = ?
"""

# === CIRCULATION FORMS ===

INSERT_CIRC_FORM = """
INSERT INTO circ_forms (meeting_id, track, subgroup, body, generated_at, pdf_path, status)
VALUES (?, ?, ?, ?, datetime('now'), ?, 'pending_review')
"""

PENDING_CIRC_FORMS = """
SELECT cf.*,
    m.meeting_date,
    m.action_count
FROM circ_forms cf
JOIN meetings m ON cf.meeting_id = m.id
WHERE cf.status = 'pending_review'
ORDER BY cf.generated_at DESC
"""

ALL_CIRC_FORMS = """
SELECT cf.*,
    m.meeting_date,
    m.action_count
FROM circ_forms cf
JOIN meetings m ON cf.meeting_id = m.id
ORDER BY cf.generated_at DESC
"""

CIRC_FORM_BY_ID = """
SELECT cf.*,
    m.meeting_date,
    m.action_count
FROM circ_forms cf
JOIN meetings m ON cf.meeting_id = m.id
WHERE cf.id = ?
"""

CIRC_FORM_BY_MEETING = """
SELECT * FROM circ_forms WHERE meeting_id = ?
"""

APPROVE_CIRC_FORM = """
UPDATE circ_forms
SET status = 'approved', reviewed_by = ?, reviewed_at = datetime('now')
WHERE id = ?
"""

UPLOAD_CIRC_FORM = """
UPDATE circ_forms
SET status = 'uploaded', sharepoint_url = ?
WHERE id = ?
"""

REJECT_CIRC_FORM = """
UPDATE circ_forms
SET status = 'rejected', reviewed_by = ?, reviewed_at = datetime('now'), rejection_reason = ?
WHERE id = ?
"""

AUTO_POPULATE_AGENDA = """
INSERT OR IGNORE INTO meeting_agenda_items (meeting_id, proposal_uid, sort_order)
SELECT ?, p.proposal_uid, ROW_NUMBER() OVER (ORDER BY p.canonical_id) * 10
FROM proposals p
JOIN v_current_status v ON p.canonical_id = v.canonical_id
WHERE p.track = ?
  AND p.current_subgroup = ?
  AND v.status IN ('Pending', 'Testing')
"""

# === CENTRALIZED CONTENT (proposal_text, modifications, proposal_links) ===

PROPOSAL_TEXT_FOR_MEETING = """
SELECT pt.proposal_uid, pt.proposal_html, pt.proposal_plain,
       pt.reason_text, pt.cost_impact_text, pt.code_section_text,
       pt.source_type, pt.verified
FROM proposal_text pt
INNER JOIN (
    SELECT proposal_uid, MIN(
        CASE source_type
            WHEN 'cdpaccess_docx' THEN 1
            WHEN 'monograph_markup' THEN 2
            WHEN 'cdpaccess_pdf' THEN 3
            WHEN 'monograph_pdf' THEN 4
            ELSE 5
        END
    ) as best_rank
    FROM proposal_text
    WHERE proposal_uid IN ({placeholders})
    GROUP BY proposal_uid
) best ON pt.proposal_uid = best.proposal_uid
    AND CASE pt.source_type
            WHEN 'cdpaccess_docx' THEN 1
            WHEN 'monograph_markup' THEN 2
            WHEN 'cdpaccess_pdf' THEN 3
            WHEN 'monograph_pdf' THEN 4
            ELSE 5
        END = best.best_rank
"""

MODIFICATIONS_FOR_PROPOSALS = """
SELECT m.id, m.proposal_uid, m.submitted_by, m.submitted_date,
       m.modification_html, m.modification_plain, m.reason_text,
       m.status, m.source_path, m.secretariat_approved
FROM modifications m
WHERE m.proposal_uid IN ({placeholders})
  AND m.status NOT IN ('withdrawn', 'superseded')
  AND m.secretariat_approved = 1
ORDER BY m.submitted_date DESC
"""

# Secretariat view: ALL modifications (including unapproved) for approval management
MODIFICATIONS_ALL_FOR_PROPOSAL = """
SELECT m.id, m.proposal_uid, m.submitted_by, m.submitted_date,
       m.modification_html, m.modification_plain, m.reason_text,
       m.status, m.source_path, m.secretariat_approved
FROM modifications m
WHERE m.proposal_uid = ?
  AND m.status NOT IN ('withdrawn', 'superseded')
ORDER BY m.secretariat_approved DESC, m.submitted_date DESC
"""

PROPOSAL_LINKS_FOR_PROPOSALS = """
SELECT pl.proposal_uid_a, pl.proposal_uid_b, pl.link_type, pl.notes,
       pa.canonical_id as canonical_a, pb.canonical_id as canonical_b
FROM proposal_links pl
JOIN proposals pa ON pl.proposal_uid_a = pa.proposal_uid
JOIN proposals pb ON pl.proposal_uid_b = pb.proposal_uid
WHERE pl.proposal_uid_a IN ({placeholders})
   OR pl.proposal_uid_b IN ({placeholders})
"""

PROPOSAL_TEXT_BY_UID = """
SELECT pt.proposal_html, pt.proposal_plain, pt.reason_text,
       pt.cost_impact_text, pt.code_section_text, pt.source_type
FROM proposal_text pt
WHERE pt.proposal_uid = ?
ORDER BY CASE pt.source_type
    WHEN 'cdpaccess_docx' THEN 1
    WHEN 'monograph_markup' THEN 2
    WHEN 'cdpaccess_pdf' THEN 3
    WHEN 'monograph_pdf' THEN 4
    ELSE 5
END
LIMIT 1
"""
