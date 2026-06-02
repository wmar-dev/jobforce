-- Migration 010: Add 'archived' and 'shortlisted' triage statuses to job_listings.
-- SQLite does not support ALTER TABLE DROP/MODIFY CONSTRAINT, so we recreate the table.

PRAGMA foreign_keys = OFF;

BEGIN TRANSACTION;

CREATE TABLE job_listings_new (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id     INTEGER NOT NULL REFERENCES companies(id),
    title          TEXT    NOT NULL,
    location       TEXT,
    role_type      TEXT,
    description    TEXT,
    source_url     TEXT    NOT NULL,
    status         TEXT    NOT NULL DEFAULT 'saved'
                   CHECK(status IN ('saved','applied','interviewing','offer','rejected','withdrawn','archived','shortlisted')),
    fit_score      REAL,
    fit_scored     INTEGER NOT NULL DEFAULT 0,
    fit_confidence TEXT,
    fit_rationale  TEXT,
    crawled_at     TEXT,
    created_at     TEXT    NOT NULL,
    updated_at     TEXT    NOT NULL
);

INSERT INTO job_listings_new SELECT
    id, company_id, title, location, role_type, description, source_url,
    status, fit_score, fit_scored, fit_confidence, fit_rationale,
    crawled_at, created_at, updated_at
FROM job_listings;

DROP TABLE job_listings;
ALTER TABLE job_listings_new RENAME TO job_listings;

CREATE INDEX idx_job_listings_company ON job_listings(company_id);
CREATE INDEX idx_job_listings_status  ON job_listings(status);

COMMIT;

PRAGMA foreign_keys = ON;
