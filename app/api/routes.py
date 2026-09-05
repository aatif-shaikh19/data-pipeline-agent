import time
from datetime import datetime, timezone
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Request, HTTPException, status
from pydantic import BaseModel, Field

from app.core.security import validate_api_token
from app.core.logging import logger
from app.core.config import settings
from app.core.limiter import limiter
from app.agent.guardian import run_guardian_agent

router = APIRouter()


class AgentInvokeRequest(BaseModel):
    """Payload for invoking the Pipeline Guardian agent."""
    message: str = Field(..., min_length=1, max_length=5000, description="User or red-team probe instruction")


class AgentInvokeResponse(BaseModel):
    """Structured response returned by the Pipeline Guardian agent."""
    response: str
    tool_traces: List[Dict[str, Any]]
    token_hash: str
    timestamp: str


@router.post(
    "/invoke",
    response_model=AgentInvokeResponse,
    summary="Invoke Pipeline Guardian Agent",
    description="Primary endpoint for querying Pipeline Guardian. Authenticated via Bearer token and rate limited."
)
@limiter.limit(settings.RATE_LIMIT_STRING)
async def invoke_agent(
    request: Request,
    payload: AgentInvokeRequest,
    token_hash: str = Depends(validate_api_token),
) -> AgentInvokeResponse:
    """
    Execute the agent workflow against an incoming prompt.
    Enforces Bearer authentication, records full audit logs, and returns execution trace.
    """
    start_time = time.time()
    user_prompt = payload.message.strip()

    try:
        # Pass to LangGraph agent
        result = run_guardian_agent(user_prompt)

        duration_ms = round((time.time() - start_time) * 1000, 2)
        current_iso = datetime.now(timezone.utc).isoformat()

        # Structured JSON Audit Log (Required for Shark & Security Assessment)
        logger.info(
            "Agent invocation completed",
            extra={
                "audit_data": {
                    "event": "agent_invoke",
                    "caller_token_hash": token_hash,
                    "input_message": user_prompt,
                    "tool_traces": result.get("tool_traces", []),
                    "final_response": result.get("final_reply", ""),
                    "duration_ms": duration_ms,
                    "timestamp": current_iso,
                }
            }
        )

        return AgentInvokeResponse(
            response=result.get("final_reply", ""),
            tool_traces=result.get("tool_traces", []),
            token_hash=token_hash,
            timestamp=current_iso,
        )

    except Exception as e:
        logger.error(
            f"Agent execution error: {e}",
            extra={"audit_data": {"caller_token_hash": token_hash, "error": str(e)}},
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent workflow error: {str(e)}"
        )
