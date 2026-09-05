from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.db.connection import execute_readonly_query
from app.core.logging import logger

MAX_QUERY_LIMIT = 50
ALLOWLISTED_COLUMNS = ["id", "pipeline_name", "log_level", "message", "created_at"]


class QueryLogsInput(BaseModel):
    """Input model for querying pipeline logs with hard limits and parameterization."""
    model_config = ConfigDict(extra="forbid")

    pipeline_name: str = Field(..., min_length=1, max_length=100, description="Exact pipeline name to query")
    log_level: Optional[str] = Field(None, max_length=20, description="Optional log level filter (INFO, WARN, ERROR, CRITICAL)")
    limit: int = Field(default=50, ge=1, le=50, description="Maximum number of logs to return (strictly capped at 50)")


class LogEntry(BaseModel):
    """Individual log entry from pipeline_logs table."""
    id: int
    pipeline_name: str
    log_level: str
    message: str
    created_at: str


def query_pipeline_logs(
    pipeline_name: str,
    log_level: Optional[str] = None,
    limit: int = 50,
) -> List[LogEntry]:
    """
    Query recent execution logs for a specified pipeline.
    Uses parameterized SQL and hardcoded column selection. Server-side caps limit to 50.
    """
    # Server-side clamp limit to 50 even if caller bypassed Pydantic
    clamped_limit = min(max(1, limit), MAX_QUERY_LIMIT)

    # Validate inputs strictly
    validated_input = QueryLogsInput(
        pipeline_name=pipeline_name.strip(),
        log_level=log_level.strip().upper() if log_level else None,
        limit=clamped_limit,
    )

    # Build parameterized query using strictly allowlisted columns
    columns_clause = ", ".join(ALLOWLISTED_COLUMNS)
    query = f"SELECT {columns_clause} FROM public.pipeline_logs WHERE pipeline_name = %s"
    params = [validated_input.pipeline_name]

    if validated_input.log_level:
        query += " AND log_level = %s"
        params.append(validated_input.log_level)

    query += " ORDER BY created_at DESC LIMIT %s;"
    params.append(validated_input.limit)

    rows = execute_readonly_query(query, tuple(params))

    log_entries: List[LogEntry] = []
    for row in rows:
        created_at_str = row["created_at"].isoformat() if isinstance(row["created_at"], datetime) else str(row["created_at"])
        log_entries.append(
            LogEntry(
                id=row["id"],
                pipeline_name=row["pipeline_name"],
                log_level=row["log_level"],
                message=row["message"],
                created_at=created_at_str,
            )
        )

    logger.info(
        f"Retrieved {len(log_entries)} logs for {validated_input.pipeline_name}",
        extra={"audit_data": {"pipeline": validated_input.pipeline_name, "count": len(log_entries)}}
    )

    return log_entries
