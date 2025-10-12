-- Migration: Add missing fields to pending_stores table
-- Date: 2024-01-10

-- Add street, level, local columns to pending_stores
ALTER TABLE pending_stores ADD COLUMN street VARCHAR;
ALTER TABLE pending_stores ADD COLUMN level VARCHAR;
ALTER TABLE pending_stores ADD COLUMN local VARCHAR;

-- Note: SQLite doesn't support adding NOT NULL columns to existing tables
-- We'll add them as nullable first, then we can handle defaults in application

-- For new records, these will be required via the application layer

