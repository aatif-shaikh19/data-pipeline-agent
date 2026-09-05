# DECISIONS.md — Pipeline Guardian (Fencio Submission)

| Decision | Alternative considered | Why rejected |
|---|---|---|
| Scope to 4 tools, 1 agent | 6-agent full "Data Pipeline Guardian AI" platform | Fencio's ask is onboard-run-review-report, not a platform; more surface = less depth of understanding under time pressure; that full version is a separate later project |
| FastAPI + LangGraph | n8n workflow | Shark supports n8n as a connection method, but building agent *logic* in n8n produces no reviewable code and is a weaker resume artifact; n8n also doesn't match Fencio's stated LangGraph SDK support |
| Apply real security controls, accept residual injection risk | Try to make the agent fully "unbreakable" | Zero findings makes for a hollow report — Fencio is evaluating understanding of findings, not a perfect score; prompt injection is an unsolved industry problem, claiming full immunity would be dishonest |
| Fabricated data only | Use existing live agent (Grievance Resolver) | Live production system as red-team target risks real data/integration exposure; fabricated data removes that risk entirely |
| DB-level SELECT-only grant, not just app-level checks | App-level permission checks only | Defense in depth — if the app layer is bypassed via injection, the DB role itself still can't write |
| Railway for hosting | ngrok tunnel | Public URL survives past the assessment for resume use; no tunnel-session expiry risk mid-assessment |
