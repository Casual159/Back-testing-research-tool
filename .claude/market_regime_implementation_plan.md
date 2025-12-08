# Market Regime Classifier - Implementation Plan

## Executive Summary

Implementace pokročilého Market Regime Classifier s 3D granulární klasifikací (trend + volatility + momentum) a vizualizací v TradingView stylu.

**Approach:** Kombinace granulárního GPT přístupu s praktičním Gemini mapováním.

---

## 1. Architecture Overview

### 1.1 Component Structure

```
core/
  indicators/
    technical.py           # Existing - ADD: ADX, ROC
    regime.py             # NEW - Market Regime Classifier
    __init__.py           # Update exports

api/
  main.py                 # ADD: regime endpoints

frontend/
  components/
    CandlestickChart.tsx  # Existing - will extend
    RegimeChart.tsx       # NEW - regime visualization layer
```

### 1.2 Data Flow

```
OHLCV Data (PostgreSQL)
  ↓
Add All Indicators (technical.py)
  ↓ (includes ADX, ROC)
RegimeClassifier.detect_regime(row)
  ↓
{
  trend_state: "uptrend" | "downtrend" | "neutral",
  volatility_state: "low" | "high",
  momentum_state: "bullish" | "bearish" | "weak",
  full_regime: "UPTREND_LOWVOL_BULLISH",
  simplified: "TREND_UP"  // Gemini mapping
}
  ↓
API Endpoint (/api/data/regime/{symbol}/{timeframe})
  ↓
Frontend RegimeChart (colored bars)
```

---

## 2. Missing Indicators Implementation

### 2.1 ADX (Average Directional Index)

**Purpose:** Trend strength detection
- ADX > 25 → trending market
- ADX < 20 → sideways/ranging

**Implementation:** Add to `TechnicalIndicators` class

```python
@staticmethod
def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate ADX using +DI, -DI, and smoothed directional movement
    """
    # Implementation based on standard ADX formula
```

### 2.2 ROC (Rate of Change)

**Purpose:** Momentum measurement
- ROC > 0 → bullish momentum
- ROC < 0 → bearish momentum

**Implementation:** Add to `TechnicalIndicators` class

```python
@staticmethod
def roc(data: pd.Series, period: int = 12) -> pd.Series:
    """
    Rate of Change: ((close - close_n_periods_ago) / close_n_periods_ago) * 100
    """
    return ((data - data.shift(period)) / data.shift(period)) * 100
```

### 2.3 Update `add_all_indicators()`

Add ADX and ROC to the indicator pipeline:

```python
# ADX
result['adx'] = TechnicalIndicators.adx(df['high'], df['low'], df['close'])

# ROC
result['roc'] = TechnicalIndicators.roc(df['close'], 12)
```

---

## 3. Market Regime Classifier

### 3.1 Core Classifier (`core/indicators/regime.py`)

**Design Principles:**
- ✅ Event-driven: No lookahead bias
- ✅ Candle-by-candle processing
- ✅ Adaptive thresholds using rolling percentiles
- ✅ Granular 3D classification + simplified mapping

### 3.2 Regime Detection Logic

#### A) Trend State Detection

```python
def detect_trend_state(row, indicators) -> str:
    """
    Returns: "uptrend" | "downtrend" | "neutral"

    Logic:
    1. IF ADX < 20 → "neutral" (sideways, weak trend)
    2. ELSE IF ADX >= 25:
       - IF close > SMA50 AND SMA50 > SMA200 → "uptrend"
       - IF close < SMA50 AND SMA50 < SMA200 → "downtrend"
       - ELSE → "neutral"
    3. Nuance: Check SMA20/SMA50 cross for emerging trends
    """
```

**Key Indicators:**
- ADX (trend strength)
- SMA 20, 50, 200 (trend direction)
- Close price position

#### B) Volatility State Detection

