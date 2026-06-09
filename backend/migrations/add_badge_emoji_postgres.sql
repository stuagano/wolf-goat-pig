-- Migration: add emoji column to badges table
ALTER TABLE badges ADD COLUMN IF NOT EXISTS emoji VARCHAR;
