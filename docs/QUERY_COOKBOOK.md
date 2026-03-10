# IECC Database — SQL Query Cookbook

> Ready-to-use queries for common secretariat tasks. Copy-paste into SQLite.
> All queries run on the unified `iecc.db`. Add `WHERE track = 'commercial'` or `WHERE track = 'residential'` to filter by track.
> Governance and errata data is commercial-only (`track = 'commercial'`).
> For quick lookups, use `python3 iecc_query.py --status CEPC28-25` instead.

---

## Status & Lookup Queries

### Get current status of any proposal
```sql
SELECT * FROM v_current_status WHERE canonical_id = 'CEPC28-25';
```

### Get full action history (all actions, not just final)
```sql
SELECT ca.sequence, ca.action_date, ca.recommendation,
       ca.vote_for || '-' || ca.vote_against || '-' || ca.vote_not_voting AS vote,
       ca.reason, ca.is_final, ca.moved_by, ca.seconded_by
FROM consensus_actions ca
WHERE ca.proposal_uid = (SELECT proposal_uid FROM proposals WHERE canonical_id = 'CEPC11-25')
ORDER BY ca.sequence;
```

### Get subgroup recommendation for a proposal
```sql
SELECT sa.subgroup, sa.action_date, sa.recommendation,
       sa.vote_for || '-' || sa.vote_against || '-' || sa.vote_not_voting AS vote,
       sa.reason, sa.modification_text
FROM subgroup_actions sa
WHERE sa.proposal_uid = (SELECT proposal_uid FROM proposals WHERE canonical_id = 'CECP7-25');
```

### Disambiguate CEPC vs CECP (the common trap)
```sql
-- NOTE: v_current_status does NOT expose proposal_uid. Join on canonical_id.
SELECT p.canonical_id, p.proponent, p.current_subgroup, p.phase, p.withdrawn,
       cs.status, cs.ca_recommendation, cs.sg_recommendation
FROM proposals p
LEFT JOIN v_current_status cs ON p.canonical_id = cs.canonical_id
WHERE p.canonical_id LIKE 'CEC%7-25'
ORDER BY p.canonical_id;
```

---

## Pending & Ready Queries

### All genuinely pending proposals (active, not withdrawn, not decided)
```sql
-- Column is 'status' (NOT computed_status). Values: Decided, Pending, Withdrawn, Phase Closed
SELECT canonical_id, proponent, current_subgroup, status,
       sg_recommendation, sg_date, ca_recommendation, ca_date
FROM v_current_status
WHERE status = 'Pending'
ORDER BY current_subgroup, canonical_id;
```

### Proposals ready for consensus (SG done, no committee action)
```sql
SELECT * FROM v_ready_for_consensus ORDER BY current_subgroup;
```

### Proposals with NO subgroup action yet
```sql
SELECT p.canonical_id, p.proponent, p.current_subgroup, p.cdpaccess_id
FROM proposals p
WHERE p.phase = 'PUBLIC_COMMENT'
  AND p.withdrawn = 0
  AND p.proposal_uid NOT IN (SELECT proposal_uid FROM subgroup_actions)
  AND p.proposal_uid NOT IN (
    SELECT proposal_uid FROM consensus_actions WHERE is_final = 1
  )
ORDER BY p.current_subgroup, p.canonical_id;
```

---

## Meeting & Agenda Queries

### All decisions from a specific meeting
```sql
SELECT p.canonical_id, p.proponent, ca.recommendation,
       ca.vote_for || '-' || ca.vote_against || '-' || ca.vote_not_voting AS vote,
       ca.reason, ca.moved_by
FROM consensus_actions ca
JOIN proposals p ON ca.proposal_uid = p.proposal_uid
WHERE ca.action_date = '2026-02-25' AND ca.is_final = 1
ORDER BY p.canonical_id;
```

### Meeting history (all meetings with actions)
```sql
SELECT meeting_date, phase, status, action_count, notes
FROM meetings
WHERE action_count > 0
ORDER BY meeting_date DESC;
```

### Proposals discussed at multiple meetings (procedural chains)
```sql
SELECT p.canonical_id, p.proponent, COUNT(*) AS action_count,
       GROUP_CONCAT(ca.recommendation || ' (' || ca.action_date || ')', ' > ') AS history
FROM consensus_actions ca
JOIN proposals p ON ca.proposal_uid = p.proposal_uid
GROUP BY p.canonical_id
HAVING COUNT(*) > 1
ORDER BY action_count DESC;
```

Or use the dedicated view:
```sql
SELECT * FROM v_multi_action_proposals ORDER BY canonical_id, sequence;
```

---

## Subgroup Queries