```python
def detect_volatility_state(row, adaptive_thresholds) -> str:
    """
    Returns: "low" | "high"

    Logic:
    1. normalized_vol = ATR / close
    2. boll_width = (bb_upper - bb_lower) / bb_middle
    3. Use rolling percentiles (30th/70th) for adaptive thresholds

    IF normalized_vol < p30 AND boll_width < p30 → "low"
    ELIF normalized_vol > p70 OR boll_width > p70 → "high"
    ELSE → "low" (default unless strong signal)
    """
```

**Key Indicators:**
- ATR (normalized by price)
- Bollinger Band width
- Rolling percentile thresholds

**Adaptive Thresholds:**
- Window: 100-200 periods
- Percentiles: 30th (low threshold), 70th (high threshold)
- Recalculated continuously

#### C) Momentum State Detection

```python
def detect_momentum_state(row) -> str:
    """
    Returns: "bullish" | "bearish" | "weak"

    Scoring System:
    bullish_score = 0
    - IF ROC > 0: +1
    - IF MACD_histogram > 0: +1
    - IF RSI > 55: +1

    bearish_score = 0
    - IF ROC < 0: +1
    - IF MACD_histogram < 0: +1
    - IF RSI < 45: +1

    IF bullish_score >= 2 → "bullish"
    ELIF bearish_score >= 2 → "bearish"
    ELSE → "weak"
    """
```

**Key Indicators:**
- ROC (rate of change)
- MACD histogram
- RSI (with thresholds 45/55)

### 3.3 Composite Regime Generation

```python
def detect_market_regime(row, adaptive_thresholds) -> dict:
    """
    Main entry point - returns comprehensive regime analysis

    Returns:
    {
        "trend_state": "uptrend",
        "volatility_state": "low",
        "momentum_state": "bullish",
        "full_regime": "UPTREND_LOWVOL_BULLISH",
        "simplified": "TREND_UP",
        "confidence": 0.85  # Optional: aggregate confidence score
    }
    """
    trend = detect_trend_state(row, indicators)
    volatility = detect_volatility_state(row, adaptive_thresholds)
    momentum = detect_momentum_state(row)

    # Composite
    full = f"{trend.upper()}_{volatility.upper()}VOL_{momentum.upper()}MOM"

    # Simplified mapping (Gemini style)
    simplified = map_to_simplified_regime(trend, volatility, momentum)

    return {
        "trend_state": trend,
        "volatility_state": volatility,
        "momentum_state": momentum,
        "full_regime": full,
        "simplified": simplified
    }
```

### 3.4 Simplified Regime Mapping

Map granular → practical trading regimes:

```python
def map_to_simplified_regime(trend, volatility, momentum) -> str:
    """
    Map to Gemini-style practical regimes

    Returns: "TREND_UP" | "TREND_DOWN" | "RANGE" | "CHOPPY" | "NEUTRAL"
    """
    # CHOPPY: High volatility + weak momentum
    if volatility == "high" and momentum == "weak":
        return "CHOPPY"

    # TREND_UP: Uptrend + bullish momentum
    if trend == "uptrend" and momentum == "bullish":
        return "TREND_UP"

    # TREND_DOWN: Downtrend + bearish momentum
    if trend == "downtrend" and momentum == "bearish":
        return "TREND_DOWN"

    # RANGE: Neutral trend + low volatility
    if trend == "neutral" and volatility == "low":
        return "RANGE"

    # Default
    return "NEUTRAL"
```

---

## 4. Adaptive Thresholds Implementation

### 4.1 Rolling Percentile Calculator

```python
class AdaptiveThresholds:
    """
    Calculate and maintain rolling percentile thresholds
    for volatility detection
    """

    def __init__(self, window: int = 100):
        self.window = window
        self.atr_buffer = []
        self.boll_width_buffer = []

    def update(self, atr_normalized, boll_width):
        """Update buffers with new values"""
        self.atr_buffer.append(atr_normalized)
        self.boll_width_buffer.append(boll_width)

        # Keep only last window periods
        if len(self.atr_buffer) > self.window:
            self.atr_buffer.pop(0)
            self.boll_width_buffer.pop(0)

    def get_thresholds(self) -> dict:
        """
        Calculate current percentile thresholds

        Returns:
        {
            "atr_p30": float,
            "atr_p70": float,
            "boll_p30": float,
            "boll_p70": float
        }
        """
        if len(self.atr_buffer) < self.window:
            # Not enough data - return defaults
            return default_thresholds()

        return {
            "atr_p30": np.percentile(self.atr_buffer, 30),
            "atr_p70": np.percentile(self.atr_buffer, 70),
            "boll_p30": np.percentile(self.boll_width_buffer, 30),
            "boll_p70": np.percentile(self.boll_width_buffer, 70)
        }
```

