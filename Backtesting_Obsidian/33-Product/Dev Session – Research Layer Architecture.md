# Dev Session – Research Layer Architecture

> Ideation session: 2024-12-22
> Status: Exploratory design

---

## Kontext

Navazuje na [[Research Layer – User Stories]] a [[Research-First Vision]]. Cílem bylo navrhnout architekturu pro research layer - od UI přes entity až po batch testing.

---

## Současný stav (baseline)

### Agent
- ReAct pattern s Claude API (sonnet-4)
- 11 tools (strategies, backtest, data, reports...)
- 6-fázový workflow: STRATEGY_DESIGN → VALIDATION → DATA → EXECUTION → ANALYSIS → COMPLETE
- **In-memory** conversation storage (netrvalé) ← TODO
- SSE streaming + MCP integrace

### Frontend
- 6 sekcí: Home, Chat, Data, Strategies, Backtest, Results
- Chat sidebar jako primární interakce s agentem
- Block-based rendering (text + tool calls)

### Gap

| Produkt požaduje | Současný stav |
|------------------|---------------|
| Thesis → Situation → Strategy | Agent jde rovnou: Strategy → Backtest |
| Knihovna situací (komplexní) | Pouze `regime_filter` (5 hodnot) |
| Knowledge base (perzistence) | Žádná perzistence tezí/situací |
| Sokratovský dialog | Agent odpovídá, ale nechallenuje |

---

## Architektonické varianty

### Varianta A: Research Board jako separátní sekce
```
/research
├── /board          # Hlavní deska s tezemi
├── /thesis/[id]    # Detail teze
├── /situations     # Knihovna situací
└── /knowledge      # Knowledge base
```

### Varianta B: Rozšíření Chat jako "Research Mode"
Chat zůstává primární interface, agent se přepne do research mode.

### Varianta C: Hybrid (doporučeno)
- **Chat** = primární interakce, research mode enabled
- **Research Board** = read-only dashboard nad perzistovanými daty

```
Chat (sidebar) → vytváří teze, situace, backtesty
                         ↓
Research Board → zobrazuje, filtruje, organizuje
```

---

## Klíčové rozhodnutí

**Conversation = Research Session**

Research log operuje na úrovni research session (= conversation s metadaty). Každá konverzace s agentem je potenciálně research session.

---

## Navržené entity (DB schema)

```sql
-- Hlavní research entita (rozšířená conversation)
research_sessions (
  id UUID PRIMARY KEY,
  title TEXT,                    -- AI-generated nebo user-defined
  initial_input TEXT,            -- původní myšlenka/URL/popis
  input_type TEXT,               -- 'text' | 'url' | 'image'
  status TEXT,                   -- 'captured' | 'exploring' | 'testing' | 'concluded'
  created_at, updated_at
)

-- Teze extrahované z session
theses (
  id UUID PRIMARY KEY,
  session_id UUID REFERENCES research_sessions,
  content TEXT,                  -- formalizovaná teze
  domain TEXT[],                 -- ['timing', 'mean_reversion', 'volatility']
  validation_status TEXT,        -- 'pending' | 'validated' | 'invalidated' | 'inconclusive'
  ai_confidence FLOAT,           -- 0-1 jak moc si AI věří
  created_at
)

-- Situace - flexibilní struktura
situations (
  id UUID PRIMARY KEY,
  thesis_id UUID REFERENCES theses,
  name TEXT,

  -- Structured conditions (co umíme programaticky)
  conditions JSONB,              -- {"regime": ["TREND_UP"], "volatility": "low", ...}

  -- Fallback markdown (co neumíme, ale AI popsalo)
  description_md TEXT,           -- "180 dní po halvingu, DXY klesá, ..."

  -- Metadata
  historical_occurrences JSONB,  -- [{"start": "2020-05-11", "end": "2020-11-11"}, ...]
  total_days INT,
  created_at
)

-- Batch test definice
batch_tests (
  id UUID PRIMARY KEY,
  situation_id UUID REFERENCES situations,
  name TEXT,
  test_matrix JSONB,             -- parametry k testování
  total_tests INT,
  status TEXT,                   -- 'queued' | 'running' | 'completed' | 'failed'
  progress INT,                  -- 0-100
  started_at, completed_at
)

-- Jednotlivé testy v batchi
batch_test_runs (
  id UUID PRIMARY KEY,
  batch_id UUID REFERENCES batch_tests,
  params JSONB,                  -- {"strategy": "MA Cross", "fast": 10, ...}
  metrics JSONB,                 -- {"return": 0.45, "sharpe": 1.2, ...}
  status TEXT,
  executed_at
)

-- AI interpretace batch výsledků
batch_insights (
  id UUID PRIMARY KEY,
  batch_id UUID REFERENCES batch_tests,
  summary TEXT,
  top_performers JSONB,
  recommendations TEXT[],
  concerns TEXT[],
  created_at
)
```

