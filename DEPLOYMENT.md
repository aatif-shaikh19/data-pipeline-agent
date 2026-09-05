# DEPLOYMENT.md — Deploying Pipeline Guardian to Railway

This document guides you through deploying the Pipeline Guardian service to **Railway** (or any container platform) and connecting it to **Shark** for the Fencio security assessment.

---

## 1. Prerequisites
- A free GitHub account and a Git repository with this project pushed.
- A free Railway account at [railway.com](https://railway.com) (or [railway.app](https://railway.app)).
- Your Supabase `DATABASE_URL` and `GROQ_API_KEY`.

---

## 2. Token Generation & Rotation

Your API uses constant-time comparison against the SHA-256 hash of your Bearer token.
To generate a new secure 32-byte token and its SHA-256 hash, run this command in Python:

```bash
python -c "import secrets, hashlib; token=secrets.token_urlsafe(32); print('RAW TOKEN (give to Shark):', token); print('TOKEN HASH (put in Railway env):', hashlib.sha256(token.encode()).hexdigest())"
```

Keep the **RAW TOKEN** to enter into Shark's connection form.
Put the **TOKEN HASH** into your Railway environment variables.

---

## 3. Step-by-Step Railway Deployment

### Step 3.1: Create New Project on Railway
1. Log in to [railway.com](https://railway.com).
2. Click **+ New Project** $\rightarrow$ **Deploy from GitHub repo**.
3. Select your repository `data-pipeline-agent` (or whatever you named it).
4. Railway will detect the `Dockerfile` automatically and prepare the build.

### Step 3.2: Configure Environment Variables
In your Railway dashboard, click on your deployed service $\rightarrow$ go to the **Variables** tab.
Add the following environment variables:

| Variable Name | Value | Description |
|---|---|---|
| `LLM_PROVIDER` | `groq` | Provider selection |
| `GROQ_API_KEY` | `gsk_...` | Your Groq Cloud API Key |
| `GROQ_MODEL` | `qwen/qwen3.8-27b` | Active Groq model |
| `DATABASE_URL` | `postgresql://...` | Supabase connection string (use the pooler URI) |
| `API_BEARER_TOKEN_HASH` | `88e1467ea309...` | SHA-256 hash of your Bearer token |
| `API_BEARER_TOKEN` | `your-unhashed-token` | *(Optional for fallback validation)* |
| `ENVIRONMENT` | `production` | Production mode |

### Step 3.3: Generate Public Networking Domain
1. In your service settings in Railway, go to the **Settings** tab.
2. Scroll to the **Networking** section.
3. Click **Generate Domain** (e.g. `pipeline-guardian-production.up.railway.app`).
4. Railway will provision an HTTPS endpoint with automated TLS/SSL.

---

## 4. Verification After Deployment

### Check 1: Public Health Check
Open your browser or run in terminal:
```bash
curl -i https://YOUR_RAILWAY_DOMAIN.up.railway.app/health
```
Expected output:
```json
{"status": "ok"}
```

### Check 2: Public Agent Invocation (with Bearer Token)
```bash
curl -i -X POST https://YOUR_RAILWAY_DOMAIN.up.railway.app/agent/invoke \
  -H "Authorization: Bearer YOUR_RAW_BEARER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Check the health of billing_sync_pipeline"}'
```
Expected output:
HTTP `200 OK` with JSON payload containing `response`, `tool_traces`, and `timestamp`.

---

## 5. Phase 6: Connecting to Shark

Once your Railway endpoint is live and verified:
1. Open the **Shark** assessment dashboard provided in your Fencio onboarding link.
2. In the connection setup:
   - **Target Endpoint:** `https://YOUR_RAILWAY_DOMAIN.up.railway.app/agent/invoke`
   - **Authentication:** Select `Bearer Token`.
   - **Token:** Paste your **RAW TOKEN** (not the hash).
   - **Protocol:** `HTTP / REST`.
   - **Scope Definition:** Explicitly scope to `POST /agent/invoke`.
3. Launch the assessment run (Shark will stream live red-team probes against your agent).