---

## 5. Integration Patterns

### 5.1 Option A: Standalone Analysis

**Use Case:** Pre-compute regime for all historical data

```python
# Compute regimes for entire dataset
df_with_indicators = add_all_indicators(df)
regime_classifier = RegimeClassifier()
regimes = regime_classifier.classify_dataframe(df_with_indicators)

# Returns DataFrame with regime columns added
# Can be stored in DB or returned via API
```

**Pros:**
- ✅ Fast - compute once
- ✅ No impact on backtest engine
- ✅ Easy to visualize and analyze
- ✅ Can store in database for quick retrieval

**Cons:**
- ❌ Separate from live backtest execution

### 5.2 Option B: Live Integration into Backtest Engine ⭐ PRIORITY

**Use Case:** Real-time regime tracking during backtest

```python
# In engine.py - add regime to MarketEvent metadata
market_event = self._create_market_event(timestamp, bar)
regime = self.regime_classifier.detect_regime(bar)
market_event.metadata['regime'] = regime
```

**Pros:**
- ✅ Regime available to strategy during backtesting
- ✅ Strategies can filter by regime
- ✅ True event-driven processing
- ✅ **KEY:** Enables strategy-regime coupling (core feature)

**Cons:**
- ❌ More complex
- ❌ Slower (compute every bar)

**Recommendation:** Implement BOTH approaches:
- **Phase 3A:** Standalone API for visualization
- **Phase 3B:** Live integration for strategy-regime coupling

**Rationale:** Market regime is a KEY variable for strategy selection, not a nice-to-have. Strategies need access to regime in real-time to make decisions (e.g., trend-following only in TREND_UP/DOWN, mean-reversion in RANGE).

### 5.3 Strategy Regime Filtering (Future Enhancement)

```python
class RegimeAwareStrategy(Strategy):
    """
    Strategy that only trades in specific market regimes
    """

    def __init__(self, base_strategy, allowed_regimes):
        self.strategy = base_strategy
        self.allowed_regimes = allowed_regimes

    def calculate_signals(self, market_event):
        regime = market_event.metadata.get('regime')

        if regime['simplified'] not in self.allowed_regimes:
            return None  # Don't trade in this regime

        return self.strategy.calculate_signals(market_event)

# Example: Only trade trend-following strategy in TREND_UP/TREND_DOWN
strategy = RegimeAwareStrategy(
    base_strategy=MovingAverageCrossover(),
    allowed_regimes=["TREND_UP", "TREND_DOWN"]
)
```

---

## 6. API Endpoints

### 6.1 New Endpoint: Get Regime Data

```python
@app.get("/api/data/regime/{symbol}/{timeframe}")
def get_regime_data(symbol: str, timeframe: str):
    """
    Calculate and return market regime data for visualization

    Returns:
    [
        {
            "time": 1234567890,
            "regime": "TREND_UP",
            "full_regime": "UPTREND_LOWVOL_BULLISH",
            "trend_state": "uptrend",
            "volatility_state": "low",
            "momentum_state": "bullish",
            "color": "#22c55e"  // Green for TREND_UP
        },
        ...
    ]
    """
    # 1. Fetch candles from DB
    df = storage.get_candles(symbol, timeframe)

    # 2. Add all indicators
    df = add_all_indicators(df)

    # 3. Calculate regimes
    classifier = RegimeClassifier()
    regimes = classifier.classify_dataframe(df)

    # 4. Format for frontend
    result = []
    for _, row in regimes.iterrows():
        result.append({
            "time": int(row['open_time'].timestamp()),
            "regime": row['simplified_regime'],
            "full_regime": row['full_regime'],
            "trend_state": row['trend_state'],
            "volatility_state": row['volatility_state'],
            "momentum_state": row['momentum_state'],
            "color": get_regime_color(row['simplified_regime'])
        })

    return result
```

