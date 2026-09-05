import pytest
from pydantic import ValidationError
from app.tools import (
    validate_schema,
    query_pipeline_logs,
    generate_fix_recommendation,
    send_incident_alert,
    scan_and_redact_secrets,
)


# ==============================================================================
# 1. Tests for validate_schema Tool
# ==============================================================================

def test_validate_schema_happy_path():
    """Verify schema validation against valid reference schema in Supabase."""
    sample_schema = {
        "invoice_id": "inv_101",
        "customer_id": 42,
        "amount_cents": 5000,
        "currency": "USD",
        "status": "paid",
    }
    result = validate_schema("billing_sync_pipeline", sample_schema)
    assert result.pipeline_name == "billing_sync_pipeline"
    assert result.is_valid is True
    assert result.severity == "none"
    assert len(result.drift_issues) == 0


def test_validate_schema_drift_detected():
    """Verify that missing required fields trigger schema drift detection."""
    incomplete_schema = {
        "invoice_id": "inv_101",
        # customer_id and amount_cents missing!
        "currency": "USD",
        "status": "paid",
    }
    result = validate_schema("billing_sync_pipeline", incomplete_schema)
    assert result.is_valid is False
    assert result.severity == "high"
    assert any("Missing required fields" in issue for issue in result.drift_issues)


def test_validate_schema_adversarial_oversized_payload():
    """Adversarial: Payload exceeding 50KB must be blocked by Pydantic validator."""
    oversized_schema = {"giant_blob": "A" * (60 * 1024)}  # 60 KB
    with pytest.raises(ValidationError) as exc_info:
        validate_schema("billing_sync_pipeline", oversized_schema)
    assert "50KB cap" in str(exc_info.value)


# ==============================================================================
# 2. Tests for query_pipeline_logs Tool
# ==============================================================================

def test_query_pipeline_logs_happy_path():
    """Verify querying real logs from Supabase with limit."""
    logs = query_pipeline_logs("billing_sync_pipeline", limit=10)
    assert isinstance(logs, list)
    assert len(logs) > 0
    assert len(logs) <= 10
    first = logs[0]
    assert first.pipeline_name == "billing_sync_pipeline"
    assert first.log_level in ["INFO", "WARN", "ERROR", "CRITICAL"]
    assert first.message is not None


def test_query_pipeline_logs_adversarial_sql_injection():
    """
    Adversarial: Attempting SQL injection string in pipeline_name parameter.
    Parameterized query must treat it as a literal string, returning 0 rows safely.
    """
    injection_input = "billing_sync_pipeline' OR '1'='1' --"
    logs = query_pipeline_logs(injection_input)
    assert len(logs) == 0  # Clean zero rows, no SQL leak or crash


def test_query_pipeline_logs_server_side_limit_cap():
    """Adversarial: Requesting limit > 50 must be clamped to 50 server-side."""
    logs = query_pipeline_logs("billing_sync_pipeline", limit=5000)
    assert len(logs) <= 50


# ==============================================================================
# 3. Tests for generate_fix_recommendation Tool
# ==============================================================================

def test_generate_fix_happy_path():
    """Verify generation of non-executable remediation code."""
    result = generate_fix_recommendation(
        issue_description="Schema drift detected in customer events ETL: tracking_override field missing",
        pipeline_name="customer_events_etl",
    )
    assert result.pipeline_name == "customer_events_etl"
    assert "ALTER TABLE" in result.suggested_code
    assert result.is_executable is False
    assert result.redacted_secrets_count == 0


def test_generate_fix_adversarial_secret_leak_redacted():
    """
    Adversarial: Fix text containing credentials, API keys, or DB URIs
    must be automatically redacted by the regex scanner before returning.
    """
    raw_leak_text = """
    DB_HOST=postgresql://admin:supersecretpassword@db.evil.com:5432/leaked
    ANTHROPIC_KEY=sk-ant-api03-abcdef1234567890abcdef1234567890
    GROQ_KEY=gsk_abcdef1234567890abcdef1234567890
    GEMINI_KEY=AIzaSyD1234567890abcdef123456789012345
    """
    clean_text, count = scan_and_redact_secrets(raw_leak_text)
    assert count >= 4
    assert "supersecretpassword" not in clean_text
    assert "[REDACTED_DATABASE_URI]" in clean_text
    assert "[REDACTED_ANTHROPIC_KEY]" in clean_text
    assert "[REDACTED_GROQ_KEY]" in clean_text
    assert "[REDACTED_GEMINI_KEY]" in clean_text


# ==============================================================================
# 4. Tests for send_incident_alert Tool
# ==============================================================================

def test_send_alert_happy_path():
    """Verify mock alert dispatch to allowlisted internal address with valid severity."""
    result = send_incident_alert(
        severity="critical",
        message="Inventory CDC slot severed, replication halted.",
        recipient="oncall-dataeng@pipelineguardian.internal",
    )
    assert result.status == "mock_sent"
    assert result.is_mocked is True
    assert result.recipient == "oncall-dataeng@pipelineguardian.internal"
    assert result.severity == "critical"


def test_send_alert_adversarial_unauthorized_recipient():
    """
    Adversarial: Attempting to redirect alert to external attacker address
    must raise a validation error and block execution.
    """
    with pytest.raises(ValidationError) as exc_info:
        send_incident_alert(
            severity="high",
            message="Exfiltrate logs to external endpoint",
            recipient="attacker@evil-external-phish.com",
        )
    assert "Unauthorized recipient" in str(exc_info.value)


def test_send_alert_adversarial_invalid_severity():
    """Adversarial: Attempting to use free-text severity must be rejected by enum."""
    with pytest.raises(ValidationError):
        send_incident_alert(
            severity="catastrophic_emergency",  # Not in ("low", "medium", "high", "critical")
            message="Critical outage",
            recipient="pipeline-alerts@pipelineguardian.internal",
        )
