# Strategy Domain - Design Notes

## Current State (Lidl varianta)

Strategie jsou definované na dvou místech:
- `core/backtest/strategies/` - implementace (MovingAverageCrossover, RSIReversal, MACDCross, BollingerBands)
- `api/main.py:690` - STRATEGY_CLASSES slovník v backtest endpointu

Validace při vytváření strategie v DB chybí - lze vytvořit strategii s neexistující třídou.

## Budoucí požadavky

1. **Composite Strategies** - strategie definované LogicTree (entry_logic, exit_logic)
2. **Stop Loss / Take Profit** komponenty
3. **Custom conditions** - price_above_ma, volume_spike, rsi_overbought, etc.
4. **Validace** - při vytváření strategie ověřit, že class_name existuje

## Návrh: Strategy Registry

```
core/backtest/strategies/
├── registry.py          # Centrální registr - single source of truth
├── base.py              # Base Strategy class
├── ma_crossover.py
├── rsi_reversal.py
├── macd_cross.py
├── bollinger_bands.py
├── composite.py         # CompositeStrategy s LogicTree
└── components/
    ├── stop_loss.py     # TrailingStop, FixedStop, ATRStop
    ├── take_profit.py   # FixedTP, RiskRewardTP
    └── conditions.py    # Reusable conditions pro LogicTree
```

### registry.py

```python
class StrategyRegistry:
    """Single source of truth for strategy domain."""

    # Builtin strategy classes
    BUILTIN_CLASSES = {
        'MovingAverageCrossover': MovingAverageCrossover,
        'RSIReversal': RSIReversal,
        'MACDCross': MACDCross,
        'BollingerBands': BollingerBands,
    }

    # Available components for composite strategies
    STOP_LOSS_TYPES = ['fixed', 'trailing', 'atr']
    TAKE_PROFIT_TYPES = ['fixed', 'risk_reward']

    # Available conditions for LogicTree
    CONDITIONS = {
        'price_above_ma': PriceAboveMA,
        'rsi_overbought': RSIOverbought,
        'volume_spike': VolumeSpike,
        # ...
    }

    @classmethod
    def get_class(cls, name: str) -> type:
        if name not in cls.BUILTIN_CLASSES:
            raise ValueError(f"Unknown strategy: {name}. Available: {list(cls.BUILTIN_CLASSES.keys())}")
        return cls.BUILTIN_CLASSES[name]

    @classmethod
    def validate_class_name(cls, name: str) -> bool:
        return name in cls.BUILTIN_CLASSES or name == 'CompositeStrategy'

    @classmethod
    def list_available(cls) -> list[str]:
        return list(cls.BUILTIN_CLASSES.keys())
```

### Použití v API

```python
# api/main.py

from core.backtest.strategies.registry import StrategyRegistry

# V create_strategy endpoint - validace
if request.builtin_class:
    if not StrategyRegistry.validate_class_name(request.builtin_class):
        raise HTTPException(400, f"Invalid class: {request.builtin_class}")

# V backtest endpoint - instantiation
strategy_class = StrategyRegistry.get_class(class_name)
strategy = strategy_class(**params)
```

## Priorita

Nízká - aktuální Lidl varianta funguje pro agenta. Udělat až při:
- Implementaci composite strategies
- Přidání stop-loss/take-profit komponent
- Když začne být STRATEGY_CLASSES slovník duplikovaný na více místech

## Related Files

- [api/main.py](../api/main.py) - backtest endpoint, create_strategy endpoint
- [core/backtest/strategies/__init__.py](../core/backtest/strategies/__init__.py) - exporty
- [migrations/002_add_strategies.sql](../migrations/002_add_strategies.sql) - DB schema
