-- Migration 002: Centralized Content Tables
-- Purpose: Eliminate file-hunting by bringing all proposal content into the database
-- Date: 2026-03-05 (Session 29)
--
-- New tables: proposal_text, modifications, proposal_links, documents, meeting_events
-- Column additions: subgroup_actions (moved_by, seconded_by), meetings (transcript_path, recording_url)

-- ============================================================
-- TABLE 1: proposal_text
-- The actual code language for every proposal, extracted from
-- cdpACCESS DOCX files or monograph PDFs. This is what populates
-- the Quill editor so chairs stop seeing blank pages.
-- ============================================================
CREATE TABLE IF NOT EXISTS proposal_text (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_uid TEXT NOT NULL REFERENCES proposals(proposal_uid),
    source_type TEXT NOT NULL CHECK(source_type IN (
        'cdpaccess_docx', 'monograph_pdf', 'manual_entry', 'transcript'
    )),
    source_path TEXT,                    -- disk path to the source file
    proposal_html TEXT,                  -- formatted code text (underline=add, strike=delete)
    proposal_plain TEXT,                 -- plain text fallback (no markup)
    reason_text TEXT,                    -- proponent's original reason statement
    cost_impact_text TEXT,               -- cost impact statement
    code_section_text TEXT,              -- the specific section/table being modified
    extracted_at TEXT NOT NULL DEFAULT (datetime('now')),
    verified INTEGER DEFAULT 0,          -- has a human confirmed this is correct?
    verified_by TEXT,
    verified_at TEXT,
    notes TEXT,
    UNIQUE(proposal_uid, source_type)    -- one extraction per source type per proposal
);

-- ============================================================
-- TABLE 2: modifications
-- Pre-submitted modification documents. Separate from
-- subgroup_actions.modification_text because that captures what
-- the committee DECIDED — this tracks what was SUBMITTED.
-- A proposal might have multiple competing mods submitted.
-- ============================================================
CREATE TABLE IF NOT EXISTS modifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_uid TEXT NOT NULL REFERENCES proposals(proposal_uid),
    track TEXT NOT NULL,
    submitted_by TEXT,                   -- who submitted the modification
    submitted_date TEXT,                 -- when it was submitted
    source_path TEXT,                    -- path to the MOD DOCX file
    modification_html TEXT,              -- formatted modification text
    modification_plain TEXT,             -- plain text fallback
    reason_text TEXT,                    -- reason for the modification
    status TEXT NOT NULL DEFAULT 'received' CHECK(status IN (
        'received', 'posted_to_sharepoint', 'approved_by_committee',
        'rejected_by_committee', 'further_modified', 'superseded', 'withdrawn'
    )),
    meeting_id INTEGER REFERENCES meetings(id),  -- intended meeting (nullable)
    parent_modification_id INTEGER REFERENCES modifications(id),  -- for "further modified" chain
    extracted_at TEXT DEFAULT (datetime('now')),
    notes TEXT
);

-- ============================================================
-- TABLE 3: proposal_links
-- Cross-references between proposals. Captures relationships
-- that only emerge during discussion (combined consideration,
-- superseded, companion proposals).
-- ============================================================
CREATE TABLE IF NOT EXISTS proposal_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_uid_a TEXT NOT NULL REFERENCES proposals(proposal_uid),
    proposal_uid_b TEXT NOT NULL REFERENCES proposals(proposal_uid),
    link_type TEXT NOT NULL CHECK(link_type IN (
        'combined_consideration',   -- heard together (RECP9 + RECP15)
        'superseded_by',            -- action on A makes B moot (REPC49 by REPC34)
        'companion',                -- should advance together (REPC4 + REPC11)
        'depends_on',               -- A requires B to pass
        'conflicts_with',           -- A and B can't both pass
        'same_section'              -- both modify the same code section
    )),
    created_by TEXT DEFAULT 'manual',   -- 'manual', 'auto_scanner', 'transcript_extraction'
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(proposal_uid_a, proposal_uid_b, link_type)
);

