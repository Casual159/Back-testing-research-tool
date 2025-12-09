# Strategy Domain Implementation Plan

> Kompletní plán pro dokončení strategy aparátu včetně frontendu a agent tools

## Konceptuální model

```
┌─────────────────────────────────────────────────────────────────────┐
│  STRATEGY = Entry Logic + Exit Logic + Context (Regime Filter)     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  "Malá" strategie (implementace):                                   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  name: "RSI Mean Reversion"                                  │   │
│  │  entry_logic: RSI < 30 AND price > SMA(200)                 │   │
│  │  exit_logic: RSI > 70 OR trailing_stop_hit                  │   │
│  │  regime_filter: ["RANGE", "NEUTRAL"]                        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  "Velká" strategie (metodologie):                                   │
│  - Výběr správné "malé" strategie pro aktuální podmínky            │
│  - Portfolio strategií                                              │
│  - Risk management                                                  │
│  - Position sizing                                                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Fáze 1: Backend Core

### 1.1 Regime Filter v CompositeStrategy

**Soubor:** `core/backtest/strategies/composition/composite_strategy.py`

```python
class CompositeStrategy(Strategy):
    def __init__(
        self,
        name: str,
        entry_logic: LogicTree,
        exit_logic: LogicTree,
        description: str = "",
        regime_filter: Optional[List[str]] = None,  # NEW
        sub_regime_filter: Optional[Dict[str, List[str]]] = None  # NEW
    ):
        """
        Args:
            regime_filter: List of allowed simplified regimes
                          ["TREND_UP", "RANGE", "NEUTRAL"]
            sub_regime_filter: Filter by sub-regime components
                              {"trend": ["uptrend"], "volatility": ["low"]}
        """
        self.regime_filter = regime_filter
        self.sub_regime_filter = sub_regime_filter
        # ...

    def calculate_signals(self, market_event: MarketEvent) -> Optional[SignalEvent]:
        # Check regime filter first
        if not self._regime_allowed(market_event):
            return None  # Skip signal in disallowed regime

        # Continue with normal logic...

    def _regime_allowed(self, market_event: MarketEvent) -> bool:
        """Check if current market regime is allowed for this strategy"""
        regime_data = market_event.metadata.get('regime', {})

        # Check simplified regime filter
        if self.regime_filter:
            simplified = regime_data.get('simplified')
            if simplified not in self.regime_filter:
                return False

        # Check sub-regime filter
        if self.sub_regime_filter:
            for component, allowed_values in self.sub_regime_filter.items():
                current_value = regime_data.get(f'{component}_state')
                if current_value not in allowed_values:
                    return False

        return True
```

**Effort:** 30 min

---

### 1.2 Database Schema - strategies table

**Soubor:** `migrations/002_add_strategies.sql`

```sql
CREATE TABLE IF NOT EXISTS strategies (
    -- Primary key
    id SERIAL PRIMARY KEY,

    -- Basic info
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,

    -- Strategy type
    strategy_type VARCHAR(50) NOT NULL,  -- 'builtin' | 'composite' | 'custom'

    -- For builtin strategies: just store the class name
    builtin_class VARCHAR(50),  -- 'MovingAverageCrossover', 'RSIReversal', etc.

    -- For composite strategies: store the logic as JSON
    entry_logic JSONB,
    exit_logic JSONB,

    -- Parameters (for any strategy type)
    parameters JSONB DEFAULT '{}',

    -- Context filters
    regime_filter TEXT[],  -- ['TREND_UP', 'RANGE']
    sub_regime_filter JSONB,  -- {"trend": ["uptrend"], "volatility": ["low"]}

    -- Metadata
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_strategy_type CHECK (
        strategy_type IN ('builtin', 'composite', 'custom')
    ),
    CONSTRAINT builtin_has_class CHECK (
        strategy_type != 'builtin' OR builtin_class IS NOT NULL
    ),
    CONSTRAINT composite_has_logic CHECK (
        strategy_type != 'composite' OR (entry_logic IS NOT NULL AND exit_logic IS NOT NULL)
    )
);

-- Indexes
CREATE INDEX idx_strategies_name ON strategies(name);
CREATE INDEX idx_strategies_type ON strategies(strategy_type);
CREATE INDEX idx_strategies_active ON strategies(is_active) WHERE is_active = true;

