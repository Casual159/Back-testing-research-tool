# Research Layer – User Stories

> Definice uživatelských příběhů pro research-first přístup

**Předpoklad:** Přečti [[Research-First Vision]] pro filozofii a principy.

---

## Klíčový princip (opakování)

> **Strategie je odpověď. Situace je otázka. Teze je důvod, proč se ptáme.**

---

## Epic 1: Od impulzu k tezi

### Záměr epicu

Uživatel sleduje podcast, čte Twitter, vidí graf. Slyší nebo vidí něco zajímavého. Chce to **vyzkoušet, otestovat, pochopit**.

Cílem je **zachytit moment inspirace** a proměnit ho v testovatelnou tezi. 1-3 věty od uživatele stačí – AI rozpozná doménu, identifikuje prvky, a provede uživatele procesem.

**Výstup:** AHA momenty, pochopení, inspirace k algoritmickému myšlení.

---

### US-R01: Zachycení myšlenky

**Jako** uživatel
**chci** napsat myšlenku, kterou jsem někde slyšel nebo sám mám
**abych** mohl zjistit, jestli je pravdivá a za jakých podmínek

**Acceptance criteria:**
- [ ] Mohu zadat 1-3 věty volného textu
- [ ] AI rozpozná doménu (timing, mean reversion, trend, volatilita...)
- [ ] AI identifikuje klíčové prvky (indikátory, podmínky, očekávání)
- [ ] AI formuluje strukturovanou tezi
- [ ] AI navrhne, jak tezi otestovat

**Příklad interakce:**
```
User: "Slyšel jsem v podcastu, že po halvingu Bitcoin
       vždycky roste 12 měsíců"

AI: "Zajímavá teze. Rozpoznávám:

     DOMÉNA: Timing, supply cycle, makro event

     PRVKY:
     ├── Event: Bitcoin halving (supply shock)
     ├── Období: 12 měsíců po eventu
     └── Očekávání: Nadprůměrný růst

     FORMALIZOVANÁ TEZE:
     'BTC vykazuje statisticky významný růst
      v období 0-12 měsíců po halvingu'

     TESTOVATELNÉ: ✅ Ano
     Máme 3 historické halvingy (2012, 2016, 2020)

     Chceš, abych:
     1. Ukázal výnosy v těchto obdobích?
     2. Porovnal s obdobími mimo halving?
     3. Navrhl situaci a strategii pro testování?"
```

---

### US-R02: Zachycení z URL

**Jako** uživatel
**chci** vložit odkaz na tweet/článek/video
**abych** mohl rychle ověřit tvrzení, které jsem viděl online

**Acceptance criteria:**
- [ ] Mohu vložit URL
- [ ] AI extrahuje klíčové tvrzení z obsahu
- [ ] AI zhodnotí testovatelnost
- [ ] AI navrhne, jak pokračovat

**Příklad:**
```
User: [vloží tweet URL]

AI: "Autor tvrdí: 'RSI pod 20 na daily = garantovaný
     bounce do týdne'

     Moje analýza:
     ├── Testovatelné: ✅ Ano
     ├── Ale 'garantovaný' je silné slovo
     └── Historicky můžeme ověřit success rate

     Chceš tuto tezi prozkoumat? Můžu ukázat,
     kolikrát to historicky fungovalo a kdy ne."
```

---

### US-R03: Zachycení z vizuálu

**Jako** uživatel
**chci** nahrát screenshot grafu nebo anotovaný obrázek
**abych** mohl prozkoumat pattern, který jsem viděl

**Acceptance criteria:**
- [ ] Mohu nahrát obrázek
- [ ] AI analyzuje vizuální obsah
- [ ] AI interpretuje pattern/anotace
- [ ] AI navrhne formalizaci jako tezi

---

## Epic 2: Od teze k situaci

### Záměr epicu

AI z teze **uvědomí, jaká doména se v ní odehrává**. Identifikuje prvky, podmínky, kontext. Formalizuje je do **situace** – konkrétních, testovatelných podmínek.

Situace = odpověď na otázku "kdy přesně by toto mělo platit?"

---

### US-R04: AI extrakce situace z teze

**Jako** uživatel
**chci** aby AI navrhla situaci na základě mé teze
**abych** měl jasně definovaný kontext pro testování

**Acceptance criteria:**
- [ ] AI navrhne podmínky situace (regime, timing, volatilita, makro...)
- [ ] AI identifikuje historická období, kdy situace nastala
- [ ] Mohu podmínky upravit
- [ ] Vidím statistiky výskytů

