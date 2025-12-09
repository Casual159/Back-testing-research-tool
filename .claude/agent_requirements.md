# Agent Requirements

> Co chceme od backtesting agenta

## Doménový model

```
Backtest = f(Strategy, Dataset)

Strategy musí EXISTOVAT před backtestem
Dataset musí EXISTOVAT před backtestem (candles v DB)
```

## Agent capabilities

### 1. List & Query
- **list_strategies** - zobrazit dostupné strategie
- **get_strategy** - detail konkrétní strategie
- **check_data** - ověřit dostupnost datasetu

### 2. Create
- **create_strategy** - vytvořit novou strategii
  - Entry logic (indikátory + podmínky)
  - Exit logic
  - Regime filter (optional)

### 3. Test
- **run_backtest** - spustit backtest
  - Vyžaduje existující strategii
  - Vyžaduje existující dataset
  - Vrací metriky + trades pro AI analýzu

### 4. Advise (domain knowledge)
Agent není jen API wrapper - má znalosti:
- Které strategie se hodí pro které market regime
- Jak kombinovat indikátory smysluplně
- Jak interpretovat výsledky backtestu

## Příklady interakcí

### Query
```
User: "Jaké strategie máš?"
Agent: [list_strategies] → "MA Crossover, RSI Reversal, BB, MACD"
```

### Backtest s validací
```
User: "Otestuj RSI na BTC za Q1 2024"
Agent:
  1. Ověří že strategie existuje
  2. Ověří že data existují
  3. Spustí backtest
  4. Interpretuje výsledky
```

### Strategy Advisor
```
User: "Navrhni strategii pro RANGE market"
Agent: (přemýšlí o domain knowledge)
  → "Pro RANGE doporučuji mean-reversion: RSI + BB..."
  → "Chceš vytvořit a otestovat?"
```

### Create + Test flow
```
User: "Vytvoř strategii s RSI < 30 a MACD cross up"
Agent:
  1. [create_strategy {...}]
  2. "Vytvořeno. Chceš otestovat?"
User: "Ano, na BTC 2024"
Agent:
  3. [run_backtest {...}]
  4. "Sharpe 1.2, Win Rate 58%..."
```

## Regime awareness

Strategy může mít `regime_filter`:
- Agregovaný: `["TREND_UP", "RANGE"]`
- Sub-regime: `{"trend": ["uptrend"], "volatility": ["low"]}`

Agent ví, které strategie se hodí pro které regime:
- TREND_UP/DOWN → trend-following (MA Cross, MACD)
- RANGE → mean-reversion (RSI, BB)
- CHOPPY → stay out nebo velmi konzervativní

## Backtest results pro AI

Agent dostane strukturovaná data pro analýzu:
```python
{
    "metrics": {
        "total_return_pct": 15.4,
        "sharpe_ratio": 1.2,
        "max_drawdown_pct": -8.5,
        "win_rate_pct": 58.0,
        "total_trades": 23,
        "profit_factor": 1.8
    },
    "trades": [...],  # Pro detailní analýzu
    "equity_curve": [...]  # Pro vizualizaci
}
```

Agent umí interpretovat:
- "Sharpe > 1 je dobré, > 2 výborné"
- "Win rate 58% s profit factor 1.8 = solidní edge"
- "Max DD -8.5% je přijatelné pro crypto"
