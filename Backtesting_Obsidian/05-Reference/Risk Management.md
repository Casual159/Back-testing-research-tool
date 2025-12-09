# Risk Management

> Reference dokument pro risk management v trading strategiích

## Dimenze Risk Managementu

```
┌─────────────────────────────────────────────────────────────────────┐
│  RISK MANAGEMENT - DIMENZE                                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  A) EXIT MANAGEMENT (ochrana pozice)                                │
│  ├── Stop Loss: Fixní % nebo ATR-based                             │
│  ├── Trailing Stop: Posouvá se s cenou                             │
│  ├── Take Profit: Fixní target                                     │
│  └── OCO (One-Cancels-Other): TP + SL jako pár                     │
│                                                                     │
│  B) POSITION SIZING (kolik riskovat)                                │
│  ├── Fixed %: Vždy 2% portfolia                                    │
│  ├── Kelly Criterion: Optimální sizing dle edge                    │
│  ├── Volatility-adjusted: Menší pozice při vysoké vol              │
│  └── Risk parity: Stejný risk na každý trade                       │
│                                                                     │
│  C) PORTFOLIO LEVEL (teorie her / game theory)                      │
│  ├── Diversifikace: Nekorelované strategie                         │
│  ├── Max Drawdown Limit: Stop trading při -20%                     │
│  ├── Correlation Management: Avoid concentrated bets               │
│  └── Anti-Martingale: Zvyšovat size při winning streak             │
│                                                                     │
│  D) EXECUTION (jak provést)                                         │
│  ├── Market order: Okamžitě, ale slippage                          │
│  ├── Limit order: Lepší cena, ale nemusí se vyplnit               │
│  ├── Bracket order: Entry + TP + SL najednou                       │
│  └── Iceberg: Rozdělit velké ordery                                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## A) Exit Management

### Stop Loss
Ochrana proti velkým ztrátám.

| Typ | Popis | Kdy použít |
|-----|-------|------------|
| Fixed % | Např. -2% od entry | Jednoduché, konzistentní |
| ATR-based | 2x ATR od entry | Adaptivní k volatilitě |
| Support-based | Pod support level | Technicky motivované |
| Time-based | Exit po X barech | Mean-reversion strategie |

```python
# ATR-based stop loss
stop_price = entry_price - (atr * 2.0)
```

### Trailing Stop
Posouvá se s cenou, chrání zisky.

```python
# Trailing stop logika
if current_price > highest_since_entry:
    highest_since_entry = current_price
    trailing_stop = highest_since_entry - (atr * 2.0)

if current_price <= trailing_stop:
    exit_position()
```

### Take Profit
Fixní target pro uzamčení zisku.

| Přístup | Popis |
|---------|-------|
| Fixed % | +5% od entry |
| Risk:Reward | 2:1 nebo 3:1 ratio |
| Resistance-based | Na dalším resistance |
| Partial | 50% na TP1, 50% trailing |

### OCO (One-Cancels-Other)
Binance order type - kombinuje TP a SL.

```python
# OCO order structure
oco_order = {
    "symbol": "BTCUSDT",
    "side": "SELL",
    "quantity": 0.1,
    "price": 45000,           # Take profit (limit)
    "stopPrice": 42000,       # Stop trigger
    "stopLimitPrice": 41900,  # Stop limit price
}
```

---

## B) Position Sizing

### Fixed Percentage
Nejjednodušší přístup.

```python
position_size = portfolio_value * 0.02  # 2% per trade
```

### Kelly Criterion
Matematicky optimální sizing dle edge.

```python
def kelly_fraction(win_rate: float, avg_win: float, avg_loss: float) -> float:
    """
    f* = (bp - q) / b
    f* = optimal fraction of capital
    b = odds (win/loss ratio)
    p = probability of win
    q = probability of loss (1-p)
    """
    b = avg_win / avg_loss  # payoff ratio
    p = win_rate
    q = 1 - p
    return (b * p - q) / b

# Příklad: 55% win rate, avg win = 1.5x avg loss
kelly = kelly_fraction(0.55, 1.5, 1.0)  # = 0.183 = 18.3%

# V praxi: half-Kelly pro bezpečnost
safe_kelly = kelly * 0.5  # = 9.15%
```

### Volatility-Adjusted
Menší pozice při vysoké volatilitě.

```python
def volatility_adjusted_size(
    base_size: float,
    current_atr: float,
    baseline_atr: float
) -> float:
    """Adjustuje size inverzně k volatilitě"""
    return base_size * (baseline_atr / current_atr)

