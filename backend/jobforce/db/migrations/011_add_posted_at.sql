-- Migration 011: Add posted_at to job_listings (the employer's original
-- posting date, distinct from crawled_at/created_at which record when
-- Jobforce ingested the listing). Plain ADD COLUMN suffices here since no
-- CHECK constraint is involved (unlike migration 010's table recreate).

ALTER TABLE job_listings ADD COLUMN posted_at TEXT;
