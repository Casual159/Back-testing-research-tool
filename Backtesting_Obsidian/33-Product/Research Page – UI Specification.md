# Research Page – UI Specification

> Detailní wireframe a specifikace pro `/research` page
> Status: Design draft

---

## Overview

Research page slouží jako **dashboard pro research sessions**. Primární interakce s AI zůstává v chat sidebar - research page pouze zobrazuje a organizuje výsledky.

**Filozofie:** Read-heavy, write-light. Většina akcí spouští chat sidebar.

---

## Page Layout

```
┌────────────────────────────────────────────────────────────────────────────┐
│ HEADER                                                                     │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌─────────────────────────┐  ┌─────────────────────────────────────────┐  │
│  │                         │  │                                         │  │
│  │    NEW RESEARCH         │  │         ACTIVE WORK                     │  │
│  │    (input card)         │  │         (running batches)               │  │
│  │                         │  │                                         │  │
│  └─────────────────────────┘  └─────────────────────────────────────────┘  │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                                                                      │  │
│  │                        RESEARCH LOG                                  │  │
│  │                        (timeline)                                    │  │
│  │                                                                      │  │
│  │                                                                      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
                                                          ┌──────────────────┐
                                                          │  CHAT SIDEBAR    │
                                                          │  (overlay)       │
                                                          └──────────────────┘
```

**Grid:**
- Desktop: 2 columns nahoře (1fr 2fr), full-width dole
- Tablet: stack vertikálně
- Mobile: single column

---

## Komponenty

### 1. Header

```
┌──────────────────────────────────────────────────────────────────────────┐
│  ← Home          RESEARCH LAB                           [Filter] [Sort]  │
└──────────────────────────────────────────────────────────────────────────┘
```

**Elementy:**
- Back link → `/` (Home)
- Title: "Research Lab"
- Filter dropdown: status (all / captured / testing / concluded)
- Sort dropdown: newest / oldest / recently active

**Interakce:**
- Filter/Sort mění zobrazení Research Log

---

### 2. New Research Card

```
┌─────────────────────────────────────────────────────────────────┐
│  📝 NEW RESEARCH                                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  "What's on your mind?"                                         │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │  Start typing a thesis, question, or idea...             │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  [📎 Paste URL]  [🖼 Upload Image]               [Explore →]    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Elementy:**
- Textarea (3-4 řádky, auto-expand)
- Placeholder text
- Action buttons: Paste URL, Upload Image
- Primary CTA: "Explore →"

**Stavy:**
| Stav | Chování |
|------|---------|
| Empty | Placeholder visible, Explore disabled |
| Has text | Explore enabled |
| URL pasted | URL parsed, preview shown |
| Image uploaded | Thumbnail preview |

**Interakce:**
- Click "Explore →" → Opens chat sidebar with pre-filled message
- URL paste → Validates URL, shows domain preview
- Image upload → Shows thumbnail, stores for chat

**Poznámka:** Tato komponenta NEODESÍLÁ přímo do API. Pouze připraví input a otevře chat sidebar.

---

### 3. Active Work Card

```
┌─────────────────────────────────────────────────────────────────┐
│  🔬 ACTIVE WORK                                            2    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Post-halving MA parameter sweep                          │  │
│  │  ████████████░░░░░░░░ 67%                                 │  │
│  │  60/90 tests · ~4 min remaining                           │  │
│  │                                                   [View]  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  MTF analysis comparison                                  │  │
│  │  ░░░░░░░░░░░░░░░░░░░░ queued                              │  │
│  │  0/120 tests · starts after current                       │  │
│  │                                                   [View]  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  No more items in queue                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Elementy:**
- Card header s count badge
- List of BatchJobCard components
- Empty state message

**BatchJobCard sub-component:**
```
┌─────────────────────────────────────────────────────────────────┐
│  {name}                                                         │
│  {progress_bar}                                                 │
│  {progress_text} · {time_estimate}                              │
│                                                         [View]  │
└─────────────────────────────────────────────────────────────────┘
```

**Stavy batch jobu:**
| Status | Progress bar | Time text |
|--------|--------------|-----------|
| queued | Empty/gray | "starts after current" |
| running | Animated fill | "~X min remaining" |
| completed | Full/green | "completed" (then moves to log) |
| failed | Full/red | "failed - click to retry" |

**Interakce:**
- Click [View] → naviguje na session detail s focus na batch
- Progress bar animuje real-time (polling každých 5s)

---

### 4. Research Log (Timeline)