### 6.2 Color Mapping

```python
def get_regime_color(regime: str) -> str:
    """Map regime to visualization color"""
    colors = {
        "TREND_UP": "#22c55e",      # Green
        "TREND_DOWN": "#ef4444",    # Red
        "RANGE": "#3b82f6",         # Blue
        "CHOPPY": "#f59e0b",        # Orange
        "NEUTRAL": "#6b7280"        # Gray
    }
    return colors.get(regime, "#6b7280")
```

---

## 7. Frontend Visualization

### 7.1 RegimeChart Component

Create new component similar to volume visualization:

```typescript
// frontend/components/RegimeChart.tsx

interface RegimeData {
  time: number;
  regime: string;
  full_regime: string;
  color: string;
}

export default function RegimeChart({ data }: { data: RegimeData[] }) {
  // Add histogram series (like volume)
  const regimeSeries = chart.addHistogramSeries({
    priceFormat: { type: 'custom', formatter: () => '' },
    priceScaleId: 'regime',
  });

  // Configure as separate pane below main chart
  chart.priceScale('regime').applyOptions({
    scaleMargins: {
      top: 0.9,   // 90% offset - shows as bottom bar
      bottom: 0,
    },
  });

  // Map regime data to histogram
  const histogramData = data.map(d => ({
    time: d.time,
    value: 1,  // Fixed height
    color: d.color
  }));

  regimeSeries.setData(histogramData);
}
```

### 7.2 Integration into CandlestickChart

Extend existing CandlestickChart component:

```typescript
// CandlestickChart.tsx

interface CandlestickChartProps {
  data: CandleData[];
  regimeData?: RegimeData[];  // Optional regime overlay
  symbol: string;
  timeframe: string;
}

export default function CandlestickChart({
  data,
  regimeData,
  symbol,
  timeframe
}: CandlestickChartProps) {
  // ... existing chart setup ...

  // Add regime series if provided
  if (regimeData && regimeData.length > 0) {
    const regimeSeries = chart.addHistogramSeries({
      priceScaleId: 'regime',
    });

    regimeSeries.setData(
      regimeData.map(d => ({
        time: d.time,
        value: 1,
        color: d.color
      }))
    );

    // Position below volume
    chart.priceScale('regime').applyOptions({
      scaleMargins: { top: 0.95, bottom: 0 }
    });
  }
}
```

### 7.3 Fetch Regime Data in ChartPage

```typescript
// frontend/app/chart/[symbol]/[timeframe]/page.tsx

const [regimeData, setRegimeData] = useState<RegimeData[]>([]);
const [showRegime, setShowRegime] = useState(true); // Toggle state

useEffect(() => {
  // Fetch both candles and regime data
  const fetchData = async () => {
    const [candlesRes, regimeRes] = await Promise.all([
      fetch(`http://localhost:8000/api/data/candles/${symbol}/${timeframe}`),
      fetch(`http://localhost:8000/api/data/regime/${symbol}/${timeframe}`)
    ]);

    setCandles(await candlesRes.json());
    setRegimeData(await regimeRes.json());
  };

  fetchData();
}, [symbol, timeframe]);

// Toggle control
<Button onClick={() => setShowRegime(!showRegime)}>
  {showRegime ? 'Hide' : 'Show'} Market Regime
</Button>

// Pass to chart (only if enabled)
<CandlestickChart
  data={candles}
  regimeData={showRegime ? regimeData : undefined}
  symbol={symbol}
  timeframe={timeframe}
