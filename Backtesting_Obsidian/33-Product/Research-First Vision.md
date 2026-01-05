# Research-First Vision

> Filozofie produktu: od impulzu k pochopení

---

## Klíčový princip

> **Strategie je odpověď. Situace je otázka.**

Většina lidí se ptá *"jaká strategie funguje?"* – špatná otázka.

Správná otázka: *"V jaké situaci jsem a co v ní historicky fungovalo?"*

Tento nástroj učí uživatele **myslet v situacích**, ne v strategiích.

---

## Problém současného stavu

```
Uživatel: "Otestuj RSI strategii"
Tool: "Sharpe 1.2, drawdown 15%"
Uživatel: "...a co teď?"
```

Čísla bez kontextu = bezcenná informace.

Strategie bez situace je jako odpověď bez otázky.

---

## Konceptuální model: Research-First Trading

```
IMPULZ
│   Uživatel slyší v podcastu: "Po halvingu BTC vždy roste"
│   Vidí tweet, článek, graf s anotací
│   Má vlastní pozorování z tradingu
│
↓
TEZE
│   "Věřím, že post-halving období má specifické charakteristiky"
│   AI pomáhá formulovat: Co přesně tvrdíš? Za jakých podmínek?
│
↓
SITUACE
│   AI identifikuje doménu: timing, regime, volatilita
│   Formalizuje podmínky: 0-6M po halvingu, TREND_UP, klesající ATR
│   Najde historické výskyty: kdy tato situace nastala
│
↓
TESTOVÁNÍ
│   AI navrhne: "V této situaci historicky fungovalo X, Y, Z"
│   Backtest běží POUZE v definované situaci
│   Srovnání s baseline (celé období, buy & hold)
│
↓
POZNÁNÍ
│   "Ano, efekt existuje, ale pouze prvních 6M a při VIX < 20"
│   Teze validována/invalidována
│   Uživatel rozumí PROČ, ne jen CO
```

---

## Účel: AHA momenty, ne čísla

Produkt není kalkulačka na backtesty. Je to **nástroj pro budování intuice**.

**Cílový zážitek:**

Uživatel sleduje trading podcast. Slyší: *"RSI pod 30 je vždycky nákupní signál."*

Místo slepého přijetí nebo odmítnutí:
1. Otevře náš tool
2. Řekne AI: "Slyšel jsem, že RSI pod 30 = nákupní signál. Je to pravda?"
3. AI:
   - Rozpozná doménu (mean reversion, oversold conditions)
   - Zformuluje testovatelnou tezi
   - Ukáže historická data
   - **Challenguje**: "V silném downtrend RSI zůstává pod 30 týdny. Chceš vidět případy, kdy to NEVEDLO k rally?"
4. Uživatel odchází s **pochopením**, ne s odpovědí ano/ne

**Výsledek:** Algoritmické myšlení. Schopnost kriticky hodnotit trading tvrzení.

---

## AI Agent: Research Mode

### Současný agent
```
User: "Spusť backtest MA crossover"
Agent: [tool_call: run_backtest] → čísla
```

### Research Agent
```
User: "Slyšel jsem v podcastu, že Bitcoin má sezónní pattern v Q1"

Agent: 
1. Rozpozná doménu: timing/sezónnost
2. Formuluje tezi: "BTC má nadprůměrné výnosy v Q1"
3. Identifikuje situaci: leden-březen každého roku
4. Navrhne testování: průměrné Q1 výnosy vs ostatní kvartály
5. PTÁZKY: "Chceš zahrnout všechny roky, nebo jen post-2017?"
6. Spustí analýzu
7. Interpretuje: "Efekt existuje, ale je statisticky slabý (p=0.12)"
8. Závěr: "Nelze spolehlivě použít jako edge"
```

### Sokratovský přístup

Agent není yes-man. Challenguje:

```
User: "RSI < 30 = nákupní signál, to je jasné"

Agent: "Pojďme to prozkoumat:
        
1. V silném downtrend může RSI zůstat pod 30 týdny
   → Jak definuješ, kdy to NENÍ nákupní signál?

2. Funguje to stejně pro BTC vs altcoiny?
   → Altcoiny mohou jít na 0

3. Jaký je tvůj exit?
   → RSI > 70, fixed target, nebo trailing stop?

4. Timeframe?
   → Daily RSI vs 4h RSI = úplně jiné signály

Chceš, abych ti ukázal historické případy,
kdy RSI < 30 NEVEDLO k rally?"
```

---

## Příklady tezí a jejich zpracování

### Příklad 1: Bitcoin Halving Effect

**Impulz:** Podcast/článek o halvingu

**Teze:** "Po halvingu BTC historicky roste 12-18 měsíců"

**AI rozpozná:**
- Doména: Timing, supply shock, cyklus
- Prvky: halving date, post-halving období, cenová akce

**Situace:**
```
Název: Post-halving accumulation
Podmínky:
├── Timing: 0-180 dní po halvingu
├── Regime: TREND_UP nebo NEUTRAL  
└── Volatilita: klesající
Historické výskyty: 2012-11, 2016-07, 2020-05
```

**Test:** Momentum strategie pouze v těchto obdobích vs celé období

**Poznání:** "Efekt je reálný, ale první 2 měsíce jsou choppy. Lepší vstupovat 60+ dní po halvingu."

