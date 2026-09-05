# ROADMAP.md — Pipeline Guardian (Fencio Submission)

Compressed timeline. Goal: working, deployed, Shark-connected agent today or tomorrow. Not a
14-day plan — that's the separate flagship project.

| Phase | What | Est. time |
|---|---|---|
| 0 | Repo scaffold, Docker skeleton, env setup | 30–45 min |
| 1 | Postgres schema + fabricated data seed | 30 min |
| 2 | 4 tools implemented + unit tested in isolation | 60–90 min |
| 3 | LangGraph agent wiring, system prompt, routing | 45–60 min |
| 4 | FastAPI endpoint, bearer auth, rate limiting | 45 min |
| 5 | Dockerize + Railway deploy, smoke test | 30–45 min |
| 6 | Connect endpoint + token to Shark, define scope, launch run | 15–30 min |
| 7 | (Wait — 48–72hr) Shark generates report | external |
| 8 | Review findings, write your own explanation of 2–3 key ones, submit | 45–60 min |

Total active build time: roughly 4–6 hours across phases 0–6. Phase 7 is Fencio's turnaround, not
yours — flag this to them if the "today" framing in their email implied otherwise.

## Definition of done per phase
- **Phase 0:** `docker-compose up` runs an empty FastAPI app that responds on `/health`.
- **Phase 1:** `psql` shows `pipeline_logs` and `schema_reference` populated with fabricated rows;
  a read-only DB role exists and is confirmed to fail on INSERT.
- **Phase 2:** Each tool function has a standalone pytest passing, run without the agent involved.
- **Phase 3:** A local script can send a message to the LangGraph agent and get a tool-using response.
- **Phase 4:** `curl` with a valid bearer token hits `/agent/invoke` and gets a real response; invalid
  token gets 401; rapid repeated calls get 429.
- **Phase 5:** The Railway public URL responds the same way `curl` did locally.
- **Phase 6:** Shark's dashboard shows the run as "in progress" or live findings streaming.
