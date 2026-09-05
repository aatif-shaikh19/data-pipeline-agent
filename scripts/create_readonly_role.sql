-- ==============================================================================
-- Least Privilege Security: Read-Only Role Creation
-- Description: Creates pipeline_reader role with SELECT privileges ONLY.
-- Enforces DB-level defense-in-depth against prompt injection and arbitrary write attacks.
-- ==============================================================================

-- 1. Create dedicated read-only role with a password
-- NOTE: Replace 'YourStrongPassword123!' with your desired password!
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'pipeline_reader') THEN
        CREATE ROLE pipeline_reader WITH LOGIN PASSWORD 'YourStrongPassword123!';
    ELSE
        ALTER ROLE pipeline_reader WITH LOGIN PASSWORD 'YourStrongPassword123!';
    END IF;
END
$$;

-- 2. Grant connection and usage
GRANT CONNECT ON DATABASE postgres TO pipeline_reader;
GRANT USAGE ON SCHEMA public TO pipeline_reader;

-- 3. Explicitly grant SELECT ONLY on our two target tables
GRANT SELECT ON public.pipeline_logs TO pipeline_reader;
GRANT SELECT ON public.schema_reference TO pipeline_reader;

-- 4. Explicitly revoke all write privileges (defense in depth)
REVOKE INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER 
ON public.pipeline_logs FROM pipeline_reader;

REVOKE INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER 
ON public.schema_reference FROM pipeline_reader;

-- Ensure future tables are not automatically writable
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO pipeline_reader;

-- ==============================================================================
-- Verification queries (Run these to confirm permissions are enforced):
-- ==============================================================================
-- SET ROLE pipeline_reader;
-- SELECT COUNT(*) FROM public.pipeline_logs; -- Should SUCCEED
-- INSERT INTO public.pipeline_logs (pipeline_name, log_level, message) VALUES ('t', 'INFO', 'fail'); -- MUST FAIL with Permission Denied!
-- RESET ROLE;
