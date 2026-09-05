# PROMPTS.md — Antigravity Build Prompts, Phase by Phase

Run these in order. Paste PRD.md, TECH_STACK.md, ARCHITECTURE.md, AGENTS.md, and SECURITY.md into
Antigravity's context (or point it at the repo docs/ folder) before Phase 0, so every phase prompt
can reference them instead of re-explaining the design each time.

---

## Phase 0 — Scaffold
```
Using the attached PRD.md, TECH_STACK.md, and ARCHITECTURE.md, scaffold a new Python project called
"pipeline-guardian". Create:
- FastAPI app skeleton with a /health endpoint returning {"status": "ok"}
- Project structure: app/main.py, app/api/, app/agent/, app/tools/, app/db/, app/core/ (config,
  security), tests/
- requirements.txt matching TECH_STACK.md exactly (fastapi, uvicorn, langgraph, langchain-groq,
  langchain-google-genai, psycopg2-binary, pydantic, slowapi, python-dotenv, pytest)
- .env.example with placeholders for DATABASE_URL, GROQ_API_KEY, GEMINI_API_KEY, API_BEARER_TOKEN_HASH
- .gitignore covering .env, __pycache__, .venv
- docker-compose.yml with a FastAPI service and a local Postgres service for dev
Do not implement business logic yet — this phase is structure only. Confirm `docker-compose up`
serves /health before moving on.
```

## Phase 1 — Data layer
```
Using AGENTS.md's "Fabricated Data" section, create:
- SQL migration creating `pipeline_logs` (columns: id, pipeline_name, log_level, message, created_at)
  and `schema_reference` (columns: pipeline_name, expected_schema jsonb)
- A seed script generating ~200 fabricated, realistic-looking log rows across 3-4 fake pipeline
  names, and a handful of schema_reference rows. No real company/personal data — everything invented.
- A second SQL script creating a Postgres role `pipeline_reader` with GRANT SELECT ONLY on
  pipeline_logs and schema_reference — explicitly no INSERT/UPDATE/DELETE, and confirm this with
  a test that attempts an INSERT as that role and expects it to fail.
Wire DATABASE_URL for the app to connect as pipeline_reader, not the superuser.
```

## Phase 2 — Tools
```
Using AGENTS.md's tool specs exactly, implement each of the 4 tools as standalone Python functions
in app/tools/, each with:
- A strict Pydantic input model (reject unknown fields, enforce types, enforce the 50KB payload cap
  on validate_schema)
- query_pipeline_logs: parameterized query only, hardcoded allowlist of table/columns, limit capped
  server-side at 50 regardless of requested value
- generate_fix_recommendation: returns a string field only, run through a regex-based secret/
  credential pattern scanner before returning (flag and redact anything matching common API key /
  connection string patterns)
- send_incident_alert: mocked (log the event, no real network call), recipient checked against a
  hardcoded allowlist of 2-3 fake addresses, severity restricted to an enum
Write a pytest for each tool that exercises both the happy path and at least one adversarial input
(oversized payload, non-allowlisted recipient, attempted raw-SQL injection string in a text field).
All four test files should pass before moving to Phase 3.
```

## Phase 3 — LangGraph agent
```
Using ARCHITECTURE.md's "Agent Architecture" section and AGENTS.md's system prompt, wire a LangGraph
graph with one agent node (Groq / Llama 3.3 70B or Gemini, tool-calling enabled) and one tool node per Phase 2 tool. The
system prompt must be passed as its own message role and must never be string-concatenated with
tool outputs or retrieved log content. Implement conditional routing: agent -> tool (if tool_calls
present) -> agent -> END. Write a local test script (not pytest, a runnable script) that sends a
sample message like "why did the customer_pipeline run fail yesterday?" and prints the full
tool-call trace plus final response, so I can eyeball that it's actually calling query_pipeline_logs.
```

## Phase 4 — API layer
```
Using ARCHITECTURE.md's request flow, add a POST /agent/invoke endpoint to the FastAPI app that:
- Requires Authorization: Bearer <token>, validated against a hash stored in
  API_BEARER_TOKEN_HASH (never compare raw tokens; use constant-time comparison)
- Returns 401 on missing/invalid token before any agent logic runs
- Applies slowapi rate limiting (e.g. 20 requests/minute per token)
- Logs every request as structured JSON: timestamp, hashed token, input message, full tool-call
  trace, final response — this is the audit trail referenced in SECURITY.md
- Passes the validated input to the Phase 3 LangGraph agent and returns its response as JSON
Write a pytest hitting the endpoint with (a) no token -> 401, (b) invalid token -> 401,
(c) valid token -> 200 with expected response shape, (d) rapid repeated valid calls -> 429 eventually.
```

## Phase 5 — Containerize & deploy
```
Write a production Dockerfile for the FastAPI app (multi-stage if it meaningfully reduces image
size, otherwise keep it simple), using the requirements.txt from Phase 0. Add a DEPLOYMENT.md
documenting: how to set DATABASE_URL, GROQ_API_KEY (or GEMINI_API_KEY), and API_BEARER_TOKEN_HASH as Railway
environment variables, how Railway auto-builds from the Dockerfile on push, and how to generate a
new bearer token + its hash for rotation. Confirm the /health endpoint responds on the Railway
public URL before considering this phase done.
```

## Phase 6 — Connect to Shark
```
(No code needed — manual step.) In the Shark dashboard: set Target to the Railway public URL +
/agent/invoke, Auth to Bearer token (paste the real, unhashed token), Protocol to HTTP, and scope
it explicitly to this endpoint only, per Shark's "you define the boundary" model. Launch the run
and watch the live findings feed.
```

## Phase 8 — Post-assessment (after report arrives)
```
I'm going to paste in Shark's vulnerability report. For each confirmed finding, explain in plain
language: what the attack path was, why it worked given our SECURITY.md control set, and what a
concrete fix would look like — I want to write these explanations myself for the Fencio submission,
so give me the technical breakdown, not submission-ready prose.
```