/>
```

### 7.4 Hover Tooltip Enhancement

Add regime info to existing hover functionality:

```typescript
// On crosshair move, show regime details
chart.subscribeCrosshairMove((param) => {
  if (param.time) {
    const regime = regimeData.find(r => r.time === param.time);
    if (regime) {
      // Show tooltip with regime details
      showTooltip({
        regime: regime.regime,
        full: regime.full_regime,
        trend: regime.trend_state,
        volatility: regime.volatility_state,
        momentum: regime.momentum_state
      });
    }
  }
});
```

### 7.5 Playback Controls (Future Enhancement)

Add interactive playback controls for backtest visualization:

```typescript
// Playback state
const [isPlaying, setIsPlaying] = useState(false);
const [playbackSpeed, setPlaybackSpeed] = useState(1); // 1x, 2x, 5x, 10x
const [currentBar, setCurrentBar] = useState(0);

// Controls
<div className="playback-controls">
  <Button onClick={() => setIsPlaying(!isPlaying)}>
    {isPlaying ? '⏸️ Pause' : '▶️ Play'}
  </Button>

  <select onChange={(e) => setPlaybackSpeed(Number(e.target.value))}>
    <option value="1">1x</option>
    <option value="2">2x</option>
    <option value="5">5x</option>
    <option value="10">10x</option>
  </select>

  <input
    type="range"
    min="0"
    max={candles.length}
    value={currentBar}
    onChange={(e) => setCurrentBar(Number(e.target.value))}
  />
</div>

// Timeline scrubbing with lightweight-charts
chart.timeScale().scrollToPosition(currentBar, true);
chart.timeScale().setVisibleRange({
  from: candles[Math.max(0, currentBar - 100)].time,
  to: candles[currentBar].time
});
```

**Purpose:** Allow users to:
- ⏯️ Play/Pause backtest visualization
- ⏩ Control playback speed (1x - 10x)
- 📊 Scrub timeline to any point
- 👁️ Watch how regime evolves over time

**Implementation Note:** Use `lightweight-charts` timeScale API for smooth animation.

---

## 8. Implementation Phases

**⚠️ IMPORTANT: Execute phases sequentially with validation checkpoints**

After EACH phase:
1. ✅ Run tests / sanity checks
2. ✅ User review & approval
3. ✅ Commit working code before proceeding

**Do NOT proceed to next phase without explicit confirmation.**

---

### Phase 1: Core Indicators (1-2 hours)
1. ✅ Add ADX to technical.py
2. ✅ Add ROC to technical.py
3. ✅ Update add_all_indicators()
4. ✅ Test indicator calculations

### Phase 2: Regime Classifier (3-4 hours)
1. ✅ Create regime.py module
2. ✅ Implement trend detection
3. ✅ Implement volatility detection (with adaptive thresholds)
4. ✅ Implement momentum scoring
5. ✅ Implement composite regime detection
6. ✅ Add simplified regime mapping
7. ✅ Test on sample data

### Phase 3: Integration (2-3 hours)

**Phase 3A: API Endpoint**
1. ✅ Add regime endpoint to main.py
2. ✅ Test endpoint with existing data
3. ✅ Verify JSON response format

**Phase 3B: Live Engine Integration** ⭐ NEW
1. ✅ Add RegimeClassifier to BacktestEngine
2. ✅ Compute regime per bar and add to MarketEvent.metadata
3. ✅ Enable strategies to access regime
4. ✅ Test regime-aware strategy filtering

### Phase 4: Frontend Visualization (2-3 hours)
1. ✅ Create RegimeChart component
2. ✅ Extend CandlestickChart to support regime overlay
3. ✅ Add regime data fetching to ChartPage
4. ✅ Implement toggle show/hide regime (default: ON)
5. ✅ Implement color mapping
6. ✅ Add hover tooltip enhancements
7. ✅ Add regime color legend
8. ✅ Test visualization
9. 📋 (Optional) Playback controls placeholder

### Phase 5: Testing & Refinement (1-2 hours)
1. ✅ Test with different symbols/timeframes
2. ✅ Validate regime classification accuracy
3. ✅ Tune adaptive threshold parameters
4. ✅ Performance optimization
5. ✅ Documentation

**Total Estimated Time: 9-15 hours** (with live engine integration)

---

## 9. Testing Strategy

### 9.1 Unit Tests

```python
# tests/test_regime_classifier.py

def test_adx_calculation():
    # Test ADX matches known values
    pass

def test_roc_calculation():
    # Test ROC matches known values
    pass

