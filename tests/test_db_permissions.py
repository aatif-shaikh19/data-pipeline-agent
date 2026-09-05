import pytest
import psycopg2
from app.core.config import settings
from app.db.connection import execute_readonly_query, get_connection_params


def test_database_connection_and_logs():
    """Verify that we can connect to the database and query pipeline_logs."""
    assert settings.DATABASE_URL, "DATABASE_URL is not configured in .env"
    
    rows = execute_readonly_query("SELECT COUNT(*) as count FROM public.pipeline_logs;")
    assert len(rows) > 0
    count = rows[0]["count"]
    print(f"\n[SUCCESS] Connected to Supabase! Total pipeline logs found: {count}")
    assert count > 0, "pipeline_logs table is empty. Did you run scripts/seed_data.sql?"


def test_database_schemas_exist():
    """Verify that schema_reference table has entries."""
    rows = execute_readonly_query("SELECT pipeline_name FROM public.schema_reference;")
    assert len(rows) > 0
    pipeline_names = [r["pipeline_name"] for r in rows]
    print(f"\n[SUCCESS] Reference schemas verified: {pipeline_names}")
    assert "customer_events_etl" in pipeline_names


def test_pipeline_reader_blocks_insert():
    """
    Verify DB-level least privilege:
    If connected as pipeline_reader, attempting an INSERT must fail.
    If connected as postgres admin, inform the user to switch to pipeline_reader for production.
    """
    assert settings.DATABASE_URL, "DATABASE_URL is not configured in .env"
    
    params = get_connection_params()
    username = params.get("user", "")
    
    if "pipeline_reader" in username:
        with pytest.raises(Exception) as exc_info:
            conn = psycopg2.connect(**params)
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO public.pipeline_logs (pipeline_name, log_level, message) VALUES (%s, %s, %s);",
                    ("malicious_injection", "CRITICAL", "Attempted write via agent")
                )
                conn.commit()

        error_msg = str(exc_info.value).lower()
        print(f"\n[SECURITY VERIFIED] Read-only role blocked unauthorized write: {error_msg.strip()}")
        assert "permission denied" in error_msg or "read-only" in error_msg
    else:
        print(f"\n[NOTE] Currently testing as admin '{username}'. To enforce least privilege, switch user to 'pipeline_reader'.")
        # Ensure connection works regardless
        conn = psycopg2.connect(**params)
        conn.close()