-- Insert built-in strategies
INSERT INTO strategies (name, description, strategy_type, builtin_class, parameters) VALUES
('MA Crossover', 'Trend-following strategy using moving average crossovers', 'builtin', 'MovingAverageCrossover', '{"fast_period": 20, "slow_period": 50, "ma_type": "SMA"}'),
('RSI Reversal', 'Mean-reversion strategy using RSI overbought/oversold levels', 'builtin', 'RSIReversal', '{"rsi_period": 14, "oversold": 30, "overbought": 70}'),
('Bollinger Bands', 'Volatility-based mean-reversion using Bollinger Bands', 'builtin', 'BollingerBands', '{"period": 20, "num_std": 2.0}'),
('MACD Cross', 'Momentum strategy using MACD crossovers', 'builtin', 'MACDCross', '{"fast_period": 12, "slow_period": 26, "signal_period": 9}')
ON CONFLICT (name) DO NOTHING;
```

**Effort:** 30 min

---

### 1.3 Strategy Storage Layer

**Soubor:** `data/strategy_storage.py`

```python
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import json

@dataclass
class StrategyRecord:
    id: int
    name: str
    description: str
    strategy_type: str  # 'builtin' | 'composite' | 'custom'
    builtin_class: Optional[str]
    entry_logic: Optional[Dict]
    exit_logic: Optional[Dict]
    parameters: Dict[str, Any]
    regime_filter: Optional[List[str]]
    sub_regime_filter: Optional[Dict]
    is_active: bool
    created_at: str
    updated_at: str

class StrategyStorage:
    """CRUD operations for strategies table"""

    def __init__(self, connection_string: str):
        self.conn_string = connection_string

    async def list_strategies(self, active_only: bool = True) -> List[StrategyRecord]:
        """Get all strategies"""
        pass

    async def get_strategy(self, name: str) -> Optional[StrategyRecord]:
        """Get strategy by name"""
        pass

    async def create_strategy(self, strategy: StrategyRecord) -> StrategyRecord:
        """Create new strategy"""
        pass

    async def update_strategy(self, name: str, updates: Dict) -> StrategyRecord:
        """Update existing strategy"""
        pass

    async def delete_strategy(self, name: str) -> bool:
        """Soft delete strategy (set is_active=false)"""
        pass

    def instantiate_strategy(self, record: StrategyRecord):
        """Convert DB record to actual Strategy object"""
        if record.strategy_type == 'builtin':
            return self._instantiate_builtin(record)
        elif record.strategy_type == 'composite':
            return self._instantiate_composite(record)

    def _instantiate_builtin(self, record: StrategyRecord):
        """Create builtin strategy instance"""
        from core.backtest.strategies import (
            MovingAverageCrossover, RSIReversal,
            BollingerBands, MACDCross
        )

        class_map = {
            'MovingAverageCrossover': MovingAverageCrossover,
            'RSIReversal': RSIReversal,
            'BollingerBands': BollingerBands,
            'MACDCross': MACDCross,
        }

        cls = class_map[record.builtin_class]
        return cls(**record.parameters)

    def _instantiate_composite(self, record: StrategyRecord):
        """Create composite strategy from JSON logic"""
        from core.backtest.strategies.composition import (
            CompositeStrategy, LogicTree
        )

        entry_logic = LogicTree.from_dict(record.entry_logic)
        exit_logic = LogicTree.from_dict(record.exit_logic)

        return CompositeStrategy(
            name=record.name,
            entry_logic=entry_logic,
            exit_logic=exit_logic,
            description=record.description,
            regime_filter=record.regime_filter,
            sub_regime_filter=record.sub_regime_filter
        )
```

**Effort:** 1.5 h

---

### 1.4 Backtest Results Storage

**Soubor:** `migrations/003_add_backtest_results.sql`

```sql
CREATE TABLE IF NOT EXISTS backtest_results (
    id SERIAL PRIMARY KEY,

    -- Reference to strategy
    strategy_id INTEGER REFERENCES strategies(id),
    strategy_name VARCHAR(100) NOT NULL,  -- Denormalized for convenience

    -- Data context
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,

    -- Backtest config
    initial_capital DECIMAL(20, 2) NOT NULL,
    commission_rate DECIMAL(10, 6),
    slippage_rate DECIMAL(10, 6),
    position_size_pct DECIMAL(5, 4),

    -- Results - Metrics
    total_return_pct DECIMAL(10, 4),
    sharpe_ratio DECIMAL(10, 4),
    max_drawdown_pct DECIMAL(10, 4),
    win_rate_pct DECIMAL(10, 4),
    total_trades INTEGER,
    profit_factor DECIMAL(10, 4),
    avg_trade_duration_hours DECIMAL(10, 2),

    -- Results - Full data (for charts)
    equity_curve JSONB,  -- [[timestamp, value], ...]
    trades JSONB,        -- [{entry_time, exit_time, pnl, ...}, ...]

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),

    -- Indexes
    CONSTRAINT fk_strategy FOREIGN KEY (strategy_id)
        REFERENCES strategies(id) ON DELETE SET NULL
);