-- ============================================================
-- TABLE 4: documents
-- Registry of every file on disk tied to a proposal or meeting.
-- Eliminates "searching around aimlessly" — query this instead
-- of hunting through a 29 GB folder tree.
-- ============================================================
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_uid TEXT REFERENCES proposals(proposal_uid),  -- nullable (meeting-level docs)
    meeting_id INTEGER REFERENCES meetings(id),            -- nullable (proposal-level docs)
    track TEXT,
    doc_type TEXT NOT NULL CHECK(doc_type IN (
        'proposal_docx',       -- cdpACCESS proposal document
        'modification_docx',   -- pre-submitted modification
        'pnnl_analysis',       -- PNNL technical analysis
        'circ_form_docx',      -- generated circulation form
        'circ_form_pdf',       -- converted PDF
        'transcript_docx',     -- meeting transcript (Word)
        'transcript_vtt',      -- meeting transcript (VTT subtitle)
        'agenda_pdf',          -- posted meeting agenda
        'agenda_docx',         -- generated agenda document
        'monograph_pdf',       -- public comment monograph
        'pcd_pdf',             -- public comment draft
        'proponent_comment',   -- comment from proponent
        'other'
    )),
    file_name TEXT,                     -- just the filename
    file_path TEXT NOT NULL,            -- full disk path
    file_size INTEGER,                  -- bytes
    file_hash TEXT,                     -- SHA256 for change detection
    discovered_at TEXT DEFAULT (datetime('now')),
    processed INTEGER DEFAULT 0,        -- has content been extracted?
    processed_at TEXT,
    notes TEXT,
    UNIQUE(file_path)                   -- no duplicate file entries
);

-- ============================================================
-- TABLE 5: meeting_events
-- Structured data extracted from meeting transcripts.
-- Captures the granular reality: motions, votes, amendments,
-- withdrawals, discussion points.
-- ============================================================
CREATE TABLE IF NOT EXISTS meeting_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id INTEGER NOT NULL REFERENCES meetings(id),
    proposal_uid TEXT REFERENCES proposals(proposal_uid),  -- nullable (procedural events)
    event_type TEXT NOT NULL CHECK(event_type IN (
        'motion', 'second', 'vote', 'amendment',
        'further_modification', 'withdrawal', 'discussion',
        'roll_call', 'agenda_change', 'combined_consideration',
        'reason_statement', 'procedural'
    )),
    speaker TEXT,                       -- who said/moved it
    content TEXT,                       -- what happened (text)
    vote_for INTEGER,                   -- for vote events
    vote_against INTEGER,
    vote_abstain INTEGER,
    vote_outcome TEXT,                  -- 'passed', 'failed'
    timestamp_seconds INTEGER,          -- seconds from meeting start
    source TEXT CHECK(source IN ('transcript_docx', 'transcript_vtt', 'manual', 'llm_extraction')),
    confidence REAL,                    -- 0.0-1.0 for LLM-extracted data
    verified INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

-- ============================================================
-- COLUMN ADDITIONS to existing tables
-- ============================================================

-- subgroup_actions: add moved_by and seconded_by (already on consensus_actions)
ALTER TABLE subgroup_actions ADD COLUMN moved_by TEXT;
ALTER TABLE subgroup_actions ADD COLUMN seconded_by TEXT;

-- meetings: add transcript and recording paths
ALTER TABLE meetings ADD COLUMN transcript_path TEXT;
ALTER TABLE meetings ADD COLUMN recording_url TEXT;

-- ============================================================
-- INDEXES for common query patterns
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_proposal_text_uid ON proposal_text(proposal_uid);
CREATE INDEX IF NOT EXISTS idx_modifications_uid ON modifications(proposal_uid);
CREATE INDEX IF NOT EXISTS idx_modifications_meeting ON modifications(meeting_id);
CREATE INDEX IF NOT EXISTS idx_proposal_links_a ON proposal_links(proposal_uid_a);
CREATE INDEX IF NOT EXISTS idx_proposal_links_b ON proposal_links(proposal_uid_b);
CREATE INDEX IF NOT EXISTS idx_documents_uid ON documents(proposal_uid);
CREATE INDEX IF NOT EXISTS idx_documents_meeting ON documents(meeting_id);
CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(doc_type);
CREATE INDEX IF NOT EXISTS idx_documents_processed ON documents(processed);
CREATE INDEX IF NOT EXISTS idx_meeting_events_meeting ON meeting_events(meeting_id);
CREATE INDEX IF NOT EXISTS idx_meeting_events_proposal ON meeting_events(proposal_uid);