# Příklad: Když ATR je 2x vyšší, size je 0.5x
```

### Risk Parity
Stejný risk (v $) na každý trade.

```python
def risk_parity_size(
    risk_per_trade: float,  # Např. $100
    entry_price: float,
    stop_price: float
) -> float:
    """Počet jednotek pro fixní $ risk"""
    risk_per_unit = abs(entry_price - stop_price)
    return risk_per_trade / risk_per_unit

# Příklad: Risk $100, entry $50000, stop $49000
# units = 100 / 1000 = 0.1 BTC
```

---

## C) Portfolio Level (Game Theory)

### Diversifikace
Kombinuj nekorelované strategie.

```python
portfolio_strategies = [
    ("TrendFollowing_BTC", correlation_group="trend"),
    ("MeanReversion_ETH", correlation_group="mean_rev"),
    ("Momentum_BNB", correlation_group="momentum"),
]

# Maximální alokace per correlation group
max_per_group = 0.30  # 30%
```

### Max Drawdown Limit
Circuit breaker pro portfolio.

```python
def check_drawdown_limit(
    current_value: float,
    peak_value: float,
    max_dd: float = 0.20
) -> bool:
    """Vrátí True pokud překročen DD limit"""
    current_dd = (peak_value - current_value) / peak_value
    return current_dd >= max_dd

# Akce při překročení:
# - Stop all trading
# - Reduce position sizes
# - Alert user
```

### Anti-Martingale (Pyramiding)
Zvyšuj expozici při winning streak.

```python
def anti_martingale_multiplier(consecutive_wins: int) -> float:
    """Zvyšuj size při výhrách, snižuj při prohrách"""
    if consecutive_wins >= 3:
        return 1.5
    elif consecutive_wins >= 2:
        return 1.25
    elif consecutive_wins <= -2:  # consecutive losses
        return 0.5
    return 1.0
```

---

## D) Execution

### Order Types

| Typ | Pros | Cons | Kdy použít |
|-----|------|------|------------|
| Market | Jistota vyplnění | Slippage | Rychlé exity, SL |
| Limit | Lepší cena | Může se nevyplnit | TP, plánované entry |
| Stop-Limit | Kontrola nad cenou | Gap risk | SL s limit |
| Bracket | Kompletní setup | Komplexnější | OCO scénáře |

### Slippage Modeling

```python
def estimate_slippage(
    order_size: float,
    avg_volume: float,
    volatility: float
) -> float:
    """Odhad slippage pro backtest"""
    size_impact = order_size / avg_volume * 0.1
    vol_impact = volatility * 0.5
    return size_impact + vol_impact

# Typicky 0.05% - 0.2% pro crypto
```

---

## Implementace v projektu

### Aktuální stav
```python
# BacktestEngine - základní podpora
BacktestEngine(
    commission_rate=0.001,   # ✅ Máme
    slippage_rate=0.0005,    # ✅ Máme
    position_size_pct=1.0,   # ✅ Máme (fixed %)
)
```

### Co přidat (MVP)
```python
@dataclass
class RiskConfig:
    # Exit management
    stop_loss_pct: Optional[float] = 0.02      # 2% SL
    take_profit_pct: Optional[float] = None    # Optional TP
    trailing_stop_atr: Optional[float] = 2.0   # ATR multiplier

    # Position sizing
    max_position_pct: float = 0.10             # Max 10% per trade
    risk_per_trade_pct: float = 0.02           # Risk 2% per trade

    # Portfolio level
    max_drawdown_pct: float = 0.20             # Stop at -20%
```

### Co přidat (Later)
- [ ] Kelly-based position sizing
- [ ] Correlation-aware portfolio allocation
- [ ] Multi-timeframe risk assessment
- [ ] Dynamic stop adjustment based on regime

---

## Vazba na Market Regime

| Regime | Stop Loss | Position Size | Trailing |
|--------|-----------|---------------|----------|
| TREND_UP | Wider (3x ATR) | Normal | Aggressive |
| TREND_DOWN | Wider (3x ATR) | Normal/Short | Aggressive |
| RANGE | Tight (1.5x ATR) | Normal | Tight |
| CHOPPY | Very tight | Reduced 50% | Very tight |
| NEUTRAL | Standard (2x ATR) | Normal | Standard |

```python
def regime_adjusted_risk(regime: str, base_config: RiskConfig) -> RiskConfig:
    """Adjustuje risk config dle market regime"""
    adjustments = {
        "TREND_UP": {"atr_mult": 1.5, "size_mult": 1.0},
        "CHOPPY": {"atr_mult": 0.75, "size_mult": 0.5},
        # ...
    }
    # Apply adjustments...
```

---

*Vytvořeno: 2025-01-09*
*Souvisí s: [[Strategy Landscape]], [[Market Regime Classification]]*
