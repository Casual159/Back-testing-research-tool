# Analýza implementace AI Agenta

## Architektura agenta

```
Frontend (Next.js) → API Layer → BacktestingAgent (Claude Sonnet 4) → Tool Execution → PostgreSQL
```

Klíčové soubory:
- `agent/core.py` - hlavní třída agenta
- `agent/mcp_server.py` - MCP wrapper pro Claude Code
- `frontend/components/chat/ChatProvider.tsx` - state management

---

## Kategorizace podle AI Agent Patterns

### 1. Tool-Using Agent (ReAct Pattern)

Agent implementuje klasický **ReAct loop** (Reasoning + Acting):

```python
while iterations < MAX_ITERATIONS:
    1. Claude přemýšlí o úkolu
    2. Volá tool (list_strategies, run_backtest, etc.)
    3. Zpracuje výsledek
    4. Opakuje dokud není hotovo
```

**11 nástrojů:** `list_strategies`, `get_strategy`, `check_data`, `fetch_data`, `run_backtest`, `create_strategy`, `get_market_regime`, `save_report`, `list_reports`, `get_report`, `get_data_stats`

### 2. Workflow/Phase-Based Agent

Implementuje **stavový automat** s 6 fázemi workflow:

| Fáze | Účel |
|------|------|
| `STRATEGY_DESIGN` | Návrh strategie s uživatelem |
| `STRATEGY_VALIDATION` | Validace a registrace strategie |
| `DATA_SELECTION` | Výběr/fetch historických dat |
| `BACKTEST_EXECUTION` | Spuštění backtestu |
| `RESULTS_ANALYSIS` | Interpretace metrik |
| `CONVERSATION` | Volná Q&A |

### 3. Domain-Expert Agent

Agent má **vestavěnou doménovou znalost** o tradingu:

- **Regime-aware doporučení:** TREND_UP → MA Crossover, RANGE → RSI Reversal
- **Interpretace metrik:** Sharpe > 2.0 = dobrý, Max DD < 20% = akceptovatelný
- **Varování:** < 30 obchodů = riziko overfittingu

### 4. Streaming/Real-time Agent

Implementuje **Server-Sent Events** s těmito event typy:

| Event | Účel |
|-------|------|
| `text_delta` | Postupné streamování textu |
| `tool_start` | Začátek volání nástroje |
| `tool_progress` | Progress bar (fetch_data) |
| `tool_result` | Výsledek nástroje |
| `done` | Dokončení odpovědi |

---

## Architektonické vzory

| Vzor | Implementace | Soubor |
|------|-------------|--------|
| **HTTP Adapter** | Mapování tools → REST API | `agent/tools.py` |
| **Singleton** | ConversationStorage | `agent/core.py` |
| **Block-Based Messages** | Text + Tool bloky sekvenčně | `ChatProvider.tsx` |
| **MCP Protocol** | Integrace s Claude Code | `mcp_server.py` |

---

## Silné stránky implementace

1. **Multi-modal integrace** - Web UI + MCP server (Claude Code CLI)
2. **Produkční připravenost** - Streaming, cost tracking, persistentní reporty
3. **Domain-specific reasoning** - Agent rozumí backtestingu, ne jen volá nástroje
4. **Confirmation UX** - Chytrá konfirmace jen pro destruktivní akce

## Kategorie pro prezentaci

- ✅ **Tool-Calling Agent** (ReAct pattern)
- ✅ **Workflow Orchestration Agent** (fázový automat)
- ✅ **Domain Expert Agent** (trading knowledge)
- ✅ **Streaming Agent** (real-time SSE)

## Srovnání s frameworky

- Podobný LangChain AgentExecutor, ale **bez závislosti na frameworku**
- Vlastní implementace = plná kontrola nad chováním
- MCP integrace = interoperabilita s Claude ekosystémem
