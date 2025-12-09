# Strategy Landscape

> Reference dokument mapující dimenze a přístupy k trading strategiím

## Dimenze reprezentace strategie

```
┌─────────────────────────────────────────────────────────────────────┐
│  STRATEGIE - DIMENZE PRO REPREZENTACI                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  A) FILOZOFIE (škola myšlení)                                       │
│  ├── Trend-following: "The trend is your friend"                   │
│  ├── Mean-reversion: "What goes up must come down"                 │
│  ├── Momentum: "Winners keep winning"                              │
│  ├── Statistical arbitrage: "Exploit inefficiencies"              │
│  └── Market-making: "Capture the spread"                          │
│                                                                     │
│  B) INDIKÁTORY (building blocks)                                    │
│  ├── Price-based: MA, BB, Support/Resistance                       │
│  ├── Momentum: RSI, MACD, Stochastic                               │
│  ├── Volume: OBV, VWAP, Volume Profile                             │
│  └── Volatility: ATR, VIX, Bollinger Width                         │
│                                                                     │
│  C) PODMÍNKY (logika)                                               │
│  ├── Entry: IF (RSI < 30) AND (price > SMA200) → BUY               │
│  ├── Exit: IF (RSI > 70) OR (trailing_stop hit) → SELL            │
│  └── Filter: IF (regime = CHOPPY) → SKIP                           │
│                                                                     │
│  D) KONTEXT (kdy použít)                                            │
│  ├── Market Regime: TREND_UP, RANGE, CHOPPY...                     │
│  ├── Timeframe: Scalping (1m) vs Swing (4h) vs Position (1d)       │
│  └── Asset class: Crypto volatility ≠ Forex ≠ Stocks               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## A) Filozofie - Školy myšlení

### Trend-following
- **Princip**: Trh má tendenci pokračovat v trendu
- **Indikátory**: MA crossover, breakouty, higher highs/lows
- **Vhodné regime**: TREND_UP, TREND_DOWN
- **Slabiny**: Whipsaw v RANGE/CHOPPY

### Mean-reversion
- **Princip**: Cena se vrací k průměru
- **Indikátory**: RSI extremes, Bollinger Bands, distance from MA
- **Vhodné regime**: RANGE
- **Slabiny**: Catching falling knife v silném trendu

### Momentum
- **Princip**: Síla pohybu indikuje pokračování
- **Indikátory**: MACD, ROC, RSI divergence
- **Vhodné regime**: TREND_UP, TREND_DOWN (potvrzení)
- **Slabiny**: Pozdní vstupy, obraty

### Statistical Arbitrage
- **Princip**: Exploatace statistických neefektivit
- **Metody**: Pairs trading, mean-reversion portfolia
- **Náročnost**: Vysoká (vyžaduje statistické modelování)

### Market-making
- **Princip**: Profit ze spreadu mezi bid/ask
- **Náročnost**: Velmi vysoká (latence, kapitál)
- **Mimo scope**: Retail backtesting

---

## B) Indikátory - Building Blocks

### Price-based
| Indikátor | Popis | Použití |
|-----------|-------|---------|
| SMA/EMA | Klouzavé průměry | Trend direction, support/resistance |
| Bollinger Bands | Volatility envelope | Mean-reversion, breakout |
| Support/Resistance | Price levels | Entry/exit zones |
| Pivot Points | Calculated levels | Intraday targets |

### Momentum
| Indikátor | Popis | Použití |
|-----------|-------|---------|
| RSI | Relative Strength Index | Overbought/oversold |
| MACD | Moving Average Convergence | Trend momentum |
| Stochastic | Price position in range | Reversal signals |
| ROC | Rate of Change | Momentum speed |

### Volume
| Indikátor | Popis | Použití |
|-----------|-------|---------|
| OBV | On-Balance Volume | Volume trend |
| VWAP | Volume Weighted Avg Price | Fair value |
| Volume Profile | Volume at price levels | Support/resistance |

### Volatility
| Indikátor | Popis | Použití |
|-----------|-------|---------|
| ATR | Average True Range | Stop placement, position sizing |
| BB Width | Bollinger Band width | Volatility regime |
| Historical Vol | Std dev of returns | Risk assessment |

---

## C) Podmínky - Logika strategie

### Entry Logic
```python
# Příklad: Trend-following s momentum potvrzením
entry_conditions = {
    "primary": "price > SMA(200)",           # Trend filter
    "trigger": "SMA(20) cross_above SMA(50)", # Entry signal
    "confirm": "RSI(14) > 50",                # Momentum confirm
    "regime": ["TREND_UP"]                    # Context filter
}
```

### Exit Logic
```python
exit_conditions = {
    "take_profit": "price >= entry * 1.05",   # 5% target
    "stop_loss": "price <= entry * 0.98",     # 2% stop
    "trailing": "price <= highest - ATR*2",   # Trailing stop
    "signal": "SMA(20) cross_below SMA(50)"   # Signal exit
}
```

### Filter Logic
```python
skip_conditions = {
    "regime": ["CHOPPY"],              # Avoid choppy markets
    "volatility": "ATR > threshold",   # Too volatile
    "time": "not in trading_hours"     # Session filter
}
```

---

## D) Kontext - Kdy použít strategii

### Market Regime Matrix
| Regime | Trend-following | Mean-reversion | Momentum |
|--------|-----------------|----------------|----------|
| TREND_UP | Optimal | Risky | Good |
| TREND_DOWN | Optimal (short) | Risky | Good |
| RANGE | Poor | Optimal | Poor |
| CHOPPY | Avoid | Risky | Avoid |

### Timeframe Mapping
| Style | Timeframe | Hold period | Strategy type |
|-------|-----------|-------------|---------------|
| Scalping | 1m-5m | Minutes | Mean-reversion, momentum |
| Day trading | 15m-1h | Hours | Trend + momentum |
| Swing | 4h-1d | Days | Trend-following |
| Position | 1d-1w | Weeks/months | Trend + fundamentals |

---

## Implementace v projektu

### Dostupné strategie
- `MovingAverageCrossover` - trend-following
- `RSIReversal` - mean-reversion
- `BollingerBands` - volatility-based
- `MACDCross` - momentum

### Composition Framework
```python
from core.backtest.strategies.composition import (
    CompositeStrategy,
    IndicatorSignal,
    LogicTree,
    Condition
)

# Lze skládat libovolné kombinace
entry = LogicTree.AND([
    IndicatorSignal("RSI", {"period": 14}, Condition("<", 30)),
    IndicatorSignal("MACD", {...}, Condition("cross_above", 0))
])
```

---

## Další rozvoj

- [ ] Risk management integrace (stop loss, trailing, OCO)
- [ ] Regime-based strategy switching
- [ ] Strategy portfolio (multi-strategy)
- [ ] Strategy Lab UI

---

*Vytvořeno: 2025-01-09*
*Souvisí s: [[Market Regime Classification]], [[Backtest Engine]]*
