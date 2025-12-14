# Claude Direct Test - Backtesting MCP Server

**Datum:** 2024-12-10
**Účel:** Kompletní test všech nástrojů backtesting MCP serveru

---

## 1. get_data_stats - Statistiky dostupných dat

**Účel:** Zjistit jaká historická data jsou k dispozici pro backtesting.

### Výsledek ✅

| Symbol | Timeframe | Počet svíček | Od | Do |
|--------|-----------|--------------|----|----|
| ADAUSDT | 1h | 8,761 | 2024-01-01 | 2024-12-31 |
| ATOMUSDC | 1h | 8,161 | 2025-01-01 | 2025-12-07 |
| BTCUSDT | 1h | 8,761 | 2024-01-01 | 2024-12-31 |
| DOGEUSDC | 4h | 2,035 | 2025-01-01 | 2025-12-06 |

---

## 2. list_strategies - Seznam strategií

**Účel:** Získat seznam všech dostupných obchodních strategií.

### Výsledek ✅

| Název | Typ | Parametry | Filtr režimu |
|-------|-----|-----------|--------------|
| MA Crossover 10/30 Fast | MovingAverageCrossover | EMA, fast=10, slow=30 | TREND_UP, TREND_DOWN |
| MA Crossover 20/50 | MovingAverageCrossover | fast=20, slow=50 | TREND_UP, TREND_DOWN |

---

## 3. get_strategy - Detail strategie

**Účel:** Získat detailní informace o konkrétní strategii.

### Výsledek ✅ (opraveno 2024-12-10)

**Původní problém:** 404 - lomítko v názvu (`MA Crossover 20/50`) rozbíjelo URL routing.

**Fix:** `{name}` → `{name:path}` v API + URL enkódování v MCP serveru.

---

## 4. check_data - Kontrola dostupnosti dat

**Účel:** Ověřit, zda jsou data dostupná pro konkrétní symbol a období před spuštěním backtestu.

### Výsledek ✅

| Parametr | Hodnota |
|----------|---------|
| Symbol | BTCUSDT |
| Timeframe | 1h |
| Požadované období | 2024-03-01 → 2024-06-30 |
| Dostupná data | 2024-01-01 → 2024-12-31 |
| **Dostupnost** | ✅ Data jsou k dispozici |

---

## 5. get_market_regime - Aktuální tržní režim

**Účel:** Zjistit aktuální klasifikaci tržního režimu pro rozhodnutí, jakou strategii použít.

### Výsledek ✅

**Aktuální režim (BTCUSDT 1h):**

| Vlastnost | Hodnota |
|-----------|---------|
| Režim | **TREND_DOWN** 🔴 |
| Plná klasifikace | DOWNTREND_HIGHVOL_BEARISHMOM |
| Trend | Downtrend |
| Volatilita | High |
| Momentum | Bearish |
| Confidence | 85% |

**Posledních 10 hodin:**
```
TREND_DOWN → TREND_DOWN → NEUTRAL → NEUTRAL → NEUTRAL → NEUTRAL → TREND_DOWN → TREND_DOWN → TREND_DOWN → TREND_DOWN
```

---

## 6. create_strategy - Vytvoření nové strategie

**Účel:** Vytvořit vlastní strategii s custom parametry.

### Výsledek ✅

| Parametr | Hodnota |
|----------|---------|
| Úspěch | ✅ Ano |
| ID strategie | 3 |
| Název | RSI Test Strategy |
| Třída | RSIReversal |
| Popis | Testovací RSI strategie pro mean-reversion v ranging trzích |
| Parametry | rsi_period: 14, oversold: 30, overbought: 70 |
| Filtr režimu | RANGE |

---

## 7. run_backtest - Spuštění backtestu

**Účel:** Provést backtest strategie na historických datech a získat metriky výkonnosti.

### Konfigurace

- Strategie: MA Crossover 20/50
- Symbol: BTCUSDT
- Timeframe: 1h
- Období: 2024-03-01 → 2024-09-30
- Počáteční kapitál: $10,000

### Výsledek ✅

**Metriky výkonnosti:**

| Metrika | Hodnota | Hodnocení |
|---------|---------|-----------|
| Celkový výnos | **-15.23%** | 🔴 Ztráta |
| Sharpe Ratio | -0.11 | 🔴 Špatný (< 1.0) |
| Max Drawdown | -31.74% | 🔴 Vysoké riziko |
| Win Rate | 36.67% | 🟡 Pod 50% |
| Počet obchodů | 60 | Aktivní |
| Profit Factor | 0.71 | 🔴 Pod 1.0 |

**Interpretace:** Strategie MA Crossover 20/50 podala špatný výkon v období březen-září 2024. Nízký win rate a profit factor pod 1 naznačují, že trh byl převážně v ranging/choppy podmínkách, které nejsou vhodné pro trend-following strategie.

---

# Souhrn testů

| # | Nástroj | Status | Popis |
|---|---------|--------|-------|
| 1 | `get_data_stats` | ✅ OK | Vrátil 4 datasety s metadaty |
| 2 | `list_strategies` | ✅ OK | Vrátil 2 existující strategie |
| 3 | `get_strategy` | ✅ OK | Opraveno - URL encoding fix |
| 4 | `check_data` | ✅ OK | Správně ověřil dostupnost dat |
| 5 | `get_market_regime` | ✅ OK | Vrátil aktuální režim + historii |
| 6 | `create_strategy` | ✅ OK | Úspěšně vytvořil RSI strategii (ID: 3) |
| 7 | `run_backtest` | ✅ OK | Spustil backtest s kompletními metrikami |

**Celkový výsledek: 7/7 nástrojů funguje správně (100%)**

---

## Závěr

Backtesting MCP server je plně funkční a připravený k použití.