---

### Příklad 2: Mean Reversion po VIX Spike

**Impulz:** Tweet od tradera

**Teze:** "Když VIX vyskočí nad 30, BTC se vrátí do 2 týdnů"

**AI rozpozná:**
- Doména: Mean reversion, volatilita, sentiment
- Prvky: VIX, drawdown, recovery time

**Situace:**
```
Název: VIX panic spike
Podmínky:
├── VIX > 30
├── BTC drawdown > 10% za 7 dní
└── Regime: TREND_DOWN nebo CHOPPY
Historické výskyty: 2020-03, 2022-05, 2022-11...
```

**Test:** Long entry při VIX > 30, exit po 14 dnech nebo +15%

**Poznání:** "Funguje v 5 z 7 případů, ale 2 failures byly -30%. Potřebuje stop-loss."

---

### Příklad 3: Weekend Effect

**Impulz:** Vlastní pozorování

**Teze:** "O víkendech je menší likvidita a větší volatilita"

**AI rozpozná:**
- Doména: Timing, likvidita, mikrostruktura
- Prvky: den v týdnu, spread, volume

**Situace:**
```
Název: Weekend low liquidity
Podmínky:
├── Den: sobota, neděle
├── Volume: < 50% průměru
└── Spread: > 150% průměru
```

**Test:** Porovnání volatility weekend vs weekday

**Poznání:** "Volatilita je 1.3x vyšší, ale není konzistentně směrová. Není edge pro directional trading."

---

## UI: Research Workspace (vize)

```
┌─────────────────────────────────────────────────────────────────┐
│  📚 Research Workspace                                          │
├──────────────────────┬──────────────────────────────────────────┤
│                      │                                          │
│  TEZE                │  AKTIVNÍ VÝZKUM                          │
│  ─────               │  ────────────────                        │
│  ○ Post-halving      │                                          │
│    momentum          │  "Slyšel jsem, že RSI pod 30 je vždy     │
│  ● RSI oversold      │   nákupní signál"                        │
│    [testing]         │                                          │
│  ✓ Q1 sezónnost      │  ┌─────────────────────────────────────┐ │
│    [invalidated]     │  │ AI rozpoznává:                      │ │
│                      │  │ • Doména: Mean reversion            │ │
│  + Nová myšlenka     │  │ • Indikátor: RSI(14)                │ │
│                      │  │ • Podmínka: < 30                    │ │
│                      │  │ • Očekávání: Cenový růst            │ │
│  ZDROJE              │  └─────────────────────────────────────┘ │
│  ─────               │                                          │
│  [URL]  [Text]       │  Navrhovaná situace:                     │
│  [Screenshot]        │  RSI < 30 na daily, ne v TREND_DOWN      │
│  [Voice note?]       │                                          │
│                      │  ┌─────────────────────────────────────┐ │
│                      │  │ 💬 Agent                            │ │
│                      │  │                                     │ │
│                      │  │ Našel jsem 45 případů RSI < 30.     │ │
│                      │  │ V 28 následovala rally > 10%.       │ │
│                      │  │ Ale v 8 případech pokles pokračoval.│ │
│                      │  │                                     │ │
│                      │  │ Zajímavé: Všech 8 failures bylo     │ │
│                      │  │ během TREND_DOWN regime.            │ │
│                      │  │                                     │ │
│                      │  │ Chceš otestovat RSI strategii       │ │
│                      │  │ S regime filtrem?                   │ │
│                      │  └─────────────────────────────────────┘ │
│                      │                                          │
└──────────────────────┴──────────────────────────────────────────┘
```

---

## Zachycení impulzu (ne "import")

Nejde o technický import souboru. Jde o **zachycení momentu inspirace**.

### Z podcastu/YouTube
Uživatel slyší zajímavou myšlenku → otevře tool → napíše/nahraje co slyšel → AI převede na testovatelnou tezi

### Z Twitteru/článku
Uživatel vidí bold claim → vloží URL → AI extrahuje tvrzení → kriticky zhodnotí testovatelnost

### Z vlastního tradingu
Uživatel má pocit "tohle funguje" → popíše to → AI pomůže formalizovat → test potvrdí nebo vyvrátí

**Cíl:** Každý impulz může vést k poznání. Žádná myšlenka není ztracena.

---

## Proč to funguje pro různé persony

### Začátečník
"Slyšel jsem, že..." → Tool ho provede procesem → Naučí se kriticky myslet

### Pokročilý trader  
Má intuici z tradingu → Tool pomůže formalizovat → Validuje nebo vyvrací

### Content creator (YouTuber)
Chce ukázat divákům → Tool poskytuje "receipts" → Credibilita

### Quant/Analytik
Potřebuje rychle testovat hypotézy → Tool zrychluje research → Produktivita

---

## Vazba na Product Charter

Charter říká:
> "AI interpretuje výsledky v kontextu uživatelova záměru"

Research-First Vision definuje **jak**:
- Záměr = teze (co uživatel věří/zkoumá)
- Kontext = situace (za jakých podmínek)
- Interpretace = poznání (co to znamená pro rozhodování)

---

## Severní hvězda

> **Z každého impulzu k pochopení. Z každé myšlenky k testovatelné tezi. Z každé situace k informovanému rozhodnutí.**