CREATE INDEX idx_backtest_strategy ON backtest_results(strategy_id);
CREATE INDEX idx_backtest_symbol ON backtest_results(symbol, timeframe);
CREATE INDEX idx_backtest_created ON backtest_results(created_at DESC);
```

**Effort:** 30 min

---

## Fáze 2: API Endpoints

### 2.1 Strategy Endpoints

**Soubor:** `api/main.py` (rozšíření)

```python
from data.strategy_storage import StrategyStorage, StrategyRecord

# ============================================================================
# STRATEGY ENDPOINTS
# ============================================================================

@app.get("/api/strategies")
async def list_strategies():
    """List all available strategies"""
    storage = StrategyStorage(get_connection_string())
    strategies = await storage.list_strategies()
    return [
        {
            "name": s.name,
            "description": s.description,
            "type": s.strategy_type,
            "parameters": s.parameters,
            "regime_filter": s.regime_filter,
        }
        for s in strategies
    ]

@app.get("/api/strategies/{name}")
async def get_strategy(name: str):
    """Get strategy details by name"""
    storage = StrategyStorage(get_connection_string())
    strategy = await storage.get_strategy(name)
    if not strategy:
        raise HTTPException(404, f"Strategy '{name}' not found")
    return strategy

@app.post("/api/strategies")
async def create_strategy(request: CreateStrategyRequest):
    """Create new composite strategy"""
    storage = StrategyStorage(get_connection_string())
    record = StrategyRecord(
        id=0,
        name=request.name,
        description=request.description,
        strategy_type='composite',
        builtin_class=None,
        entry_logic=request.entry_logic,
        exit_logic=request.exit_logic,
        parameters=request.parameters or {},
        regime_filter=request.regime_filter,
        sub_regime_filter=request.sub_regime_filter,
        is_active=True,
        created_at="",
        updated_at=""
    )
    created = await storage.create_strategy(record)
    return {"success": True, "strategy": created}

@app.delete("/api/strategies/{name}")
async def delete_strategy(name: str):
    """Delete strategy (soft delete)"""
    storage = StrategyStorage(get_connection_string())
    success = await storage.delete_strategy(name)
    if not success:
        raise HTTPException(404, f"Strategy '{name}' not found")
    return {"success": True}
```

**Effort:** 1 h

---

### 2.2 Backtest Endpoint

**Soubor:** `api/main.py` (rozšíření)

```python
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class BacktestRequest(BaseModel):
    strategy_name: str
    symbol: str = "BTCUSDT"
    timeframe: str = "1h"
    start_date: str  # ISO format
    end_date: Optional[str] = None
    initial_capital: float = 10000.0
    commission_rate: float = 0.001
    slippage_rate: float = 0.0005
    position_size_pct: float = 1.0
    # Override strategy parameters
    parameters: Optional[dict] = None
    # Override regime filter for this run
    regime_filter: Optional[List[str]] = None

class BacktestResponse(BaseModel):
    success: bool
    strategy_name: str
    symbol: str
    timeframe: str

    # Key metrics
    total_return_pct: float
    sharpe_ratio: float
    max_drawdown_pct: float
    win_rate_pct: float
    total_trades: int
    profit_factor: float

    # Data for visualization
    equity_curve: List[dict]  # [{time, value}, ...]
    trades: List[dict]        # [{entry_time, exit_time, entry_price, exit_price, pnl, pnl_pct}, ...]

    # Regime breakdown (optional)
    regime_stats: Optional[dict] = None

