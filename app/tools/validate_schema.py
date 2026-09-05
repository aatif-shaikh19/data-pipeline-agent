import json
from typing import Dict, Any, List, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.db.connection import execute_readonly_query
from app.core.logging import logger

MAX_PAYLOAD_SIZE_BYTES = 50 * 1024  # 50 KB strict cap


class SchemaValidationInput(BaseModel):
    """Input model for validate_schema tool with strict validation."""
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    pipeline_name: str = Field(..., min_length=1, max_length=100, description="Name of the pipeline to validate against")
    schema_payload: Dict[str, Any] = Field(..., alias="schema_json", description="Observed schema dictionary to validate")

    @field_validator("schema_payload")
    @classmethod
    def check_payload_size(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        serialized = json.dumps(v)
        if len(serialized.encode("utf-8")) > MAX_PAYLOAD_SIZE_BYTES:
            raise ValueError(f"Payload size exceeds strict {MAX_PAYLOAD_SIZE_BYTES} bytes limit (50KB cap).")
        return v


class ValidationResult(BaseModel):
    """Result of schema validation and drift analysis."""
    is_valid: bool
    pipeline_name: str
    drift_issues: List[str]
    severity: Literal["none", "low", "medium", "high"]


def validate_schema(pipeline_name: str, schema_json: Dict[str, Any]) -> ValidationResult:
    """
    Validate an observed schema against the reference schema stored in PostgreSQL.
    Detects schema drift, missing required fields, and unexpected properties.
    """
    # Strict validation via Pydantic model
    validated_input = SchemaValidationInput(pipeline_name=pipeline_name, schema_json=schema_json)
    
    # Query reference schema (read-only)
    query = "SELECT expected_schema FROM public.schema_reference WHERE pipeline_name = %s LIMIT 1;"
    rows = execute_readonly_query(query, (validated_input.pipeline_name,))

    if not rows:
        return ValidationResult(
            is_valid=False,
            pipeline_name=validated_input.pipeline_name,
            drift_issues=[f"No reference schema found for pipeline '{validated_input.pipeline_name}'."],
            severity="high",
        )

    expected_schema = rows[0]["expected_schema"]
    drift_issues: List[str] = []

    # Check required fields
    expected_required = set(expected_schema.get("required", []))
    observed_properties = set(validated_input.schema_payload.get("properties", {}).keys())
    
    # In JSON schema or direct dict, check both properties and top-level keys
    if not observed_properties and "required" not in validated_input.schema_payload:
        observed_properties = set(validated_input.schema_payload.keys())

    missing_required = expected_required - observed_properties
    if missing_required:
        drift_issues.append(f"Missing required fields: {sorted(list(missing_required))}")

    # Check unexpected fields if expected schema lists properties
    expected_properties = set(expected_schema.get("properties", {}).keys())
    if expected_properties:
        unexpected_fields = observed_properties - expected_properties
        if unexpected_fields:
            drift_issues.append(f"Unexpected extra fields detected: {sorted(list(unexpected_fields))}")

    # Determine drift severity
    if not drift_issues:
        severity = "none"
        is_valid = True
    elif missing_required:
        severity = "high"
        is_valid = False
    else:
        severity = "medium"
        is_valid = False

    logger.info(
        f"Schema validation completed for {validated_input.pipeline_name}",
        extra={"audit_data": {"is_valid": is_valid, "drift_count": len(drift_issues), "severity": severity}}
    )

    return ValidationResult(
        is_valid=is_valid,
        pipeline_name=validated_input.pipeline_name,
        drift_issues=drift_issues,
        severity=severity,
    )