**Příklad:**
```
TEZE: "Post-halving momentum efekt"

AI: "Z teze odvozuji situaci:

     SITUACE: Post-halving accumulation
     ─────────────────────────────────
     Podmínky:
     ├── Timing: 0-180 dní po halvingu
     ├── Regime: Není TREND_DOWN
     └── Volatilita: ATR klesá (konsolidace)

     Historické výskyty (3):
     ├── 2012-11-28 → 2013-05-28
     ├── 2016-07-09 → 2017-01-09
     └── 2020-05-11 → 2020-11-11

     Celkem 540 dní dat pro testování.

     Souhlasíš s touto definicí, nebo chceš upravit?"
```

---

### US-R05: Knihovna situací

**Jako** uživatel
**chci** mít přehled všech definovaných situací
**abych** je mohl znovu použít a kombinovat

**Acceptance criteria:**
- [ ] Seznam situací s názvem a stručným popisem
- [ ] Počet historických výskytů
- [ ] Quick action: "Testuj v této situaci"
- [ ] Možnost kombinovat situace (AND/OR)

---

## Epic 3: Od situace ke strategii

### Záměr epicu

Když je situace definovaná, AI navrhne **co by v ní mohlo fungovat**. Ne generická strategie, ale strategie vhodná pro daný kontext.

---

### US-R06: AI návrh strategie pro situaci

**Jako** uživatel
**chci** aby AI navrhla vhodnou strategii pro mou situaci
**abych** nemusel hádat

**Acceptance criteria:**
- [ ] AI analyzuje charakteristiky situace
- [ ] Navrhne 2-3 strategie s vysvětlením PROČ
- [ ] Vysvětlí trade-offy
- [ ] Mohu vybrat a okamžitě testovat

**Příklad:**
```
SITUACE: Post-halving accumulation

AI: "Pro tuto situaci navrhuji:

     1. MOMENTUM BREAKOUT (doporučeno)
        Proč: Historicky silné trendy po akumulaci
        Entry: Close > 20-day high
        Exit: Trailing stop 10%

     2. MA CROSSOVER (alternativa)
        Proč: Klasický trend-following
        Nižší výnosy, ale konzistentnější

     3. BUY & HOLD (baseline)
        Pro srovnání

     Kterou otestovat? Nebo všechny pro srovnání?"
```

---

### US-R07: Backtest omezený na situaci

**Jako** uživatel
**chci** spustit backtest POUZE v obdobích definované situace
**abych** viděl, jak strategie funguje v konkrétním kontextu

**Acceptance criteria:**
- [ ] Backtest běží pouze v identifikovaných obdobích
- [ ] Jasně vidím, která období byla zahrnuta
- [ ] Srovnání s "celé období" backtestem
- [ ] AI interpretuje rozdíl

**Příklad výstupu:**
```
VÝSLEDKY: Momentum Breakout

V situaci "Post-halving accumulation" (540 dní):
├── Return: +156%
├── Sharpe: 2.8
├── Max DD: -12%
└── Win Rate: 78%

Celé období 2012-2024:
├── Return: +45%
├── Sharpe: 0.9
├── Max DD: -35%
└── Win Rate: 52%

AI: "Strategie funguje 3.5x lépe v definované situaci.
     Mimo ni má průměrné výsledky s vyšším rizikem.

     POZNÁNÍ: Tuto strategii má smysl používat
     pouze když identifikuješ post-halving fázi."
```

---

## Epic 4: Poznání a validace

### Záměr epicu

Každý výzkum končí **poznáním**. Teze je validována nebo invalidována. Uživatel rozumí nejen CO, ale PROČ.

---

### US-R08: Označení teze jako validované/invalidované

**Jako** uživatel
**chci** po testování uzavřít tezi se závěrem
**abych** měl přehled o tom, co jsem se naučil

**Acceptance criteria:**
- [ ] Mohu označit stav: validated / invalidated / inconclusive
- [ ] AI navrhne závěr na základě výsledků
- [ ] Přidám vlastní poznámky
- [ ] Teze zůstává v historii

---

### US-R09: Knowledge base

**Jako** uživatel
**chci** mít přehled všech svých zjištění
**abych** viděl, co jsem se naučil a mohl na tom stavět

**Acceptance criteria:**
- [ ] Dashboard s tezemi a jejich stavy
- [ ] Filtrování a hledání
- [ ] AI může odkazovat na předchozí zjištění
- [ ] Export (markdown, PDF)

---

## Epic 5: AI jako průvodce

### Záměr epicu

AI není jen executor příkazů. Je to **průvodce procesem zkoumání**. Ptá se, challenguje, navrhuje, učí.

---

