# Product-Implementation Gap Analysis

> Analýza shody mezi produktovou vizí (Product Charter) a aktuální implementací

---

## Kontext

Tento dokument mapuje, jak se **současná technická implementace** překrývá s **produktovou vizí** definovanou v [[Product Charter – AI Trading Research Tool]].

Datum analýzy: 2024-12

---

## 1. Silné shody (již implementováno)

### AI jako kurátor poznání ✅

Charter definuje:
> *"AI provádí vyhodnocení, interpretuje výsledky v kontextu uživatelova záměru, komentuje poznání a upozorňuje na vzorce, limity a rizika."*

**Implementace:**
- Agent má vestavěnou doménovou znalost (`agent/prompts.py`)
- Interpretuje metriky: "Sharpe pod 1.0 = problém", "< 30 obchodů = riziko overfittingu"
- Regime-aware doporučení: TREND_UP → MA Crossover, RANGE → RSI Reversal
- Varování a limity jsou součástí promptů

**Závěr:** Toto je **klíčový diferenciátor** produktu. Většina konkurence jsou buď hype generátory nebo suché backtesting enginy. Náš agent **učí a varuje**.

---

### Workflow fáze = skeleton pro onboarding ✅

Charter definuje onboarding kroky:
1. Formulace hypotézy
2. Automatizované sestavení testů
3. Běh backtestů/simulací
4. Interpretace výsledků pomocí AI

**Implementace – 6 fází agenta:**

| Charter: Onboarding krok | Implementace: Workflow fáze |
|-------------------------|----------------------------|
| Formulace hypotézy | `STRATEGY_DESIGN` |
| Sestavení testů | `STRATEGY_VALIDATION` + `DATA_SELECTION` |
| Běh backtestů | `BACKTEST_EXECUTION` |
| Interpretace výsledků | `RESULTS_ANALYSIS` |
| Volná Q&A | `CONVERSATION` |

**Závěr:** Tutorial není nová feature – je to **guided mode** existujícího workflow. Agent už umí ty fáze, potřebuje jen "tutorial prompt" variantu s více vysvětlováním.

---

### Streaming a real-time UX ✅

Charter zmiňuje "wow efekt" během interakce.

**Implementace:**
- Server-Sent Events (SSE)
- Postupné streamování textu (`text_delta`)
- Progress indikátory pro dlouhé operace (`tool_progress`)
- Block-based rendering v UI

**Závěr:** Technický základ pro "wow efekt" existuje.

---

## 2. Částečné shody (skeleton existuje)

### Onboarding tutorial 🟡

**Charter:** 30 minut soustředění → "aha moment"

**Stav:**
- Workflow fáze existují
- Chybí: dedicated tutorial mode, progress tracking, "first run" detekce

**Potřebná práce:**
- Tutorial prompt varianta (více vysvětlování, méně expertního jazyka)
- Vizuální progress indikátor (krok 1/4, 2/4...)
- Persistentní stav "tutorial completed"

**Náročnost:** Střední

---

## 3. Významné gapy (chybí)

### Paper trading / Testnet simulace ❌

**Charter:**
> *"Simulované provádění obchodních příkazů, připojení výhradně k testnetům burz, časově omezené běhy (7 dní)"*

**Stav:**
- ✅ Historický backtest
- ❌ Forward-test / paper trading
- ❌ Testnet integrace (Binance testnet)
- ❌ Scheduling pro multi-day běhy

**Technická implikace:**
- Live/delayed data feed
- Order state management přes dny
- Notification systém (email/webhook)
- Architektonicky oddělitelný modul

**Náročnost:** Vysoká

---

### Export strategie ❌

**Charter:**
> *"Export logiky strategie – formáty: pseudokód, Python, Pine, JSON"*

**Stav:** Neimplementováno

**Řešení:**
Přidat tool `export_strategy(format: "pine" | "python" | "json" | "pseudocode")`

AI umí generovat tyto formáty snadno – jde jen o:
1. Tool definition
2. Template pro každý formát
3. UI pro stažení/kopírování

**Náročnost:** Nízká – "low-hanging fruit" pro wow efekt

---

### Gamifikace ❌

**Charter:**
- Postupné odemykání možností
- Výzvy / experimenty
- Vizualizace pokroku v porozumění strategiím

**Stav:** Frontend je čistě funkční chat

**Potřebná práce:**
- User accounts a autentizace
- Progress/achievement tracking v DB
- Achievement UI komponenty
- Design systému výzev

**Náročnost:** Vysoká (vyžaduje user management)

---

### Subscription / Billing ❌

**Charter:**
- Subscription SaaS model
- Cenové plány dle výpočetního objemu
- AI usage limity s možností dokoupení

**Stav:** Neimplementováno

**Potřebná práce:**
- User accounts
- Stripe/Paddle integrace
- Usage metering
- Plan management UI

**Náročnost:** Střední

---

## 4. Souhrnná matice

| Oblast | Status | Náročnost | Priorita |
|--------|--------|-----------|----------|
| AI jako kurátor poznání | ✅ Done | — | — |
| Workflow fáze | ✅ Done | — | — |
| Streaming UX | ✅ Done | — | — |
| Onboarding tutorial | 🟡 Skeleton | Střední | P1 |
| Export strategie | ❌ Chybí | Nízká | P1 |
| Paper trading | ❌ Chybí | Vysoká | P2 |
| Gamifikace | ❌ Chybí | Vysoká | P3 |
| Subscription/billing | ❌ Chybí | Střední | P2 |

---

## 5. Klíčová uvědomění

### Konzistence vize a implementace

Produktová vize a technická architektura jsou **konzistentní**. Charter nepopisuje sci-fi – popisuje roadmapu pro něco, co má solidní základ.

### Unikátní pozice na trhu

"Dospělý" tón charteru (anti-predátorský, research-first) odpovídá kvalitě implementace. Toto je vzácná kombinace v "AI trading" prostoru.

### Doporučený next step

1. **Export strategie** – rychlá win, vysoký wow efekt
2. **Tutorial mode** – leverage existujícího workflow
3. **User accounts** – prerequisite pro billing i gamifikaci

---

## Související dokumenty

- [[Product Charter – AI Trading Research Tool]]
- [[../01-Architecture/]] – technická architektura
- [[../02-Components/]] – komponenty systému