### All proposals assigned to a subgroup
```sql
SELECT p.canonical_id, p.proponent, p.withdrawn,
       sa.recommendation AS sg_rec, sa.action_date AS sg_date,
       sa.vote_for || '-' || sa.vote_against || '-' || sa.vote_not_voting AS sg_vote
FROM proposals p
LEFT JOIN subgroup_actions sa ON p.proposal_uid = sa.proposal_uid
WHERE p.current_subgroup LIKE '%Modeling%'
  AND p.phase = 'PUBLIC_COMMENT'
ORDER BY p.canonical_id;
```

### Subgroup activity summary
```sql
SELECT subgroup, COUNT(*) AS total_actions,
       SUM(CASE WHEN recommendation LIKE '%Approved%' THEN 1 ELSE 0 END) AS approved,
       SUM(CASE WHEN recommendation LIKE '%Disapproved%' THEN 1 ELSE 0 END) AS disapproved
FROM subgroup_actions
GROUP BY subgroup
ORDER BY total_actions DESC;
```

### Proposals where SG and Committee disagree
```sql
SELECT p.canonical_id, p.proponent,
       sa.recommendation AS sg_rec,
       ca.recommendation AS committee_rec
FROM proposals p
JOIN subgroup_actions sa ON p.proposal_uid = sa.proposal_uid
JOIN consensus_actions ca ON p.proposal_uid = ca.proposal_uid AND ca.is_final = 1
WHERE (sa.recommendation LIKE '%Approved%' AND ca.recommendation LIKE '%Disapproved%')
   OR (sa.recommendation LIKE '%Disapproved%' AND ca.recommendation LIKE '%Approved%')
ORDER BY p.canonical_id;
```

---

## Data Quality Queries

### All data quality flags needing review
```sql
SELECT dqf.flag_type, dqf.canonical_id, dqf.table_name,
       dqf.raw_value, dqf.resolved_value, dqf.needs_review
FROM data_quality_flags dqf
ORDER BY dqf.needs_review DESC, dqf.created_at DESC;
```

Or use the view:
```sql
SELECT * FROM v_data_quality_review WHERE needs_review = 1;
```

### Proposals missing vote counts
```sql
SELECT p.canonical_id, p.proponent, ca.recommendation, ca.action_date
FROM consensus_actions ca
JOIN proposals p ON ca.proposal_uid = p.proposal_uid
WHERE ca.is_final = 1
  AND (ca.vote_for IS NULL OR ca.vote_against IS NULL)
ORDER BY ca.action_date DESC;
```

---

## Governance Queries

### Search governance policies by keyword
```sql
SELECT gd.title, gc.label, gc.heading, SUBSTR(gc.clause_text, 1, 200) AS excerpt
FROM governance_clauses gc
JOIN governance_documents gd ON gc.document_id = gd.document_id
WHERE gc.clause_text LIKE '%quorum%'
ORDER BY gd.title, gc.clause_order;
```

### List all governance documents
```sql
SELECT document_id, title, approved_date, revised_date,
       (SELECT COUNT(*) FROM governance_clauses gc WHERE gc.document_id = gd.document_id) AS clause_count
FROM governance_documents gd;
```

---

## Statistics & Summary

### Overall disposition summary
```sql
SELECT ca.recommendation, COUNT(*) AS count,
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM consensus_actions WHERE is_final = 1), 1) AS pct
FROM consensus_actions ca
WHERE ca.is_final = 1
GROUP BY ca.recommendation
ORDER BY count DESC;
```

### Data completeness dashboard
```sql
SELECT
  (SELECT COUNT(*) FROM proposals) AS total_proposals,
  (SELECT COUNT(*) FROM proposals WHERE withdrawn = 1) AS withdrawn,
  (SELECT COUNT(*) FROM consensus_actions WHERE is_final = 1) AS final_actions,
  (SELECT COUNT(*) FROM consensus_actions WHERE is_final = 1 AND vote_for IS NOT NULL) AS with_votes,
  (SELECT COUNT(*) FROM consensus_actions WHERE is_final = 1 AND reason IS NOT NULL AND reason != '') AS with_reasons,
  (SELECT COUNT(*) FROM subgroup_actions) AS sg_actions,
  (SELECT COUNT(*) FROM errata) AS errata_count,
  (SELECT COUNT(*) FROM data_quality_flags) AS quality_flags;
```

### Vote margin analysis (closest decisions)
```sql
SELECT p.canonical_id, p.proponent, ca.recommendation,
       ca.vote_for, ca.vote_against,
       ca.vote_for - ca.vote_against AS margin,
       ca.action_date
FROM consensus_actions ca
JOIN proposals p ON ca.proposal_uid = p.proposal_uid
WHERE ca.is_final = 1 AND ca.vote_for IS NOT NULL AND ca.vote_against IS NOT NULL
ORDER BY ABS(ca.vote_for - ca.vote_against) ASC
LIMIT 20;
```
