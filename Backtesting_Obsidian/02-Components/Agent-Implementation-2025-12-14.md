# Agent Implementation

**Datum:** 2025-12-14

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
├── ChatProvider.tsx     # Context provider, block-based state
├── ChatSidebar.tsx      # Slide-out chat panel (fixed right)
├── ChatMessage.tsx      # Block-based message rendering
├── ChatInput.tsx        # Input field with auto-resize
├── ToolCard.tsx         # Expandable tool call card
├── ConfirmationCard.tsx # Action confirmation UI
├── ChatToggleButton.tsx # FAB toggle button
├── MainContent.tsx      # Push-layout wrapper
└── index.ts             # Exports
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

## Změny 2025-12-14: UX Vylepšení

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

## Změny 2025-12-15: Streaming Progress Bar

### Problém
Stahování dat z Binance může trvat desítky sekund. Uživatel neviděl progress - jen pulsující tečku.

### Řešení: Real-time progress streaming

#### Architektura

```
BinanceBulkFetcher          API                    Agent              Frontend
     │                       │                       │                   │
     │  yield progress       │                       │                   │
     ├──────────────────────►│  SSE: progress        │                   │
     │  (per file)           ├──────────────────────►│  tool_progress    │
     │                       │                       ├──────────────────►│
     │                       │                       │                   │  Update UI
     │  yield done           │                       │                   │
     ├──────────────────────►│  SSE: done            │                   │
     │                       ├──────────────────────►│  tool_result      │
     │                       │                       ├──────────────────►│
```

#### Backend změny

**`core/data/bulk_fetcher.py`**
```python
def fetch_historical_with_progress(self, symbol, timeframe, start_date, end_date):
    """Generator yielding progress events"""
    # Pro každý stažený soubor (monthly/daily):
    yield {"type": "progress", "current": N, "total": M, "pct": 0-100}
    # Na konci:
    yield {"type": "done", "df": DataFrame, "candles": count}
```

**`api/main.py`** - nový endpoint
```python
@app.post("/api/data/fetch/stream")
async def fetch_data_stream(request: DataFetchRequest):
    """SSE endpoint pro streaming progress"""
    async def event_generator():
        for event in fetcher.fetch_historical_with_progress(...):
            yield f"data: {json.dumps(event)}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

**`agent/core.py`** - speciální handling pro fetch_data
```python
if block.name == "fetch_data":
    async for event in self._fetch_data_with_progress(block.input):
        if event["type"] == "progress":
            yield {"type": "tool_progress", "tool": "fetch_data", ...}
        elif event["type"] == "done":
            result = event["result"]
```

#### Frontend změny

**`ChatProvider.tsx`** - nový event type
```typescript
case 'tool_progress':
    currentActiveTools[idx].progress = {
        current: event.current,
        total: event.total,
        pct: event.pct
    };
```

**`ChatMessage.tsx`** - ToolBadge s progress barem
```tsx
{hasProgress && (
    <span
        className="absolute inset-0 bg-blue-600/30"
        style={{ width: `${progress.pct}%` }}
    />
)}
{hasProgress && <span>{progress.pct}%</span>}
```

#### Event flow

| Event Type | Source | Payload |
|------------|--------|---------|
| `tool_start` | agent | `{tool: "fetch_data", args: {...}}` |
| `tool_progress` | agent | `{tool: "fetch_data", current: 5, total: 12, pct: 41}` |
| `tool_result` | agent | `{tool: "fetch_data", result: {...}, success: true}` |

#### UI chování

1. **Před progress:** Pulsující modrá tečka
2. **S progress:** Modrý progress bar vyplňující badge zleva doprava + procenta
3. **Po dokončení:** Šedý badge s výsledkem ("8761 candles")

---

## Změny 2025-12-17: Block-based Message Structure & UI Redesign

### Problém
1. **Agregace místo sekvence:** Text se kumuloval nahoře, tool cally dole - neodpovídalo reálnému průběhu konverzace
2. **Vizuální nesoulad:** Chat panel překrýval obsah aplikace
3. **Nekonzistentní styling:** Barvy neseděly se zbytkem UI

### Řešení

#### 1. Block-based Message Structure

**Před:** Flat message s `content: string` + `toolCalls: ToolCall[]`
```typescript
interface Message {
  content: string;
  toolCalls?: ToolCall[];
  activeTools?: ActiveTool[];
}
```

**Po:** Sekvenční bloky
```typescript
interface TextBlock {
  type: 'text';
  content: string;
}