```
┌──────────────────────────────────────────────────────────────────────────┐
│  RESEARCH LOG                                              [Filter ▾]    │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ○ TODAY ─────────────────────────────────────────────────────────────   │
│  │                                                                       │
│  ├─● RSI reversal in range markets                           EXPLORING  │
│  │   "Does RSI < 30 lead to bounce in ranging markets?"                 │
│  │   2 situations defined · 1 batch queued                              │
│  │   Updated 15 min ago                                                 │
│  │                                                                       │
│  ├─● Post-halving momentum effect                             TESTING   │
│  │   "BTC shows significant growth 0-12 months after halving"          │
│  │   1 situation · batch 67% complete                                   │
│  │   Updated just now                                                   │
│  │                                                                       │
│  ○ YESTERDAY ─────────────────────────────────────────────────────────   │
│  │                                                                       │
│  ├─● MA crossover parameter optimization                    CONCLUDED   │
│  │   ✓ Validated · Best config: EMA(8,30) on 4h                        │
│  │   3 batches · 270 total tests                                       │
│  │   Completed yesterday at 14:32                                       │
│  │                                                                       │
│  ├─● "BTC dumps after FOMC announcements"                  INVALIDATED  │
│  │   ✗ No statistical significance found                               │
│  │   1 batch · 48 tests                                                │
│  │   Completed yesterday at 11:15                                       │
│  │                                                                       │
│  ○ THIS WEEK ─────────────────────────────────────────────────────────   │
│  │                                                                       │
│  └─● Bollinger squeeze breakout strategy                     CAPTURED   │
│      Initial thesis captured · needs situation definition               │
│      Created 3 days ago                                                 │
│                                                                          │
│  ─────────────────────────────────────────────────────────────────────   │
│  [Load more]                                                             │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

**Elementy:**
- Time group headers (Today, Yesterday, This Week, Earlier)
- SessionCard pro každou session
- Load more button (pagination)

**SessionCard sub-component:**
```
┌─────────────────────────────────────────────────────────────────┐
│  ● {title}                                            {status}  │
│    {subtitle / thesis summary}                                  │
│    {metadata line}                                              │
│    {timestamp}                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Status badges:**
| Status | Color | Icon |
|--------|-------|------|
| CAPTURED | gray | ○ |
| EXPLORING | blue | ◐ |
| TESTING | yellow | ◑ |
| CONCLUDED (validated) | green | ✓ |
| CONCLUDED (invalidated) | red | ✗ |
| CONCLUDED (inconclusive) | gray | ? |

**Interakce:**
- Click session → naviguje na `/research/{session_id}`
- Hover → subtle highlight
- Status badge → tooltip s detailem

---

## Session Detail Page (`/research/{id}`)

