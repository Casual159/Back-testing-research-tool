# Agent Implementation

**Datum:** 2024-12-14

## Přehled

Implementace AI agenta pro backtesting research tool. Agent pomáhá uživatelům navrhovat strategie, spouštět backtesty a analyzovat výsledky.

---

## Architektura

```
agent/
├── core.py          # Hlavní agent třída (BacktestingAgent)
├── prompts.py       # System prompt a šablony
├── schemas.py       # Pydantic modely
├── protocols.py     # Abstraktní protokoly
├── mcp_server.py    # MCP server wrapper
└── cli.py           # CLI interface

frontend/components/chat/
├── ChatProvider.tsx    # Context provider, state management
├── ChatSidebar.tsx     # Slide-out chat panel
├── ChatMessage.tsx     # Message rendering
├── ChatInput.tsx       # Input field
├── ConfirmationCard.tsx # Action confirmation UI
└── index.ts            # Exports
```

---

## Backend Agent (`agent/core.py`)

### Klíčové komponenty

**BacktestingAgent** - hlavní třída
- Používá Anthropic Claude API (claude-sonnet-4)
- Agentic loop s max 20 iteracemi
- Tool calling pro interakci s backtesting API

**Tools:**
- `list_strategies` - seznam dostupných strategií
- `get_strategy` - detail strategie
- `check_data` - dostupnost dat
- `fetch_data` - stažení dat z Binance
- `get_market_regime` - aktuální tržní režim
- `run_backtest` - spuštění backtestu
- `create_strategy` - vytvoření nové strategie
- `save_report` - uložení výsledků
- `suggest_enhancement` - návrhy na vylepšení

**Fáze workflow:**
- STRATEGY_DESIGN
- STRATEGY_VALIDATION
- DATA_SELECTION
- BACKTEST_EXECUTION
- RESULTS_ANALYSIS
- CONVERSATION (volná konverzace)

---

## Frontend Chat (`frontend/components/chat/`)

### ChatProvider
- Globální state pro chat (messages, conversationId, phase)
- Komunikace s `/api/agent/chat` endpoint
- Tracking nákladů (tokens, USD)

### ChatSidebar
- Slide-out panel z pravé strany
- Toggle button vždy viditelný

### Stylování
- **Barvy:** `neutral-*` palette (sladění s aplikací)
- **Avatary:** 7x7 rounded-md, neutrální barvy
- **Message bubbles:** Minimalistické, bez emoji

---

## Database (`migrations/003_add_agent_tables.sql`)

### Tabulky

**backtest_reports**
- Snapshot výsledků backtestu
- Core metriky (return, sharpe, drawdown, win_rate)
- Extended metriky (calmar, sortino, recovery_factor)
- Vizualizační data (equity_curve, trades, drawdown_curve)
- AI interpretace (summary, recommendations, concerns)

**conversations**
- Historie zpráv
- Phase a context
- Usage tracking (tokens, cost)

**agent_suggestions**
- Návrhy na vylepšení od agenta
- Kategorie: indicator, metric, visualization, strategy, data

---

## Změny 2024-12-14: UX Vylepšení

### Problém
Agent byl příliš upovídaný:
- Dlouhé odpovědi i na jednoduché otázky
- Emoji a zbytečné formátování
- Confirmation dialog na každou otázku "would you like..."
- Vizuálně nesedící s aplikací (modrá barva)

### Řešení

#### 1. Zjednodušený prompt (`prompts.py`)
**Před:** 99 řádků s tutoriály, tabulkami metrik, workflow fázemi
**Po:** 37 řádků zaměřených na stručnost

Klíčové instrukce:
```
- Be concise. Users know the basics.
- No emoji. Clean, professional output.
- Answer directly. Skip preambles like "I'd be happy to help..."
- Data first. Show numbers, then brief interpretation.
```

#### 2. Confirmation jen pro akce (`core.py`)
**Před:** Detekce frází "would you like", "shall i" → confirmation na vše
**Po:** Confirmation jen pro:
- "run this backtest" / "run the backtest"
- "create this strategy" / "register this strategy"

#### 3. Dynamická tlačítka (`ConfirmationCard.tsx`)
**Před:** Statické "Yes, proceed" / "No, let me adjust"
**Po:** Kontextová:
- Backtest → "Run" / "Cancel"
- Strategy → "Create" / "Cancel"
- Fetch → "Fetch" / "Cancel"

#### 4. Vizuální sladění
- `blue-*` → `neutral-*`
- Avatary: menší, hranatější
- Tool calls: jednodušší zobrazení bez emoji

---

## API Endpoints

```
POST /api/agent/chat
  Body: { message: string, conversation_id?: UUID }
  Response: AgentChatResponse

GET /api/agent/conversations
GET /api/agent/conversations/{id}

POST /api/reports
GET /api/reports
GET /api/reports/{id}

POST /api/suggestions
GET /api/suggestions
```

---

## Použití

### CLI
```bash
cd agent
python cli.py
```

### Frontend
Chat sidebar dostupný přes tlačítko v pravém dolním rohu nebo kliknutím na "Research Agent" kartu na homepage.

---

## Poznámky k vývoji

- Agent používá in-memory storage pro konverzace (production: přepnout na DB)
- Cost tracking: $3/1M input, $15/1M output (claude-sonnet-4)
- Max 20 tool call iterací per request
