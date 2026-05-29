-- Migration 009: add careers_url to companies table
ALTER TABLE companies ADD COLUMN careers_url TEXT;
