# Deployment Guide

> Jak funguje produkční nasazení a jak deployovat změny.

---

## Infrastruktura

```
GitHub (main) ──push──▶ Railway (backend)  ── preDeployCommand ──▶ alembic upgrade head
                    └──▶ Vercel (frontend)  ── auto-build ──▶ production
```

Obě služby mají auto-deploy z `main` branch.

---

## Railway (Backend)

**Projekt:** `Back-Testing-research-tool`
**Environment:** `TestEnv`
**Service:** `respectful-acceptance`
**URL:** `https://respectful-acceptance-testenv.up.railway.app`

### Env vars

| Proměnná | Hodnota |
|----------|---------|
| `DATABASE_URL` | `${{Postgres.DATABASE_PUBLIC_URL}}` |
| `CORS_ORIGIN` | `https://back-testing-research-tool.vercel.app` |
| `ANTHROPIC_API_KEY` | Claude API klíč |
| `PORT` | automaticky Railway |

### Deploy proces

1. Push na `main`
2. Railway detekuje změnu, spustí Nixpacks build
3. `buildCommand`: `pip install tqdm && pip install -r requirements.txt`
4. `preDeployCommand`: `alembic upgrade head`
5. `startCommand`: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
6. Health check na `/` (timeout 200s)

### Gotchas

- `tqdm` musí být v buildCommand (Nixpacks ho přeskočí)
- Private networking nefunguje — používat public URL
- SSL required (`sslmode=require`) pro DB spojení
- Agent tools volají API přes `localhost:$PORT`

---

## Vercel (Frontend)

**Team:** `jakubs-projects-aa7cc4ce`
**Projekt:** `back-testing-research-tool`
**URL:** `https://back-testing-research-tool.vercel.app`

### Env vars

| Proměnná | Hodnota |
|----------|---------|
| `NEXT_PUBLIC_API_URL` | `https://respectful-acceptance-testenv.up.railway.app` |
| `NEXTAUTH_SECRET` | random secret |
| `GOOGLE_CLIENT_ID` | OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | OAuth secret |

### Deploy proces

1. Push na `main`
2. Vercel auto-build s Turbopack
3. Production deployment (typically ~30s)

---

## Alembic migrace

### Přidání nové migrace

```bash
cd /Users/jakub/Back-testing-research-tool
alembic revision -m "popis zmeny"
# upravit vygenerovaný soubor v alembic/versions/
git add alembic/ && git commit && git push
# Railway automaticky spustí `alembic upgrade head`
```

### Aktuální chain

```
3a8136333301 (baseline — full schema)
    ↓
7aa7c245dbff (strategies + reports columns)
    ↓
a1b2c3d4e5f6 (notebook JSONB na projects)
```

### Pravidla

- Baseline je idempotentní (`CREATE TABLE IF NOT EXISTS`)
- Vždy `ADD COLUMN IF NOT EXISTS` pro bezpečnost
- Testovat lokálně před push (`alembic upgrade head`)

---

## Manuální deploy

Pokud auto-deploy nestačí:

```bash
# Railway — přes MCP nebo CLI
railway up

# Vercel — přes CLI
vercel --prod
```

---

## Monitoring

- **Health check:** `GET /` → `{"status": "running"}`
- **Railway logs:** `railway logs` nebo DevOps MCP `railway_logs`
- **Vercel logs:** Vercel dashboard → Runtime logs
- **Error logs:** `GET /api/errors` nebo `mcp__devops__monitor_errors`
- **DB stats:** `GET /api/data/stats` nebo `mcp__devops__monitor_data_stats`