@app.post("/api/backtest", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest):
    """Run backtest with specified strategy and parameters"""

    # 1. Load strategy
    storage = StrategyStorage(get_connection_string())
    strategy_record = await storage.get_strategy(request.strategy_name)
    if not strategy_record:
        raise HTTPException(404, f"Strategy '{request.strategy_name}' not found")

    # 2. Apply parameter overrides
    if request.parameters:
        strategy_record.parameters.update(request.parameters)
    if request.regime_filter:
        strategy_record.regime_filter = request.regime_filter

    # 3. Instantiate strategy
    strategy = storage.instantiate_strategy(strategy_record)

    # 4. Load data
    data_storage = PostgresStorage(get_connection_string())
    data = await data_storage.get_candles(
        symbol=request.symbol,
        timeframe=request.timeframe,
        start_time=datetime.fromisoformat(request.start_date),
        end_time=datetime.fromisoformat(request.end_date) if request.end_date else None
    )

    if data.empty:
        raise HTTPException(400, "No data available for specified range")

    # 5. Run backtest
    from core.backtest import BacktestEngine
    engine = BacktestEngine(
        data=data,
        strategy=strategy,
        initial_capital=request.initial_capital,
        commission_rate=request.commission_rate,
        slippage_rate=request.slippage_rate,
        position_size_pct=request.position_size_pct,
        enable_regime_detection=True
    )

    results = engine.run()

    # 6. Format response
    return BacktestResponse(
        success=True,
        strategy_name=request.strategy_name,
        symbol=request.symbol,
        timeframe=request.timeframe,
        total_return_pct=results['metrics']['total_return'],
        sharpe_ratio=results['metrics'].get('sharpe_ratio', 0),
        max_drawdown_pct=results['metrics'].get('max_drawdown', 0),
        win_rate_pct=results['metrics'].get('win_rate', 0),
        total_trades=results['metrics'].get('total_trades', 0),
        profit_factor=results['metrics'].get('profit_factor', 0),
        equity_curve=[
            {"time": ts.isoformat(), "value": val}
            for ts, val in results['equity_curve']
        ],
        trades=[
            {
                "entry_time": t.entry_time.isoformat(),
                "exit_time": t.exit_time.isoformat(),
                "entry_price": t.entry_price,
                "exit_price": t.exit_price,
                "pnl": t.pnl,
                "pnl_pct": t.return_pct,
                "duration_hours": t.duration.total_seconds() / 3600
            }
            for t in results['trades']
        ]
    )
```

**Effort:** 2 h

---

## Fáze 3: Frontend

### 3.1 Strategy List Page

**Soubor:** `frontend/app/strategies/page.tsx`

```tsx
"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft, Plus, Play, Settings, TrendingUp, Activity } from "lucide-react";
import Link from "next/link";

interface Strategy {
  name: string;
  description: string;
  type: "builtin" | "composite";
  parameters: Record<string, any>;
  regime_filter: string[] | null;
}