```
┌──────────────────────────────────────────────────────────────────────────┐
│  ← Research Lab       POST-HALVING MOMENTUM EFFECT              [Edit]  │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  STATUS: TESTING                                  Created: 2 hours ago   │
│                                                                          │
│  ┌─ ORIGINAL INPUT ───────────────────────────────────────────────────┐  │
│  │                                                                    │  │
│  │  "Slyšel jsem v podcastu, že po halvingu Bitcoin vždycky roste   │  │
│  │   12 měsíců"                                                      │  │
│  │                                                                    │  │
│  │  Source: Manual input                          [Continue in chat]  │  │
│  │                                                                    │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌─ THESIS ───────────────────────────────────────────────────────────┐  │
│  │                                                                    │  │
│  │  "BTC vykazuje statisticky významný růst v období 0-12 měsíců    │  │
│  │   po halvingu ve srovnání s jinými obdobími"                      │  │
│  │                                                                    │  │
│  │  Domains: [timing] [supply-cycle] [macro-event]                   │  │
│  │                                                                    │  │
│  │  Validation: ○ Pending                                             │  │
│  │                                                                    │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌─ SITUATIONS ───────────────────────────────────────────────────────┐  │
│  │                                                                    │  │
│  │  ┌──────────────────────────────────────────────────────────────┐  │  │
│  │  │  📍 Post-halving accumulation phase                          │  │  │
│  │  │                                                              │  │  │
│  │  │  CONDITIONS:                                                 │  │  │
│  │  │  • Timing: 0-180 days after halving event                   │  │  │
│  │  │  • Regime: NOT trend_down                                   │  │  │
│  │  │  • Volatility: ATR declining (consolidation)                │  │  │
│  │  │                                                              │  │  │
│  │  │  NOTES:                                                      │  │  │
│  │  │  "Období konsolidace po halvingu, kdy supply shock ještě    │  │  │
│  │  │   není plně absorbován trhem. Historicky předchází          │  │  │
│  │  │   významné rally."                                          │  │  │
│  │  │                                                              │  │  │
│  │  │  OCCURRENCES: 3 periods · 540 total days                    │  │  │
│  │  │  • 2012-11-28 → 2013-05-28 (181 days)                       │  │  │
│  │  │  • 2016-07-09 → 2017-01-09 (184 days)                       │  │  │
│  │  │  • 2020-05-11 → 2020-11-11 (184 days)                       │  │  │
│  │  │                                                              │  │  │
│  │  │  [Test strategies in this situation]              [Edit]    │  │  │
│  │  │                                                              │  │  │
│  │  └──────────────────────────────────────────────────────────────┘  │  │
│  │                                                                    │  │
│  │  [+ Define another situation]                                      │  │
│  │                                                                    │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌─ BATCH TESTS ──────────────────────────────────────────────────────┐  │
│  │                                                                    │  │
│  │  ┌──────────────────────────────────────────────────────────────┐  │  │
│  │  │  🧪 MA Crossover Parameter Sweep                   RUNNING   │  │  │
│  │  │                                                              │  │  │
│  │  │  Strategy: MA Crossover                                      │  │  │
│  │  │  Parameters: fast[5,8,10,12,15] × slow[20,30,50] × [SMA,EMA]│  │  │
│  │  │  Timeframes: 1h, 4h, 1d                                      │  │  │
│  │  │  Periods: all 3 halving cycles                               │  │  │
│  │  │                                                              │  │  │
│  │  │  ████████████░░░░░░░░ 60/90 tests                           │  │  │
│  │  │  Elapsed: 12 min · Remaining: ~4 min                        │  │  │
│  │  │                                                              │  │  │
│  │  │  [View results]  [View log]  [Cancel]                       │  │  │
│  │  │                                                              │  │  │
│  │  └─────────────────────────────────────────────────���────────────┘  │  │
│  │                                                                    │  │
│  │  [+ Add batch test]                                                │  │
│  │                                                                    │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

**Sekce:**
1. **Header** - title, status, timestamps, edit button
2. **Original Input** - co uživatel napsal/vložil, link to continue in chat
3. **Thesis** - formalizovaná teze, domain tags, validation status
4. **Situations** - list situací s conditions a markdown notes
5. **Batch Tests** - list batch testů s progress/results

**Interakce:**
- [Continue in chat] → otevře sidebar s kontextem této session
- [Test strategies...] → otevře sidebar s promptem pro batch formulaci
- [+ Define another situation] → otevře sidebar
- [View results] → expanduje výsledky inline nebo modal

---

## Batch Results View (inline nebo modal)

```
┌──────────────────────────────────────────────────────────────────────────┐
│  MA CROSSOVER PARAMETER SWEEP                              ✓ COMPLETED  │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  90 tests · 16 minutes · Situation: Post-halving accumulation           │
│                                                                          │
│  ┌─ AI SUMMARY ───────────────────────────────────────────────────────┐  │
│  │                                                                    │  │
│  │  EMA-based configurations consistently outperform SMA across all  │  │
│  │  tested periods. The 4h timeframe shows best risk-adjusted        │  │
│  │  returns with optimal fast_period in 8-12 range.                  │  │
│  │                                                                    │  │
│  │  Key findings:                                                     │  │
│  │  • EMA outperforms SMA by +0.4 Sharpe on average                  │  │
│  │  • 4h timeframe dominates (8 of top 10 results)                   │  │
│  │  • Results consistent across all 3 halving cycles ✓               │  │
│  │                                                                    │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌─ TOP 5 CONFIGURATIONS ─────────────────────────────────────────────┐  │
│  │                                                                    │  │
│  │  #  │ Fast │ Slow │ Signal │  TF  │ Sharpe │ Return │ MaxDD       │  │
│  │  ───┼──────┼──────┼────────┼──────┼────────┼────────┼─────────    │  │
│  │  1  │   8  │  30  │  EMA   │  4h  │  2.81  │ +156%  │  -12%  [→] │  │
│  │  2  │  10  │  30  │  EMA   │  4h  │  2.64  │ +142%  │  -14%  [→] │  │
│  │  3  │   8  │  20  │  EMA   │  4h  │  2.41  │ +138%  │  -11%  [→] │  │
│  │  4  │  12  │  30  │  EMA   │  4h  │  2.38  │ +134%  │  -15%  [→] │  │
│  │  5  │   8  │  30  │  EMA   │  1d  │  2.21  │ +128%  │  -18%  [→] │  │
│  │                                                                    │  │
│  │  [Show all 90 results]                                             │  │
│  │                                                                    │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌─ PARAMETER HEATMAP ────────────────────────────────────────────────┐  │
│  │                                                                    │  │
│  │  Sharpe Ratio by fast × slow (EMA, 4h timeframe)                  │  │
│  │                                                                    │  │
│  │           │   20    30    50                                       │  │
│  │      ─────┼─────────────────                                       │  │
│  │        5  │  ░░░   ▒▒▒   ░░░      Legend:                         │  │
│  │        8  │  ▓▓▓   ███   ▒▒▒      ███ > 2.5                       │  │
│  │       10  │  ▒▒▒   ▓▓▓   ▒▒▒      ▓▓▓ 2.0-2.5                     │  │
│  │       12  │  ▒▒▒   ▓▓▓   ░░░      ▒▒▒ 1.5-2.0                     │  │
│  │       15  │  ░░░   ▒▒▒   ░░░      ░░░ < 1.5                       │  │
│  │                                                                    │  │
│  │  [Sharpe] [Return] [MaxDD] [WinRate]     ← toggle metric          │  │
│  │                                                                    │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌─ ACTIONS ──────────────────────────────────────────────────────────┐  │
│  │                                                                    │  │
│  │  [Save #1 as strategy]  [Run deeper test]  [Export CSV]           │  │
│  │                                                                    │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

**Sekce:**
1. **Header** - název, status, metadata
2. **AI Summary** - klíčové závěry
3. **Top Configurations** - tabulka nejlepších výsledků
4. **Parameter Heatmap** - vizualizace závislostí
5. **Actions** - další kroky

---

## Empty States

### No sessions yet
```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                    🔬                                           │
│                                                                 │
│            No research sessions yet                             │
│                                                                 │
│    Start by typing a thesis, question, or idea above.          │
│    The AI will help you explore and validate it.               │
│                                                                 │
│              [Start your first research →]                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### No active batches
```
┌─────────────────────────────────────────────────────────────────┐
│  🔬 ACTIVE WORK                                            0    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  No batch tests running                                         │
│                                                                 │
│  When you run batch tests, they'll appear here                 │
│  with real-time progress.                                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Responzivita

### Desktop (>1024px)
- 2-column layout nahoře
- Full-width research log
- Chat sidebar 420px

### Tablet (768-1024px)
- Stack: New Research → Active Work → Log
- Chat sidebar full-width overlay

### Mobile (<768px)
- Single column
- New Research collapsed to button
- Chat jako separate page místo sidebar

---

## Integrace s existujícím Chat Sidebar

**Klíčový princip:** Research page NEVOLÁ API přímo. Všechny write operace jdou přes chat.

| Akce na Research Page | Co se stane |
|----------------------|-------------|
| Click "Explore →" | Otevře sidebar s pre-filled message |
| Click "Continue in chat" | Otevře sidebar s kontextem session |
| Click "Test strategies..." | Otevře sidebar s batch formulation prompt |
| Click "+ Define situation" | Otevře sidebar s situation definition prompt |
| Click "+ Add batch test" | Otevře sidebar s batch formulation prompt |

**Chat context passing:**
```typescript
openSidebarWithContext({
  sessionId: "uuid",
  prefillMessage: "I want to test MA strategies in this situation",
  focusArea: "batch_formulation"
})
```

---

## Mock Data Structure

Pro implementaci mockupu potřebujeme:

```typescript
interface ResearchSession {
  id: string;
  title: string;
  originalInput: string;
  inputType: 'text' | 'url' | 'image';
  status: 'captured' | 'exploring' | 'testing' | 'concluded';
  validationResult?: 'validated' | 'invalidated' | 'inconclusive';
  createdAt: Date;
  updatedAt: Date;
  thesis?: Thesis;
  situations: Situation[];
  batchTests: BatchTest[];
}

interface Thesis {
  content: string;
  domains: string[];
  aiConfidence: number;
  validationStatus: 'pending' | 'validated' | 'invalidated' | 'inconclusive';
}

interface Situation {
  id: string;
  name: string;
  conditions: Record<string, any>;
  descriptionMd: string;
  occurrences: { start: string; end: string }[];
  totalDays: number;
}

interface BatchTest {
  id: string;
  name: string;
  strategyName: string;
  testMatrix: Record<string, any>;
  totalTests: number;
  completedTests: number;
  status: 'queued' | 'running' | 'completed' | 'failed';
  startedAt?: Date;
  completedAt?: Date;
  results?: BatchResults;
}

interface BatchResults {
  aiSummary: string;
  keyFindings: string[];
  topPerformers: TestResult[];
  allResults: TestResult[];
}

interface TestResult {
  params: Record<string, any>;
  metrics: {
    sharpe: number;
    return: number;
    maxDrawdown: number;
    winRate: number;
  };
}
```

---

## Další kroky

1. [ ] Implementovat mock data
2. [ ] Postavit ResearchPage component
3. [ ] Postavit SessionCard component
4. [ ] Postavit BatchJobCard component
5. [ ] Postavit SessionDetail page
6. [ ] Integrovat s chat sidebar context