def test_trend_detection():
    # Test trend states with synthetic data
    pass

def test_volatility_detection():
    # Test volatility classification
    pass

def test_momentum_scoring():
    # Test momentum state detection
    pass

def test_adaptive_thresholds():
    # Test percentile calculations
    pass
```

### 9.2 Integration Tests

```python
def test_regime_api_endpoint():
    # Test full API flow
    response = client.get("/api/data/regime/BTCUSDT/1h")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert 'regime' in data[0]
```

### 9.3 Manual Validation

1. **Visual inspection:** Chart regime bars against price action
2. **Known patterns:** Test on known trending/ranging periods
3. **Edge cases:** Test with limited data, extreme volatility
4. **Performance:** Measure computation time for large datasets

---

## 10. Configuration & Tuning

### 10.1 Regime Classifier Parameters

```python
# Default configuration
REGIME_CONFIG = {
    # Trend detection
    'adx_trending_threshold': 25,
    'adx_sideways_threshold': 20,

    # Volatility detection
    'adaptive_window': 100,
    'vol_low_percentile': 30,
    'vol_high_percentile': 70,

    # Momentum scoring
    'rsi_bullish_threshold': 55,
    'rsi_bearish_threshold': 45,
    'momentum_score_threshold': 2
}
```

### 10.2 Future Enhancements

1. **Machine Learning:** Train classifier on labeled regime data
2. **Multi-timeframe:** Aggregate regime across timeframes
3. **Regime transitions:** Detect and signal regime changes
4. **Strategy optimization:** Auto-select strategies by regime
5. **Alert system:** Notify on regime changes
6. **Historical analysis:** Regime distribution statistics

---

## 11. Database Considerations

### 11.1 Option A: Compute On-The-Fly (MVP Phase)

**Pros:**
- No schema changes
- Always uses latest logic
- No storage overhead

**Cons:**
- Slower API response
- Repeated computation

**Implementation:** Phase 1 MVP uses this approach

### 11.2 Option B: Store Pre-computed Regimes ⭐ FUTURE REQUIREMENT

Create new table:

```sql
CREATE TABLE market_regimes (
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    open_time TIMESTAMP NOT NULL,
    trend_state VARCHAR(20),
    volatility_state VARCHAR(10),
    momentum_state VARCHAR(20),
    full_regime VARCHAR(50),
    simplified_regime VARCHAR(20),
    PRIMARY KEY (symbol, timeframe, open_time),
    FOREIGN KEY (symbol, timeframe, open_time)
        REFERENCES candles(symbol, timeframe, open_time)
);

-- Index for fast regime queries
CREATE INDEX idx_regime_lookup ON market_regimes(symbol, timeframe, open_time DESC);
CREATE INDEX idx_regime_simplified ON market_regimes(simplified_regime);
```

**When to use:**
- Large datasets (millions of candles)
- Need for historical regime analysis
- API performance critical
- **AI-driven research agents** querying regime data

**Migration Strategy:**
```python
# Backfill script for existing data
def backfill_regimes():
    for symbol, timeframe in get_all_datasets():
        df = storage.get_candles(symbol, timeframe)
        df = add_all_indicators(df)
        regimes = classifier.classify_dataframe(df)
        storage.insert_regimes(regimes)