export default function StrategiesPage() {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStrategies();
  }, []);

  const loadStrategies = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/strategies");
      const data = await response.json();
      setStrategies(data);
    } catch (error) {
      console.error("Failed to load strategies:", error);
    } finally {
      setLoading(false);
    }
  };

  const getStrategyIcon = (type: string) => {
    return type === "builtin" ? (
      <TrendingUp className="h-5 w-5 text-blue-600" />
    ) : (
      <Activity className="h-5 w-5 text-purple-600" />
    );
  };

  return (
    <div className="min-h-screen bg-neutral-100 dark:bg-neutral-800">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/">
              <Button variant="outline" size="icon">
                <ArrowLeft className="h-4 w-4" />
              </Button>
            </Link>
            <div>
              <h1 className="text-3xl font-bold">Trading Strategies</h1>
              <p className="text-neutral-600 dark:text-neutral-400">
                Manage and test your trading strategies
              </p>
            </div>
          </div>
          <Link href="/strategies/create">
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Create Strategy
            </Button>
          </Link>
        </div>

        {/* Strategy Cards */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {strategies.map((strategy) => (
            <Card key={strategy.name} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {getStrategyIcon(strategy.type)}
                    <CardTitle className="text-lg">{strategy.name}</CardTitle>
                  </div>
                  <span className={`px-2 py-1 text-xs rounded ${
                    strategy.type === "builtin"
                      ? "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-200"
                      : "bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-200"
                  }`}>
                    {strategy.type}
                  </span>
                </div>
                <CardDescription>{strategy.description}</CardDescription>
              </CardHeader>
              <CardContent>
                {/* Parameters */}
                <div className="mb-4">
                  <h4 className="text-sm font-medium mb-2">Parameters:</h4>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(strategy.parameters).map(([key, value]) => (
                      <span
                        key={key}
                        className="px-2 py-1 text-xs bg-neutral-200 dark:bg-neutral-700 rounded"
                      >
                        {key}: {value}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Regime Filter */}
                {strategy.regime_filter && (
                  <div className="mb-4">
                    <h4 className="text-sm font-medium mb-2">Regime Filter:</h4>
                    <div className="flex flex-wrap gap-2">
                      {strategy.regime_filter.map((regime) => (
                        <span
                          key={regime}
                          className="px-2 py-1 text-xs bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-200 rounded"
                        >
                          {regime}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="flex gap-2 mt-4">
                  <Link href={`/backtest?strategy=${strategy.name}`} className="flex-1">
                    <Button variant="outline" className="w-full">
                      <Play className="mr-2 h-4 w-4" />
                      Backtest
                    </Button>
                  </Link>
                  <Link href={`/strategies/${strategy.name}`}>
                    <Button variant="outline" size="icon">
                      <Settings className="h-4 w-4" />
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
```

**Effort:** 1.5 h

---

### 3.2 Backtest Page

**Soubor:** `frontend/app/backtest/page.tsx`

```tsx
"use client";

import { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft, Play, TrendingUp, TrendingDown, Activity } from "lucide-react";
import Link from "next/link";
import dynamic from "next/dynamic";

// Dynamic import for chart (client-side only)
const BacktestChart = dynamic(() => import("@/components/BacktestChart"), { ssr: false });

interface BacktestResult {
  success: boolean;
  strategy_name: string;
  total_return_pct: number;
  sharpe_ratio: number;
  max_drawdown_pct: number;
  win_rate_pct: number;
  total_trades: number;
  profit_factor: number;
  equity_curve: { time: string; value: number }[];
  trades: {
    entry_time: string;
    exit_time: string;
    entry_price: number;
    exit_price: number;
    pnl: number;
    pnl_pct: number;
  }[];
}

export default function BacktestPage() {
  const searchParams = useSearchParams();
  const preselectedStrategy = searchParams.get("strategy");

  // Form state
  const [strategies, setStrategies] = useState<string[]>([]);
  const [selectedStrategy, setSelectedStrategy] = useState(preselectedStrategy || "");
  const [symbol, setSymbol] = useState("BTCUSDT");
  const [timeframe, setTimeframe] = useState("1h");
  const [startDate, setStartDate] = useState("2024-01-01");
  const [endDate, setEndDate] = useState("2024-06-30");
  const [initialCapital, setInitialCapital] = useState(10000);

  // Results state
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Chart display mode
  const [displayMode, setDisplayMode] = useState<1 | 2 | 3 | 4>(4);
  // 1: hidden, 2: candles 50% + trades 100%, 3: candles 0% + trades 50%, 4: both 100%

  useEffect(() => {
    loadStrategies();
  }, []);

  const loadStrategies = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/strategies");
      const data = await response.json();
      setStrategies(data.map((s: any) => s.name));
    } catch (error) {
      console.error("Failed to load strategies:", error);
    }
  };

  const runBacktest = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch("http://localhost:8000/api/backtest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          strategy_name: selectedStrategy,
          symbol,
          timeframe,
          start_date: startDate,
          end_date: endDate,
          initial_capital: initialCapital,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Backtest failed");
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-neutral-100 dark:bg-neutral-800">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8 flex items-center gap-4">
          <Link href="/strategies">
            <Button variant="outline" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold">Backtest</h1>
            <p className="text-neutral-600 dark:text-neutral-400">
              Test your strategy on historical data
            </p>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          {/* Form */}
          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle>Configuration</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Strategy Select */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Strategy</label>
                <select
                  value={selectedStrategy}
                  onChange={(e) => setSelectedStrategy(e.target.value)}
                  className="w-full rounded-md border px-3 py-2 dark:bg-neutral-900"
                >
                  <option value="">Select a strategy...</option>
                  {strategies.map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>

              {/* Symbol */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Symbol</label>
                <input
                  type="text"
                  value={symbol}
                  onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                  className="w-full rounded-md border px-3 py-2 dark:bg-neutral-900"
                />
              </div>

              {/* Timeframe */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Timeframe</label>
                <select
                  value={timeframe}
                  onChange={(e) => setTimeframe(e.target.value)}
                  className="w-full rounded-md border px-3 py-2 dark:bg-neutral-900"
                >
                  <option value="1h">1 hour</option>
                  <option value="4h">4 hours</option>
                  <option value="1d">1 day</option>
                </select>
              </div>

              {/* Date Range */}
              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Start</label>
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="w-full rounded-md border px-3 py-2 dark:bg-neutral-900"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">End</label>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="w-full rounded-md border px-3 py-2 dark:bg-neutral-900"
                  />
                </div>
              </div>

              {/* Initial Capital */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Initial Capital ($)</label>
                <input
                  type="number"
                  value={initialCapital}
                  onChange={(e) => setInitialCapital(Number(e.target.value))}
                  className="w-full rounded-md border px-3 py-2 dark:bg-neutral-900"
                />
              </div>

              {/* Run Button */}
              <Button
                onClick={runBacktest}
                disabled={loading || !selectedStrategy}
                className="w-full"
              >
                {loading ? (
                  <>
                    <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                    Running...
                  </>
                ) : (
                  <>
                    <Play className="mr-2 h-4 w-4" />
                    Run Backtest
                  </>
                )}
              </Button>

              {error && (
                <div className="p-3 bg-red-50 dark:bg-red-950 text-red-700 dark:text-red-300 rounded-md text-sm">
                  {error}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Results */}
          <div className="lg:col-span-2 space-y-6">
            {result && (
              <>
                {/* Metrics */}
                <div className="grid gap-4 md:grid-cols-3">
                  <MetricCard
                    title="Total Return"
                    value={`${result.total_return_pct.toFixed(2)}%`}
                    icon={result.total_return_pct >= 0 ? TrendingUp : TrendingDown}
                    positive={result.total_return_pct >= 0}
                  />
                  <MetricCard
                    title="Sharpe Ratio"
                    value={result.sharpe_ratio.toFixed(2)}
                    icon={Activity}
                    positive={result.sharpe_ratio > 1}
                  />
                  <MetricCard
                    title="Max Drawdown"
                    value={`${result.max_drawdown_pct.toFixed(2)}%`}
                    icon={TrendingDown}
                    positive={false}
                  />
                  <MetricCard
                    title="Win Rate"
                    value={`${result.win_rate_pct.toFixed(1)}%`}
                    icon={Activity}
                    positive={result.win_rate_pct > 50}
                  />
                  <MetricCard
                    title="Total Trades"
                    value={result.total_trades.toString()}
                    icon={Activity}
                  />
                  <MetricCard
                    title="Profit Factor"
                    value={result.profit_factor.toFixed(2)}
                    icon={Activity}
                    positive={result.profit_factor > 1}
                  />
                </div>

                {/* Chart with Display Mode Toggle */}
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between">
                    <CardTitle>Equity Curve & Trades</CardTitle>
                    <div className="flex gap-2">
                      {[1, 2, 3, 4].map((mode) => (
                        <Button
                          key={mode}
                          variant={displayMode === mode ? "default" : "outline"}
                          size="sm"
                          onClick={() => setDisplayMode(mode as 1 | 2 | 3 | 4)}
                        >
                          {mode === 1 && "Hidden"}
                          {mode === 2 && "Trades Focus"}
                          {mode === 3 && "Subtle"}
                          {mode === 4 && "Full"}
                        </Button>
                      ))}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <BacktestChart
                      equityCurve={result.equity_curve}
                      trades={result.trades}
                      displayMode={displayMode}
                      symbol={symbol}
                      timeframe={timeframe}
                      startDate={startDate}
                      endDate={endDate}
                    />
                  </CardContent>
                </Card>

                {/* Trades Table */}
                <Card>
                  <CardHeader>
                    <CardTitle>Trade History</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b">
                            <th className="text-left p-2">Entry</th>
                            <th className="text-left p-2">Exit</th>
                            <th className="text-right p-2">Entry Price</th>
                            <th className="text-right p-2">Exit Price</th>
                            <th className="text-right p-2">P&L</th>
                            <th className="text-right p-2">Return</th>
                          </tr>
                        </thead>
                        <tbody>
                          {result.trades.slice(0, 20).map((trade, i) => (
                            <tr key={i} className="border-b hover:bg-neutral-50 dark:hover:bg-neutral-700">
                              <td className="p-2">{new Date(trade.entry_time).toLocaleDateString()}</td>
                              <td className="p-2">{new Date(trade.exit_time).toLocaleDateString()}</td>
                              <td className="p-2 text-right">${trade.entry_price.toFixed(2)}</td>
                              <td className="p-2 text-right">${trade.exit_price.toFixed(2)}</td>
                              <td className={`p-2 text-right ${trade.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                ${trade.pnl.toFixed(2)}
                              </td>
                              <td className={`p-2 text-right ${trade.pnl_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                {trade.pnl_pct.toFixed(2)}%
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                      {result.trades.length > 20 && (
                        <p className="text-center text-sm text-neutral-500 mt-4">
                          Showing 20 of {result.trades.length} trades
                        </p>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// Helper component for metric cards
function MetricCard({ title, value, icon: Icon, positive }: {
  title: string;
  value: string;
  icon: any;
  positive?: boolean;
}) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-neutral-500">{title}</p>
            <p className={`text-2xl font-bold ${
              positive === undefined ? '' : positive ? 'text-green-600' : 'text-red-600'
            }`}>
              {value}
            </p>
          </div>
          <Icon className={`h-8 w-8 ${
            positive === undefined ? 'text-neutral-400' : positive ? 'text-green-600' : 'text-red-600'
          }`} />
        </div>
      </CardContent>
    </Card>
  );
}
```

**Effort:** 2.5 h

---

### 3.3 Backtest Chart Component

**Soubor:** `frontend/components/BacktestChart.tsx`

```tsx
"use client";

import { useEffect, useRef, useState } from "react";
import { createChart, IChartApi, ISeriesApi } from "lightweight-charts";

interface Trade {
  entry_time: string;
  exit_time: string;
  entry_price: number;
  exit_price: number;
  pnl: number;
}

interface BacktestChartProps {
  equityCurve: { time: string; value: number }[];
  trades: Trade[];
  displayMode: 1 | 2 | 3 | 4;
  symbol: string;
  timeframe: string;
  startDate: string;
  endDate: string;
}

export default function BacktestChart({
  equityCurve,
  trades,
  displayMode,
  symbol,
  timeframe,
  startDate,
  endDate,
}: BacktestChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const [candles, setCandles] = useState<any[]>([]);

  // Fetch candle data for overlay
  useEffect(() => {
    const fetchCandles = async () => {
      try {
        const response = await fetch(
          `http://localhost:8000/api/data/candles/${symbol}/${timeframe}?start=${startDate}&end=${endDate}`
        );
        const data = await response.json();
        setCandles(data);
      } catch (error) {
        console.error("Failed to fetch candles:", error);
      }
    };
    fetchCandles();
  }, [symbol, timeframe, startDate, endDate]);

  useEffect(() => {
    if (!containerRef.current) return;

    // Create chart
    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height: 400,
      layout: {
        background: { color: "transparent" },
        textColor: "#999",
      },
      grid: {
        vertLines: { color: "#2B2B43" },
        horzLines: { color: "#2B2B43" },
      },
    });

    chartRef.current = chart;

    // Opacity based on display mode
    const candleOpacity = displayMode === 1 ? 0 : displayMode === 2 ? 0.5 : displayMode === 3 ? 0 : 1;
    const tradeOpacity = displayMode === 1 ? 0 : displayMode === 2 ? 1 : displayMode === 3 ? 0.5 : 1;

    // Add candlestick series (if visible)
    if (candleOpacity > 0 && candles.length > 0) {
      const candleSeries = chart.addCandlestickSeries({
        upColor: `rgba(38, 166, 154, ${candleOpacity})`,
        downColor: `rgba(239, 83, 80, ${candleOpacity})`,
        borderVisible: false,
        wickUpColor: `rgba(38, 166, 154, ${candleOpacity})`,
        wickDownColor: `rgba(239, 83, 80, ${candleOpacity})`,
      });
      candleSeries.setData(candles);
    }

    // Add equity curve
    const equitySeries = chart.addLineSeries({
      color: "#2962FF",
      lineWidth: 2,
    });
    equitySeries.setData(
      equityCurve.map((p) => ({
        time: p.time.split("T")[0],
        value: p.value,
      }))
    );

    // Add trade markers (if visible)
    if (tradeOpacity > 0) {
      const markers = trades.flatMap((trade) => [
        {
          time: trade.entry_time.split("T")[0],
          position: "belowBar" as const,
          color: `rgba(38, 166, 154, ${tradeOpacity})`,
          shape: "arrowUp" as const,
          text: "BUY",
        },
        {
          time: trade.exit_time.split("T")[0],
          position: "aboveBar" as const,
          color: trade.pnl >= 0
            ? `rgba(38, 166, 154, ${tradeOpacity})`
            : `rgba(239, 83, 80, ${tradeOpacity})`,
          shape: "arrowDown" as const,
          text: `${trade.pnl >= 0 ? "+" : ""}${trade.pnl.toFixed(0)}`,
        },
      ]);
      equitySeries.setMarkers(markers);
    }

    chart.timeScale().fitContent();

    // Resize handler
    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
    };
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
    };
  }, [equityCurve, trades, candles, displayMode]);

  return <div ref={containerRef} className="w-full" />;
}
```

**Effort:** 1.5 h

---

### 3.4 Create Strategy Page

**Soubor:** `frontend/app/strategies/create/page.tsx`

Jednoduchý formulář pro vytvoření composite strategie:
- Název + popis
- Entry logic builder (dropdown pro indikátory, podmínky)
- Exit logic builder
- Regime filter checkboxy

**Effort:** 2 h

---

## Fáze 4: Agent Tools

### 4.1 Tool Definitions

**Soubor:** `agent/tools.py`

```python
BACKTEST_TOOLS = [
    {
        "name": "list_strategies",
        "description": "List all available trading strategies with their parameters and regime filters",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_strategy_details",
        "description": "Get detailed information about a specific strategy including its entry/exit logic",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Strategy name"
                }
            },
            "required": ["name"]
        }
    },
    {
        "name": "run_backtest",
        "description": "Run a backtest with specified strategy and parameters. Returns performance metrics and trade history.",
        "input_schema": {
            "type": "object",
            "properties": {
                "strategy_name": {
                    "type": "string",
                    "description": "Name of the strategy to test"
                },
                "symbol": {
                    "type": "string",
                    "description": "Trading pair (e.g., BTCUSDT)",
                    "default": "BTCUSDT"
                },
                "timeframe": {
                    "type": "string",
                    "enum": ["1h", "4h", "1d"],
                    "default": "1h"
                },
                "start_date": {
                    "type": "string",
                    "description": "Start date in ISO format (YYYY-MM-DD)"
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in ISO format (YYYY-MM-DD)"
                },
                "regime_filter": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional: Only trade in these market regimes"
                }
            },
            "required": ["strategy_name", "start_date"]
        }
    },
    {
        "name": "create_strategy",
        "description": "Create a new composite trading strategy by combining indicators and conditions",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Unique strategy name"
                },
                "description": {
                    "type": "string",
                    "description": "Strategy description"
                },
                "entry_conditions": {
                    "type": "array",
                    "description": "List of entry conditions",
                    "items": {
                        "type": "object",
                        "properties": {
                            "indicator": {"type": "string", "enum": ["RSI", "MACD", "SMA", "EMA", "BB"]},
                            "operator": {"type": "string", "enum": ["<", ">", "cross_above", "cross_below"]},
                            "value": {"type": "number"}
                        }
                    }
                },
                "exit_conditions": {
                    "type": "array",
                    "description": "List of exit conditions"
                },
                "entry_logic": {
                    "type": "string",
                    "enum": ["AND", "OR"],
                    "default": "AND"
                },
                "exit_logic": {
                    "type": "string",
                    "enum": ["AND", "OR"],
                    "default": "OR"
                },
                "regime_filter": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["TREND_UP", "TREND_DOWN", "RANGE", "CHOPPY", "NEUTRAL"]}
                }
            },
            "required": ["name", "entry_conditions", "exit_conditions"]
        }
    },
    {
        "name": "analyze_backtest_results",
        "description": "Analyze backtest results and provide insights. Use this after run_backtest to interpret the metrics.",
        "input_schema": {
            "type": "object",
            "properties": {
                "metrics": {
                    "type": "object",
                    "description": "Metrics from backtest result"
                },
                "trades": {
                    "type": "array",
                    "description": "Trade history from backtest"
                }
            },
            "required": ["metrics"]
        }
    }
]
```

**Effort:** 1 h

---

## Časový odhad

| Fáze | Komponenta | Effort |
|------|------------|--------|
| **1. Backend Core** | | |
| | 1.1 Regime filter | 30 min |
| | 1.2 DB Schema strategies | 30 min |
| | 1.3 Strategy Storage | 1.5 h |
| | 1.4 Backtest Results Schema | 30 min |
| **2. API** | | |
| | 2.1 Strategy endpoints | 1 h |
| | 2.2 Backtest endpoint | 2 h |
| **3. Frontend** | | |
| | 3.1 Strategy List page | 1.5 h |
| | 3.2 Backtest page | 2.5 h |
| | 3.3 Backtest Chart | 1.5 h |
| | 3.4 Create Strategy page | 2 h |
| **4. Agent** | | |
| | 4.1 Tool definitions | 1 h |
| | | |
| **TOTAL** | | **~14.5 h** |

---

## Prioritizace pro agenta (domácí úkol)

**Must-have (MVP pro agenta):**
1. Regime filter v CompositeStrategy (30 min)
2. Strategy endpoints - list + get (1 h)
3. Backtest endpoint (2 h)
4. Tool definitions (1 h)

**MVP Total: ~4.5 h**

**Nice-to-have (portfolio):**
- Frontend pages
- Strategy persistence
- Create strategy via UI
- Backtest results storage

---

## Další kroky

1. Schválit plán
2. Implementovat MVP pro agenta (4.5 h)
3. Otestovat agent flow
4. Dodat frontend (later)