### US-R10: Sokratovský dialog

**Jako** uživatel
**chci** aby AI kladla otázky a challengovala mé předpoklady
**abych** se vyhnul confirmation bias

**Acceptance criteria:**
- [ ] AI se ptá "proč si myslíš, že...?"
- [ ] AI upozorňuje na edge cases a rizika
- [ ] AI ukazuje protiargumenty
- [ ] Mohu požádat o "přísný" vs "supportive" mode

**Příklad:**
```
User: "RSI pod 30 = buy, to je jasné"

AI: "Moment. Pojďme to prozkoumat:

     1. V silném downtrend RSI zůstává pod 30 týdny
        → Jak poznáš, kdy to NENÍ signál?

     2. BTC vs altcoiny - funguje to stejně?
        → Altcoiny můžou jít na nulu

     3. Jaký je tvůj exit? RSI > 70? Fixed target?

     4. Timeframe? Daily RSI ≠ 4h RSI

     Chceš vidět případy, kdy RSI < 30 nevedlo k rally?"
```

---

### US-R11: Proaktivní návrhy

**Jako** uživatel
**chci** aby AI sama navrhovala zajímavé otázky
**abych** objevil věci, na které bych nepřišel

**Acceptance criteria:**
- [ ] AI navrhuje teze na základě aktuálního trhu
- [ ] AI identifikuje anomálie v datech
- [ ] Návrhy jsou volitelné, ne vtíravé

---

## Prioritizace

| Story | Popis | Priorita |
|-------|-------|----------|
| US-R01 | Zachycení myšlenky → teze | **P0** |
| US-R04 | AI extrakce situace | **P0** |
| US-R06 | AI návrh strategie pro situaci | **P0** |
| US-R07 | Backtest v situaci | **P0** |
| US-R10 | Sokratovský dialog | **P1** |
| US-R02 | Zachycení z URL | P1 |
| US-R08 | Validace teze | P1 |
| US-R05 | Knihovna situací | P2 |
| US-R09 | Knowledge base | P2 |
| US-R03 | Zachycení z vizuálu | P2 |
| US-R11 | Proaktivní návrhy | P3 |

---

## Implementační poznámky

### Bezpečnost multimodálních vstupů

US-R02 (URL) a US-R03 (obrázky) přinášejí potenciální bezpečnostní rizika:

- **Prompt injection** – útočník může do webové stránky nebo obrázku vložit text, který AI interpretuje jako instrukci
- **Indirect injection** – skrytý text v PDF nebo screenshotu (bílá na bílé, atd.)

**Pragmatické zhodnocení:** Pro tento use-case je riziko nízké:
- Uživatel aktivně vkládá obsah, který chce analyzovat → není to automatické zpracování
- Nejhorší outcome = špatná analýza, ne kompromitace systému
- AI nemá přístup k citlivým datům ani destruktivním akcím

**Mitigace (až bude relevantní):**
- Zobrazit uživateli co AI "viděla" před další akcí
- Neautomatizovat nic destruktivního na základě externího vstupu

---

### Situace ≠ Market Regime

Současná implementace má `regime_filter` (TREND_UP, RANGE, atd.), ale to je jen **jedna dimenze** situace. Reálná situace může zahrnovat:

- Timing event (halving, FOMC, earnings)
- Technická formace (breakout, divergence)
- Cross-asset vztah (BTC dominance, DXY korelace)
- Volatility conditions
- Kombinace výše

**Přístup:** Schema follows usage, ne naopak.

1. Nechat AI navrhovat situace volně (ne předdefinovaná struktura)
2. Perzistovat je jako flexibilní JSON
3. Sledovat vzory v tom, co lidi reálně testují
4. Teprve pak formalizovat taxonomii

Lepší definice vzniknou z praxe – až něco postavíme a otestujeme.

---

### Rozšíření existujícího agenta

Většina P0 stories je **rozšířením existujícího agenta**:

| Story | Existující základ |
|-------|-------------------|
| Zachycení myšlenky | Chat interface, STRATEGY_DESIGN fáze |
| Extrakce situace | Regime detection, market_regimes tabulka |
| Návrh strategie | Regime-aware doporučení v promptech |
| Backtest v situaci | `regime_filter` parametr v run_backtest |

**Hlavní práce:**
1. Rozšíření system promptu pro research mode
2. Persistence tezí a situací (nové DB tabulky)
3. UI pro research workspace

---

## Související dokumenty

- [[Research-First Vision]] – filozofie a principy
- [[Product Charter – AI Trading Research Tool]] – produktový rámec
- [[Product-Implementation Gap Analysis]] – co je hotovo
