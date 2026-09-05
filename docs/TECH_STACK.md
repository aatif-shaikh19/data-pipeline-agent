# TECH_STACK.md — Pipeline Guardian (Fencio Submission)

Confirmed, final. No n8n — a visual workflow tool doesn't produce reviewable code or a clean
LangGraph trace surface, and it's a weaker resume artifact than a coded service.

| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.11 | Matches existing stack; typing + async support |
| API | FastAPI | Already your primary backend framework; native OpenAPI docs double as reference for Shark's "define your scope" step |
| Orchestration | LangGraph | Fencio explicitly lists LangGraph as their supported SDK integration path — reduces integration risk |
| LLM | Groq API (llama-3.3-70b-versatile) / Google Gemini API | 100% free tier, zero billing/credit card required; ultra-fast inference and strong tool-calling reliability |
| Database | PostgreSQL (Supabase free tier) | Matches your stack; lets us apply real DB-level least-privilege grants (SELECT-only role), not just app-level checks |
| Auth | Bearer token (random 32-byte, hashed at rest) | Matches what Shark's connection page asks for directly |
| Rate limiting | slowapi (FastAPI middleware) | Cheap, standard, blocks brute-force / high-volume probing |
| Containerization | Docker | Required for clean Railway deploy and reproducibility |
| Hosting | Railway | Fast public URL, keepable afterward for resume link, no idle-timeout headaches like some free tunnels |
| Testing | pytest | Matches FinSight precedent (30+ tests) |
| Logging | Structured JSON (stdlib `logging` + custom formatter) | Every tool call logged with args/result — this becomes your evidence trail when explaining Shark's findings |
| Secrets | `.env` + Railway environment variables | Never committed; referenced in SECURITY.md |

## Explicitly excluded from v1
Kafka, Airflow, Spark, Snowflake, Grafana, Kubernetes, React dashboard, multi-user auth — all deferred
to the separate, longer-timeline "Data Pipeline Guardian AI" flagship project.