```

**Recommendation:**
- **Phase 1 (Today):** Option A for MVP
- **Phase 2 (Tomorrow/AI Integration):** Migrate to Option B
  - **Rationale:** AI research agents will need fast, repeated access to regime data
  - Pre-computed storage essential for AI-driven analysis workflows
  - Prepare schema now, implement when AI integration begins

---

## 12. Risk Considerations

### 12.1 No-Lookahead Validation

**Critical:** Ensure regime detection uses ONLY past data

✅ **Safe:**
- Rolling indicators (SMA, EMA, RSI)
- Historical percentiles up to current bar
- Past price comparisons

❌ **Dangerous:**
- Future data in percentile calculation
- Forward-filled indicators
- Peeking ahead in DataFrame

**Mitigation:**
- Explicit iteration bar-by-bar
- Validate with split data tests
- Code review for .shift(-1) or future indexing

### 12.2 Edge Cases

1. **Insufficient data:** Handle gracefully when < min required bars
2. **Missing indicators:** Handle NaN values in regime detection
3. **Extreme values:** Percentile calculation with outliers
4. **Low volatility periods:** Division by zero in normalized metrics

### 12.3 Performance

- **Large datasets:** Consider chunked processing
- **API latency:** Cache regime computations
- **Frontend rendering:** Limit displayed bars if needed

---

## 13. Success Metrics

### 13.1 Technical Validation

- ✅ All indicators calculate without errors
- ✅ No lookahead bias in regime detection
- ✅ API returns data in < 2s for typical dataset
- ✅ Frontend renders smoothly with regime overlay

### 13.2 Functional Validation

- ✅ Trend states align with visual price trends
- ✅ Volatility states reflect ATR/BB behavior
- ✅ Momentum states match oscillator signals
- ✅ Simplified regimes provide actionable categorization

### 13.3 User Experience

- ✅ Regime bars clearly visible on chart
- ✅ Color coding intuitive (green=bullish, red=bearish, etc.)
- ✅ Hover tooltips provide detailed regime info
- ✅ Chart loads quickly even with regime data

---

## 14. Next Steps After Implementation

Once Market Regime Classifier is complete and validated:

### 14.1 Support/Resistance Detection (Future Phase)

As discussed, S/R is complex and should be separate:

**Potential approaches:**
1. **Swing high/low detector:** Identify local peaks/troughs
2. **Psychological levels:** Round numbers (e.g., 100k for BTC)
3. **Historical levels:** All-time highs, previous resistance
4. **Dynamic S/R:** Moving averages as support in trends
5. **Volume-based:** High volume nodes as S/R zones

**Integration with regime:**
- S/R more reliable in RANGE regimes
- Dynamic S/R in TREND regimes
- S/R breaks signal regime transitions

### 14.2 Strategy Enhancement

Leverage regime classification:

```python
# Regime-aware strategy composition
strategies = {
    "TREND_UP": MovingAverageCrossover(),
    "TREND_DOWN": ShortSellStrategy(),
    "RANGE": MeanReversionStrategy(),
    "CHOPPY": StayOut()  # Don't trade
}

# Auto-select strategy by regime
current_regime = regime_classifier.detect(bar)
active_strategy = strategies[current_regime['simplified']]
signal = active_strategy.calculate_signals(bar)
```

### 14.3 Analytics Dashboard

Build regime analytics:
- Regime distribution over time
- Performance by regime
- Regime transition frequency
- Average regime duration

---

## 15. Implementation Decisions (FINALIZED)

✅ **Adaptive threshold window:** 100 periods
✅ **Regime bar height:** Same as volume
✅ **Default view:** Regime shown by default, toggleable hide/show
✅ **Regime legend:** Yes, add color legend
✅ **Database storage:**
   - Phase 1: Compute on-fly
   - Phase 2 (AI integration): Pre-computed storage (Option B)
✅ **Live integration:** Both standalone API + live engine integration
✅ **Playback feature:** Full playback controls (play/pause, speed, scrubber)
   - Purpose: Visualize backtest evolution over time
   - Implementation: lightweight-charts timeScale API

---

## Conclusion

This plan provides a complete roadmap for implementing a sophisticated Market Regime Classifier with:

- ✅ Granular 3D classification (trend/volatility/momentum)
- ✅ Simplified practical mapping (TREND_UP/DOWN/RANGE/CHOPPY)
- ✅ Adaptive thresholds for dynamic markets
- ✅ Event-driven, no-lookahead processing
- ✅ Clean API integration
- ✅ Beautiful TradingView-style visualization

**Estimated total time:** 9-15 hours across 5 phases.

**Key priorities:**
1. ⭐ Live engine integration (regime accessible to strategies)
2. ⭐ Database schema prep for AI integration (future)
3. ⭐ Toggle-able visualization (default ON)
4. 📋 Playback controls (future enhancement)

**Recommendation:** Proceed with phased implementation, validate each phase before moving forward.
