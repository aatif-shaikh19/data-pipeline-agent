# PRD — Pipeline Guardian (Fencio Submission Scope)

## Vision
A small, defensible AI agent that monitors data-pipeline health — schema validation, log lookup, fix
recommendation, incident alerting — built to be red-teamed by Shark and understood in depth, not to
be a full data platform. The full "Data Pipeline Guardian AI" product (6 agents, dashboard, Kafka,
Airflow) is a separate, later project. This doc scopes ONLY what ships for the Fencio assessment.

## Problem This Version Solves
Fencio's assessment requires: onboard an agent you built, run Shark against it, review the
vulnerabilities it finds, and submit the report with understanding of the security implications.
The agent itself needs to be real enough to have genuine attack surface (tool calls, data access,
LLM reasoning) — not a toy — while staying small enough that every design decision is defensible
in a follow-up conversation.

## Goals
- Ship a working agent + API today/tomorrow, connect it to Shark, let the 48–72hr assessment run.
- Apply real, correct security controls at every layer under our control (auth, least-privilege DB
  grants, input validation, output handling).
- Accept and document residual risk (primarily indirect prompt injection via ingested log content)
  rather than falsely claiming full coverage.
- Produce a submission where the confirmed vulnerabilities AND the proven defenses are both explainable
  in the reviewer's own words.

## Non-Goals (v1)
- No dashboard, no frontend, no multi-agent orchestration beyond one LangGraph agent.
- No Kafka, Airflow, Snowflake, multi-tenant auth, or CI/CD polish.
- No real production data anywhere in the system — all pipeline data is fabricated.

## Target User (for this scope)
Fencio's reviewer, evaluating: (1) does the agent have real tool-calling behavior worth attacking,
and (2) does the candidate understand what Shark found and why it matters.

## MVP Scope
- 1 LangGraph agent, 4 tools: `validate_schema`, `query_pipeline_logs`, `generate_fix_recommendation`,
  `send_incident_alert` (mocked).
- FastAPI HTTP wrapper with bearer-token auth, exposed via a public URL (Railway).
- Fabricated Postgres dataset: pipeline run logs, schema definitions, synthetic incident history.
- SECURITY.md documenting the threat model, controls applied, and OWASP LLM Top 10 / MITRE ATLAS mapping.

## Success Criteria
- Shark can connect and complete a full run against the live endpoint.
- At least a few findings surface (expected — full immunity isn't the goal; see SECURITY.md).
- Report is submitted with a written explanation of 2–3 findings in your own words, not just pasted.
