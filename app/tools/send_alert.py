from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.core.logging import logger

# Hardcoded strict recipient allowlist to block redirect-to-attacker attacks
ALLOWLISTED_RECIPIENTS = {
    "oncall-dataeng@pipelineguardian.internal",
    "security-team@pipelineguardian.internal",
    "pipeline-alerts@pipelineguardian.internal",
}

SeverityType = Literal["low", "medium", "high", "critical"]


class SendAlertInput(BaseModel):
    """Input model for sending pipeline incident alerts."""
    model_config = ConfigDict(extra="forbid")

    severity: SeverityType = Field(..., description="Alert severity: low, medium, high, or critical")
    message: str = Field(..., min_length=5, max_length=1000, description="Alert message content")
    recipient: str = Field(..., description="Target alert recipient (must match internal allowlist)")

    @field_validator("recipient")
    @classmethod
    def validate_recipient_allowlist(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if cleaned not in ALLOWLISTED_RECIPIENTS:
            raise ValueError(
                f"Unauthorized recipient '{v}'. Alerts may only be dispatched to verified allowlist: {sorted(list(ALLOWLISTED_RECIPIENTS))}"
            )
        return cleaned


class AlertResult(BaseModel):
    """Result of incident alert dispatch."""
    status: Literal["mock_sent", "rejected"]
    severity: str
    recipient: str
    message: str
    is_mocked: bool = True


def send_incident_alert(
    severity: str,
    message: str,
    recipient: str,
) -> AlertResult:
    """
    Dispatch an incident alert to authorized operational stakeholders.
    MOCKED: Logs an audit event only; no real network/email dispatch occurs.
    Enforces strict recipient allowlist and severity enums.
    """
    # Strict validation via Pydantic model (rejects unauthorized recipients & free-text severity)
    validated_input = SendAlertInput(
        severity=severity.lower(),  # type: ignore
        message=message,
        recipient=recipient,
    )

    # Structured audit logging for red-team observability
    logger.warning(
        f"[MOCK ALERT] Severity: {validated_input.severity.upper()} | Recipient: {validated_input.recipient} | Msg: {validated_input.message}",
        extra={
            "audit_data": {
                "event": "mock_incident_alert_dispatched",
                "severity": validated_input.severity,
                "recipient": validated_input.recipient,
                "message": validated_input.message,
            }
        }
    )

    return AlertResult(
        status="mock_sent",
        severity=validated_input.severity,
        recipient=validated_input.recipient,
        message=validated_input.message,
        is_mocked=True,
    )
