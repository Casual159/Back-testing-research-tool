# Development Log – Februari 2026

> Přehled vývoje od nasazení na produkci po aktuální stav.
> Období: 15.–22. února 2026

---

## Souhrn

Během jednoho týdne byl projekt přesunut z lokálního vývoje na **plný produkční stack** (Railway + Vercel), opraveny klíčové bugy, implementovány nové funkce a přidána autentizace.

### Stack v produkci

| Vrstva | Služba | URL |
|--------|--------|-----|
| Frontend | Vercel (Next.js 16) | `back-testing-research-tool.vercel.app` |
| Backend | Railway (FastAPI + Uvicorn) | `respectful-acceptance-testenv.up.railway.app` |
| Databáze | Railway PostgreSQL 17 | `interchange.proxy.rlwy.net:35874` |
| Migrace | Alembic (preDeployCommand) | automaticky při každém deploy |

---

## Implementované funkce

### 1. Full-stack deployment
- Vercel auto-deploy z `main` branch
- Railway auto-deploy s `alembic upgrade head` jako preDeployCommand
- CORS konfigurace přes env vars (`CORS_ORIGIN`)
- Health check endpoint na `/`

### 2. Notebook na projekt detail stránce
- JSONB sloupec `notebook` v tabulce `projects`
- Blokový systém: **text**, **backtest_ref**, **strategy_ref**, **agent_note**
- Debounced auto-save (1s)
- Vizuálně odlišené bloky (modrá = backtest, fialová = strategie, oranžová = agent)
- API: `PATCH /api/projects/:id` + `POST /api/projects/:id/notebook/blocks`
- Komponenta: `frontend/components/projects/Notebook.tsx`

### 3. Persistentní konverzace
- `ConversationStorage` přepsán z in-memory na PostgreSQL
- Upsert při každém `save()` (INSERT ON CONFLICT UPDATE)
- `project_id` linkage — konverzace patří k projektu
- API: `GET /api/projects/:id/conversations`, `GET /api/conversations/:id`
- Historie konverzací v chat sidebar (empty state)
- Načtení staré konverzace s plnými zprávami + tool calls

### 4. Resizable chat sidebar
- Drag handle na levé straně (cursor: col-resize)
- Rozsah 320–800px, persisted do localStorage
- Dynamický `marginRight` na hlavním obsahu

### 5. Auth + multi-tenancy
- NextAuth.js s Google OAuth
- Landing page pro nepřihlášené
- `user_id` sloupec v `projects` a `conversations`
- Middleware pro ochranu `/projects`, `/strategies`, `/backtest` atd.

### 6. DevOps MCP server
- `agent/devops_mcp_server.py` — Railway deploy/logs/status, DB migrace, monitoring
- Integrace s Railway CLI a Alembic

---

## Opravy bugů

| Bug | Příčina | Fix |
|-----|---------|-----|
| System error v sidebaru | Health check volal `/api/` (404) místo `/` | Použít `config.apiUrl + "/"` |
| backtest_count vždy 0 | Statický sloupec, nikdy inkrementovaný | LEFT JOIN na `research_events WHERE event_type='backtest_run'` |
| "Data not available" při startu | Auto-check běžel s defaultními params | Přidán `userInteracted` flag |
| Agent tools 500 na Railway | Hardcoded `localhost:8000` | Použít `$PORT` env var |
| create_strategy chyběl strategy_type | Staré SQL neobsahovalo nové sloupce | Doplněny `strategy_type`, `builtin_class` |
| save_report fail na produkci | Sloupce chyběly v DB | Dynamická detekce sloupců přes `information_schema` |
| Template literals v TSX | Single quotes místo backticks | Opraveno na template literals |

---

## Databázové migrace

Alembic chain: `baseline` → `7aa7c245dbff` (strategies+reports columns) → `a1b2c3d4e5f6` (notebook JSONB)

Baseline obsahuje všech 10+ tabulek jako `CREATE TABLE IF NOT EXISTS` — idempotentní pro existující i novou DB.

---

## Architektura (aktuální)

```
┌─────────────────┐     ┌──────────────────────┐
│  Vercel          │────▶│  Railway              │
│  Next.js 16      │ SSE │  FastAPI + Agent      │
│  NextAuth        │◀────│  Claude Sonnet 4      │
│  Tailwind        │     │  11 tools             │
└─────────────────┘     └──────────┬───────────┘
                                   │
                          ┌────────▼────────┐
                          │  Railway PG 17   │
                          │  10 tabulek      │
                          │  Alembic migrace │
                          └─────────────────┘
```

### Klíčové tabulky

| Tabulka | Účel |
|---------|------|
| `candles` | OHLCV data (Binance) |
| `market_regimes` | Detekce tržního režimu |
| `strategies` | Definice strategií |
| `backtest_reports` | Výsledky backtestů |
| `projects` | Research projekty + notebook |
| `project_events` | Timeline události |
| `conversations` | Persistentní konverzace s agentem |
| `agent_suggestions` | Návrhy od agenta |
| `error_logs` | Error tracking |

---

## MCP servery

Všechny konfigurovány v `~/.claude.json` (nikoliv `~/.claude/settings.json`).

- **backtesting** — hlavní agent MCP (`agent/mcp_server.py`)
- **devops** — Railway/DB/monitoring (`agent/devops_mcp_server.py`)
- **postgres-local** / **postgres-railway** — přímé SQL dotazy
- **Railway** — `@railway/mcp-server` pro deploy operace
- **filesystem** — přístup k Obsidian vault
- **vercel** — Vercel deployment management
- **Crypto.com** — live market data

---

## Další kroky

- [ ] Markdown rendering v text blocích notebooku
- [ ] Drag & drop řazení bloků v notebooku
- [ ] Conversation search a filtrace
- [ ] Equity curve embed v notebook backtest_ref blocích
- [ ] Batch testing workflow (více strategií najednou)
- [ ] Compare mode pro backtest výsledky
