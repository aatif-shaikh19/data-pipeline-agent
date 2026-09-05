-- ==============================================================================
-- Migration: Create Tables for Pipeline Guardian
-- Description: Sets up pipeline_logs and schema_reference tables in PostgreSQL.
-- ==============================================================================

-- 1. Create pipeline_logs table
CREATE TABLE IF NOT EXISTS public.pipeline_logs (
    id SERIAL PRIMARY KEY,
    pipeline_name VARCHAR(100) NOT NULL,
    log_level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for fast filtered log retrieval by pipeline and timestamp
CREATE INDEX IF NOT EXISTS idx_pipeline_logs_pipeline_created 
ON public.pipeline_logs (pipeline_name, created_at DESC);

-- 2. Create schema_reference table
CREATE TABLE IF NOT EXISTS public.schema_reference (
    pipeline_name VARCHAR(100) PRIMARY KEY,
    expected_schema JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