---

## Batch Testing Workflow

### Krok 1: AI navrhne exploration space
```
SITUACE: Post-halving accumulation

AI: "Návrh exploration space:

     STRATEGIE: MA Crossover
     ├── fast_period: [5, 8, 10, 12, 15]
     ├── slow_period: [20, 30, 50]
     └── signal: [SMA, EMA]

     TIMEFRAMES: [1h, 4h, 1d]

     = 5 × 3 × 2 × 3 = 90 testů"
```

### Krok 2: Batch execution
- PostgreSQL-based queue (ne Redis/Celery pro začátek)
- Worker = background asyncio task
- Progress tracking via polling nebo SSE

### Krok 3: AI agregace výsledků
- Top performers tabulka
- Pattern insights (co funguje kdy)
- Heatmapy pro vizualizaci
- Robustness check

---

## UI Wireframes

### Research Page Overview
```
┌─────────────────────────────────────────────────────────────────┐
│  📝 NEW RESEARCH          │  🔬 ACTIVE BATCHES                  │
│  [Start typing...]        │  ├── Post-halving MA ████░░ 67%    │
│  [URL] [Image]            │  └── MTF comparison (queued)       │
├─────────────────────────────────────────────────────────────────┤
│  RESEARCH LOG                                                   │
│  ○ TODAY                                                        │
│  ├─● RSI reversal in ranges              TESTING               │
│  ├─● Post-halving momentum               TESTING               │
│  ○ YESTERDAY                                                    │
│  ├─● MA crossover optimization         CONCLUDED ✓             │
│  └─● "BTC dumps on FOMC"              INVALIDATED ✗            │
└─────────────────────────────────────────────────────────────────┘
```

### Research Session Detail
- Original input
- Thesis (formalized)
- Situations (conditions + markdown description)
- Batch tests (matrix + progress + results)

### Batch Results View
- AI summary
- Top performers table
- Heatmaps (Sharpe by fast × slow)
- Actions: Save as strategy, Run deeper test, Export

### Batch Formulation Modal
- Strategy selection
- Parameter ranges to sweep
- Dimensions (timeframes, symbols, periods)
- AI suggestion pro zúžení scope
- Estimate (tests count, duration)

---

## Multi-agent úvaha

**Závěr: Nedoporučeno** pro tento use case.

| Multi-agent | Proč ne |
|-------------|---------|
| Složitost orchestrace | Jeden agent s tools stačí |
| Latence (agent → agent) | Uživatel čeká déle |
| Debugging | Těžší stopovat chyby |

**Alternativa:** Specializované prompty (ne agenti) - agent se přepíná mezi "research mode" a "execution mode" podle kontextu.

**Výjimka pro budoucnost:** Background agent pro proaktivní návrhy (US-R11).

---

## Implementační plán

### Fáze 1: Persistence (základ)
- [ ] Přesunout conversations z in-memory do PostgreSQL
- [ ] Conversation = Research Session (s metadaty)

### Fáze 2: UI Mockup
- [ ] `/research` page s mock daty
- [ ] Research log timeline
- [ ] Session detail view

### Fáze 3: Agent thesis capture
- [ ] Rozšířit prompt o research instrukce
- [ ] Nový tool: `save_thesis`
- [ ] Agent rozpozná a formalizuje tezi

### Fáze 4: Situations
- [ ] Situation entity s conditions + markdown fallback
- [ ] Agent navrhuje situace z teze

### Fáze 5: Batch Testing
- [ ] Queue system (PostgreSQL-based)
- [ ] Batch formulation UI
- [ ] Results agregace + AI insights

---

## Další kroky (rozhodnuto)

1. **UI Mockup first** - postavit `/research` s mock daty
2. **Persistence** - conversations do DB
3. **Thesis capture** - agent rozpozná a uloží tezi

Batch testing až později, když vidíme jak thesis/situation fungují v praxi.

---

## Související dokumenty

- [[Research Layer – User Stories]]
- [[Research-First Vision]]
- [[Product-Implementation Gap Analysis]]