interface ToolBlock {
  type: 'tool';
  id: string;
  name: string;
  args: Record<string, unknown>;
  status: 'running' | 'completed' | 'error';
  result?: Record<string, unknown>;
  progress?: { current: number; total: number; pct: number };
}

type MessageBlock = TextBlock | ToolBlock;

interface Message {
  role: 'user' | 'assistant';
  blocks: MessageBlock[];
  timestamp: Date;
  isStreaming?: boolean;
}
```

**Streaming logika (`ChatProvider.tsx`):**
```typescript
case 'text_delta':
  // Pokud je poslední blok text, připojit; jinak vytvořit nový
  if (lastBlock?.type === 'text') {
    lastBlock.content += event.delta;
  } else {
    blocks.push({ type: 'text', content: event.delta });
  }

case 'tool_start':
  blocks.push({ type: 'tool', id: toolId, name: event.tool, status: 'running', ... });

case 'tool_result':
  // Najít běžící tool a updatovat status
  block.status = event.success ? 'completed' : 'error';
  block.result = event.result;
```

#### 2. Sidebar Push Layout

**Před:** Overlay přes celou stránku
**Po:** Sidebar odsouvá hlavní obsah

Nová komponenta `MainContent.tsx`:
```tsx
export function MainContent({ children }: { children: ReactNode }) {
  const { isOpen } = useChatContext();
  return (
    <div className={`min-h-screen transition-all duration-300 ${
      isOpen ? 'sm:mr-[420px]' : ''
    }`}>
      {children}
    </div>
  );
}
```

Layout wrapping:
```tsx
<ChatProvider>
  <MainContent>{children}</MainContent>
  <ChatSidebar />
  <ChatToggleButton />
</ChatProvider>
```

#### 3. Claude VSCode-like Conversation Layout

**User zprávy:** Bubble vpravo (modrá)
```tsx
<div className="flex justify-end px-4 py-2">
  <div className="rounded-2xl rounded-br-md px-4 py-2.5 bg-blue-600 text-white">
    {textContent}
  </div>
</div>
```

**Assistant zprávy:** Flat text s vertikální čárou vlevo
```tsx
<div className="relative pl-4 pr-4 py-2">
  <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-neutral-700" />
  <div className="pl-4">
    {blocks.map(block => ...)}
  </div>
</div>
```

#### 4. Expandable ToolCard

Color-coded podle typu toolu:
```typescript
const TOOL_META = {
  list_strategies: { label: 'List Strategies', icon: '📋', color: 'blue' },
  run_backtest: { label: 'Run Backtest', icon: '⚡', color: 'orange' },
  fetch_data: { label: 'Fetch Data', icon: '⬇️', color: 'green' },
  // ...
};
```

Expandable pro zobrazení parametrů a výsledků:
- Collapsed: Ikona + název + stručný summary
- Expanded: Parametry + výsledky v gridu

### Výsledek

- **Sekvenční zobrazení:** Text a tool cally se zobrazují v pořadí, jak přicházejí
- **Čistší layout:** Sidebar neblokuje hlavní obsah
- **Konzistentní styling:** `neutral-*` palette napříč aplikací
- **Lepší UX:** Expandable tool cards pro detail on-demand

---

## Poznámky k vývoji

- Agent používá in-memory storage pro konverzace (production: přepnout na DB)
- Cost tracking: $3/1M input, $15/1M output (claude-sonnet-4)
- Max 20 tool call iterací per request
- Streaming progress funguje pouze pro `fetch_data` tool (ostatní jsou okamžité)
