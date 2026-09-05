# ARCHITECTURE.md — Pipeline Guardian (Fencio Submission)

## System Overview

```
Shark (external red-team probes)
        |
        v  HTTPS + Bearer token
FastAPI app (Railway container)
        |
        v
LangGraph agent (single graph, 1 LLM node + 4 tool nodes)
        |
        v
Postgres (Supabase) — SELECT-only role for query_pipeline_logs
                     — separate role/schema for validate_schema reference data
```

## Request Flow
1. Client (Shark) sends `POST /agent/invoke` with `Authorization: Bearer <token>` and a JSON message.
2. FastAPI middleware: rate limit check → token validation → request logged.
3. Request passed to LangGraph agent as a new/continued thread.
4. Agent (Groq / Llama 3.3 70B or Gemini) reasons over the message, decides on tool calls per LangGraph routing.
5. Tool executes against fabricated Postgres data or in-memory mock (for `send_incident_alert`).
6. Tool result returned to the model; model produces final response.
7. Full trace (input, tool calls + args, tool outputs, final response) logged as structured JSON.
8. Response returned to client.

## Agent Architecture (LangGraph)
- **Single agent, single graph** — not multi-agent for this scope. Nodes:
  - `agent` (LLM reasoning + tool selection)
  - `validate_schema` (tool node)
  - `query_pipeline_logs` (tool node)
  - `generate_fix_recommendation` (tool node)
  - `send_incident_alert` (tool node)
  - Conditional edges: agent → tool (if tool_calls present) → agent → END
- System prompt is a separate message role, never string-concatenated with tool outputs or retrieved
  log content. This limits (does not eliminate) the blast radius of injected instructions inside data.

## Data Flow / Trust Boundaries
- **Trusted:** system prompt, bearer token validation, DB schema/grants.
- **Untrusted:** any content that flows through `query_pipeline_logs` results — log entries are
  fabricated but treated as if attacker-influenced, since real pipeline logs often ingest external
  data. This is the primary injection surface and is intentionally left realistic, not sanitized away.
- **Semi-trusted:** `generate_fix_recommendation` output — returned as text only, scanned for
  obvious secret/credential patterns before being sent back, never executed.

## Deployment Flow
1. Local dev: docker-compose (FastAPI + Postgres) for iteration.
2. `Dockerfile` builds the FastAPI service image.
3. Railway deploy from GitHub repo (auto-build on push).
4. Environment variables (DB URL, GROQ_API_KEY or GEMINI_API_KEY, bearer token hash) set in Railway dashboard,
   never in code.
5. Public HTTPS URL handed to Shark as the target endpoint.

## Security Architecture
See SECURITY.md for the full threat model and control mapping. Summary: authentication + rate
limiting at the perimeter, least-privilege DB grants at the data layer, tool-output validation at
the boundary back to the model, and full audit logging throughout. Indirect prompt injection via
log content is accepted as residual risk and documented, not falsely claimed as solved.
