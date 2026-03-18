-- Migration: Enable UUID extension and fix UUID column types for PostgreSQL
-- Date: 2025-11-09
-- Purpose: Enable proper UUID support and fix varchar columns that should be UUID type

-- Enable UUID extension for generating UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Add comment explaining the extension
COMMENT ON EXTENSION "uuid-ossp" IS 'Extension for generating UUIDs';