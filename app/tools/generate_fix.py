import re
from typing import Tuple, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.core.logging import logger

# Compiled secret patterns for security scanning
SECRET_PATTERNS = [
    # API keys (Anthropic, Groq, OpenAI, Google)
    (re.compile(r"sk-ant-[a-zA-Z0-9_\-]{20,}", re.IGNORECASE), "[REDACTED_ANTHROPIC_KEY]"),
    (re.compile(r"gsk_[a-zA-Z0-9]{20,}", re.IGNORECASE), "[REDACTED_GROQ_KEY]"),
    (re.compile(r"sk-[a-zA-Z0-9]{20,}", re.IGNORECASE), "[REDACTED_API_KEY]"),
    (re.compile(r"AIza[0-9A-Za-z\-_]{20,}", re.IGNORECASE), "[REDACTED_GEMINI_KEY]"),
    # Connection strings
    (re.compile(r"(?:postgresql|postgres|mysql|mongodb(?:\+srv)?):\/\/[^\s\"'<>]+", re.IGNORECASE), "[REDACTED_DATABASE_URI]"),
    # Private keys
    (re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----[\s\S]*?-----END [A-Z ]+PRIVATE KEY-----"), "[REDACTED_PRIVATE_KEY]"),
    # Generic password assignments
    (re.compile(r"(?:password|passwd|secret|token|api_key)\s*[:=]\s*[\"'][^\"'\s]{4,}[\"']", re.IGNORECASE), "password='[REDACTED_SECRET]'"),
]


class GenerateFixInput(BaseModel):
    """Input model for generating a pipeline remediation fix."""
    model_config = ConfigDict(extra="forbid")

    issue_description: str = Field(..., min_length=5, max_length=2000, description="Description of the failure or drift to remediate")
    pipeline_name: Optional[str] = Field(None, max_length=100, description="Optional pipeline context")


class FixRecommendation(BaseModel):
    """Output recommendation for fixing a pipeline issue."""
    pipeline_name: Optional[str]
    suggested_code: str
    explanation: str
    redacted_secrets_count: int
    is_executable: bool = False  # Explicitly flagged non-executable by design


def scan_and_redact_secrets(text: str) -> Tuple[str, int]:
    """Scan string for credentials, keys, and connection strings; redact matches."""
    redacted_count = 0
    clean_text = text
    for pattern, replacement in SECRET_PATTERNS:
        matches = pattern.findall(clean_text)
        if matches:
            redacted_count += len(matches)
            clean_text = pattern.sub(replacement, clean_text)
    return clean_text, redacted_count


def generate_fix_recommendation(
    issue_description: str,
    pipeline_name: Optional[str] = None,
) -> FixRecommendation:
    """
    Generate actionable SQL/Python remediation recommendations for pipeline incidents.
    The output is strictly text (never executed) and passed through a regex secret scanner.
    """
    validated_input = GenerateFixInput(
        issue_description=issue_description,
        pipeline_name=pipeline_name,
    )

    desc_lower = validated_input.issue_description.lower()

    # Rule-based fix templates aligned with common pipeline failures
    if "schema" in desc_lower or "drift" in desc_lower or "missing field" in desc_lower:
        fix_code = """-- Remediation: Update schema migration or add default value
ALTER TABLE target_stream_table 
ADD COLUMN IF NOT EXISTS tracking_override VARCHAR(100) DEFAULT 'unassigned';

-- Verify backfill with batch validation
UPDATE target_stream_table SET tracking_override = 'default_backfill' WHERE tracking_override IS NULL;"""
        explanation = "Detected schema drift / missing field. Apply non-destructive column addition with sensible defaults."

    elif "timeout" in desc_lower or "deadlock" in desc_lower:
        fix_code = """# Remediation: Implement exponential backoff and retry policy
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    reraise=True
)
def sync_batch_with_retry(batch_data):
    # Isolated transaction with reduced lock timeout
    return execute_batch_reconciliation(batch_data, timeout_ms=3000)"""
        explanation = "Detected timeout/deadlock. Introduce exponential backoff retries and bounded transaction lock timeouts."

    elif "cdc" in desc_lower or "replication" in desc_lower or "debezium" in desc_lower:
        fix_code = """-- Remediation: Verify and re-create replication slot
SELECT slot_name, plugin, active FROM pg_replication_slots WHERE slot_name = 'inv_cdc_slot_0';

-- If inactive or dropped:
-- SELECT pg_drop_replication_slot('inv_cdc_slot_0');
-- SELECT pg_create_logical_replication_slot('inv_cdc_slot_0', 'pgoutput');"""
        explanation = "CDC replication slot failure. Inspect slot activity status and re-initialize CDC connector state."

    else:
        fix_code = f"""# General Pipeline Diagnostic Script
import logging

def diagnose_pipeline_batch():
    logging.info("Checking quarantine table for pipeline: {validated_input.pipeline_name or 'unknown'}")
    # Inspect failed record logs for payload inconsistencies
    pass"""
        explanation = "General diagnostic template. Investigate quarantined records and check pipeline consumer group lag."

    # Scan and redact any potential secrets/credentials in the fix output
    sanitized_code, redacted_count = scan_and_redact_secrets(fix_code)

    if redacted_count > 0:
        logger.warning(
            f"Redacted {redacted_count} credential pattern(s) from fix recommendation",
            extra={"audit_data": {"redacted_count": redacted_count}}
        )

    return FixRecommendation(
        pipeline_name=validated_input.pipeline_name,
        suggested_code=sanitized_code,
        explanation=explanation,
        redacted_secrets_count=redacted_count,
        is_executable=False,
    )
