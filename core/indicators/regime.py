"""
Market Regime Classifier

Detects market regimes based on 3D classification:
- Trend State: uptrend | downtrend | neutral
- Volatility State: low | high
- Momentum State: bullish | bearish | weak

Uses adaptive thresholds and event-driven processing (no lookahead bias).
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class RegimeConfig:
    """Configuration for regime detection thresholds"""
    # Trend detection
    adx_trending_threshold: float = 25.0
    adx_sideways_threshold: float = 20.0

    # Volatility detection
    adaptive_window: int = 100
    vol_low_percentile: int = 30
    vol_high_percentile: int = 70

    # Momentum scoring
    rsi_bullish_threshold: float = 55.0
    rsi_bearish_threshold: float = 45.0
    momentum_score_threshold: int = 2


class AdaptiveThresholds:
    """
    Calculate and maintain rolling percentile thresholds
    for volatility detection using event-driven processing.
    """

    def __init__(self, window: int = 100):
        """
        Initialize adaptive thresholds calculator

        Args:
            window: Rolling window size for percentile calculation
        """
        self.window = window
        self.atr_buffer = []
        self.boll_width_buffer = []

    def update(self, atr_normalized: float, boll_width: float):
        """
        Update buffers with new values (event-driven)

        Args:
            atr_normalized: Normalized ATR (ATR / close)
            boll_width: Bollinger band width normalized
        """
        self.atr_buffer.append(atr_normalized)
        self.boll_width_buffer.append(boll_width)

        # Keep only last window periods (no lookahead)
        if len(self.atr_buffer) > self.window:
            self.atr_buffer.pop(0)
            self.boll_width_buffer.pop(0)

    def get_thresholds(self, config: RegimeConfig) -> Dict[str, float]:
        """
        Calculate current percentile thresholds from historical data

        Args:
            config: Regime configuration with percentile settings

        Returns:
            Dict with atr_p30, atr_p70, boll_p30, boll_p70
        """
        # Need minimum data for reliable percentiles
        if len(self.atr_buffer) < min(self.window // 2, 30):
            # Not enough data - return conservative defaults
            return {
                "atr_p30": 0.005,   # 0.5% of price
                "atr_p70": 0.015,   # 1.5% of price
                "boll_p30": 0.02,   # 2% band width
                "boll_p70": 0.06    # 6% band width
            }

        return {
            "atr_p30": np.percentile(self.atr_buffer, config.vol_low_percentile),
            "atr_p70": np.percentile(self.atr_buffer, config.vol_high_percentile),
            "boll_p30": np.percentile(self.boll_width_buffer, config.vol_low_percentile),
            "boll_p70": np.percentile(self.boll_width_buffer, config.vol_high_percentile)
        }

    def has_sufficient_data(self) -> bool:
        """Check if we have enough data for reliable thresholds"""
        return len(self.atr_buffer) >= min(self.window // 2, 30)


class MarketRegimeClassifier:
    """
    Market Regime Classifier with 3D granular classification
    and simplified practical mapping.

    Uses event-driven processing to ensure no lookahead bias.
    """

    def __init__(self, config: Optional[RegimeConfig] = None):
        """
        Initialize regime classifier

        Args:
            config: Configuration for thresholds (uses defaults if None)
        """
        self.config = config or RegimeConfig()
        self.adaptive_thresholds = AdaptiveThresholds(self.config.adaptive_window)

    def detect_trend_state(self, row: pd.Series) -> str:
        """
        Detect trend state: uptrend | downtrend | neutral

        Logic:
        1. IF ADX < 20 → neutral (sideways, weak trend)
        2. ELSE IF ADX >= 25:
           - IF close > SMA50 AND SMA50 > SMA200 → uptrend
           - IF close < SMA50 AND SMA50 < SMA200 → downtrend
           - ELSE → neutral
        3. Check SMA20/SMA50 cross for emerging trends

        Args:
            row: DataFrame row with required indicators

        Returns:
            "uptrend" | "downtrend" | "neutral"
        """
        adx = row.get('adx')
        close = row.get('close')
        sma_20 = row.get('sma_20')
        sma_50 = row.get('sma_50')
        sma_200 = row.get('sma_200')

        # Handle missing data
        if pd.isna(adx) or pd.isna(close) or pd.isna(sma_50):
            return "neutral"

        # Weak trend → neutral
        if adx < self.config.adx_sideways_threshold:
            return "neutral"

        # Strong trend → check direction
        if adx >= self.config.adx_trending_threshold:
            # Check if we have SMA200 for long-term trend
            if not pd.isna(sma_200):
                # Classic trend definition
                if close > sma_50 and sma_50 > sma_200:
                    return "uptrend"
                elif close < sma_50 and sma_50 < sma_200:
                    return "downtrend"
            else:
                # Fallback: use close vs SMA50 only
                if close > sma_50:
                    return "uptrend"
                elif close < sma_50:
                    return "downtrend"

        # Between thresholds or ambiguous → neutral
        return "neutral"

    def detect_volatility_state(
        self,
        row: pd.Series,
        thresholds: Dict[str, float]
    ) -> str:
        """
        Detect volatility state: low | high

        Logic:
        1. normalized_vol = ATR / close
        2. boll_width = (bb_upper - bb_lower) / bb_middle
        3. Use adaptive percentile thresholds

        IF normalized_vol < p30 AND boll_width < p30 → low
        ELIF normalized_vol > p70 OR boll_width > p70 → high
        ELSE → low (default unless strong signal)

        Args:
            row: DataFrame row with required indicators
            thresholds: Adaptive percentile thresholds

        Returns:
            "low" | "high"
        """
        atr = row.get('atr')
        close = row.get('close')
        bb_upper = row.get('bb_upper')
        bb_middle = row.get('bb_middle')
        bb_lower = row.get('bb_lower')

        # Handle missing data
        if pd.isna(atr) or pd.isna(close) or close == 0:
            return "low"  # Default to low volatility

        if pd.isna(bb_upper) or pd.isna(bb_middle) or pd.isna(bb_lower):
            return "low"

        # Calculate normalized volatility metrics
        normalized_atr = atr / close

        # Bollinger band width (avoid division by zero)
        if bb_middle == 0:
            boll_width = 0
        else:
            boll_width = (bb_upper - bb_lower) / bb_middle

        # Update adaptive thresholds (event-driven)
        self.adaptive_thresholds.update(normalized_atr, boll_width)

        # Classify volatility
        atr_p30 = thresholds.get('atr_p30', 0.005)
        atr_p70 = thresholds.get('atr_p70', 0.015)
        boll_p30 = thresholds.get('boll_p30', 0.02)
        boll_p70 = thresholds.get('boll_p70', 0.06)

        # High volatility if either metric exceeds 70th percentile
        if normalized_atr > atr_p70 or boll_width > boll_p70:
            return "high"

        # Low volatility if both metrics below 30th percentile
        if normalized_atr < atr_p30 and boll_width < boll_p30:
            return "low"

        # Default to low unless strong high volatility signal
        return "low"

    def detect_momentum_state(self, row: pd.Series) -> str:
        """
        Detect momentum state: bullish | bearish | weak

        Scoring System:
        bullish_score += 1 if ROC > 0
        bullish_score += 1 if MACD_histogram > 0
        bullish_score += 1 if RSI > 55

        bearish_score += 1 if ROC < 0
        bearish_score += 1 if MACD_histogram < 0
        bearish_score += 1 if RSI < 45

        IF bullish_score >= 2 → bullish
        ELIF bearish_score >= 2 → bearish
        ELSE → weak

        Args:
            row: DataFrame row with required indicators

        Returns:
            "bullish" | "bearish" | "weak"
        """
        roc = row.get('roc')
        macd_hist = row.get('macd_histogram')
        rsi = row.get('rsi')

        # Handle missing data
        if pd.isna(roc) or pd.isna(macd_hist) or pd.isna(rsi):
            return "weak"

        bullish_score = 0
        bearish_score = 0

        # ROC scoring
        if roc > 0:
            bullish_score += 1
        elif roc < 0:
            bearish_score += 1

        # MACD histogram scoring
        if macd_hist > 0:
            bullish_score += 1
        elif macd_hist < 0:
            bearish_score += 1

        # RSI scoring
        if rsi > self.config.rsi_bullish_threshold:
            bullish_score += 1
        elif rsi < self.config.rsi_bearish_threshold:
            bearish_score += 1

        # Determine momentum state
        threshold = self.config.momentum_score_threshold

        if bullish_score >= threshold:
            return "bullish"
        elif bearish_score >= threshold:
            return "bearish"
        else:
            return "weak"

    def map_to_simplified_regime(
        self,
        trend: str,
        volatility: str,
        momentum: str
    ) -> str:
        """
        Map granular regime to simplified practical trading regime

        Returns: TREND_UP | TREND_DOWN | RANGE | CHOPPY | NEUTRAL

        Logic (priority order):
        1. TREND_UP: Uptrend + bullish momentum
        2. TREND_DOWN: Downtrend + bearish momentum
        3. CHOPPY: High volatility + weak momentum + neutral trend
        4. RANGE: Neutral trend + low volatility
        5. NEUTRAL: Everything else

        Args:
            trend: Trend state
            volatility: Volatility state
            momentum: Momentum state

        Returns:
            Simplified regime string
        """
        # Priority 1: Strong trends with momentum (highest confidence)
        if trend == "uptrend" and momentum == "bullish":
            return "TREND_UP"

        if trend == "downtrend" and momentum == "bearish":
            return "TREND_DOWN"

        # Priority 2: CHOPPY - High volatility + weak momentum + NO clear trend
        if volatility == "high" and momentum == "weak" and trend == "neutral":
            return "CHOPPY"

        # Priority 3: RANGE - Neutral trend + low volatility
        if trend == "neutral" and volatility == "low":
            return "RANGE"

        # Default: Everything else
        return "NEUTRAL"

    def calculate_confidence(
        self,
        row: pd.Series,
        trend: str,
        momentum: str
    ) -> float:
        """
        Calculate confidence score for regime classification (0.0 - 1.0)

        Higher confidence when:
        - Strong ADX (clear trend)
        - Momentum aligns with trend
        - Indicators are not missing/NaN

        Args:
            row: DataFrame row with indicators
            trend: Detected trend state
            momentum: Detected momentum state

        Returns:
            Confidence score 0.0 (low) to 1.0 (high)
        """
        confidence = 0.5  # Base confidence

        adx = row.get('adx', 0)
        rsi = row.get('rsi')
        macd_hist = row.get('macd_histogram')

        # Boost confidence for strong trend
        if not pd.isna(adx):
            if adx > 40:
                confidence += 0.3  # Very strong trend
            elif adx > self.config.adx_trending_threshold:
                confidence += 0.15  # Strong trend
            elif adx < self.config.adx_sideways_threshold:
                confidence -= 0.1  # Weak/unclear trend

        # Boost confidence when momentum aligns with trend
        if trend == "uptrend" and momentum == "bullish":
            confidence += 0.2
        elif trend == "downtrend" and momentum == "bearish":
            confidence += 0.2
        elif trend != "neutral" and momentum == "weak":
            confidence -= 0.1  # Conflicting signals

        # Penalize missing indicators
        missing_count = sum([
            pd.isna(rsi),
            pd.isna(macd_hist),
            pd.isna(adx)
        ])
        confidence -= missing_count * 0.1

        # Clamp to [0, 1]
        return max(0.0, min(1.0, confidence))

    def detect_regime(self, row: pd.Series) -> Dict[str, str]:
        """
        Main entry point - detect market regime for a single bar

        Returns comprehensive regime analysis:
        {
            "trend_state": "uptrend",
            "volatility_state": "low",
            "momentum_state": "bullish",
            "full_regime": "UPTREND_LOWVOL_BULLISH",
            "simplified": "TREND_UP",
            "confidence": 0.85
        }

        Args:
            row: DataFrame row with all required indicators

        Returns:
            Dict with regime classification and confidence score
        """
        # Get adaptive thresholds
        thresholds = self.adaptive_thresholds.get_thresholds(self.config)

        # Detect 3D regime components
        trend = self.detect_trend_state(row)
        volatility = self.detect_volatility_state(row, thresholds)
        momentum = self.detect_momentum_state(row)

        # Calculate confidence score
        confidence = self.calculate_confidence(row, trend, momentum)

        # Create composite regime string
        full_regime = f"{trend.upper()}_{volatility.upper()}VOL_{momentum.upper()}MOM"

        # Map to simplified regime
        simplified = self.map_to_simplified_regime(trend, volatility, momentum)

        return {
            "trend_state": trend,
            "volatility_state": volatility,
            "momentum_state": momentum,
            "full_regime": full_regime,
            "simplified": simplified,
            "confidence": confidence
        }

    def classify_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Classify market regime for entire dataframe (event-driven processing)

        IMPORTANT: Processes bars chronologically to maintain no-lookahead bias.
        Adaptive thresholds are built up as we iterate through data.

        Args:
            df: DataFrame with all required indicators

        Returns:
            DataFrame with added regime columns
        """
        result = df.copy()

        # Initialize regime columns
        regimes = []

        # Process each bar chronologically (event-driven)
        for idx, row in result.iterrows():
            regime = self.detect_regime(row)
            regimes.append(regime)

        # Convert to DataFrame for easy joining
        regime_df = pd.DataFrame(regimes, index=result.index)

        # Add regime columns to result
        result['trend_state'] = regime_df['trend_state']
        result['volatility_state'] = regime_df['volatility_state']
        result['momentum_state'] = regime_df['momentum_state']
        result['full_regime'] = regime_df['full_regime']
        result['simplified_regime'] = regime_df['simplified']
        result['regime_confidence'] = regime_df['confidence']

        return result


# Convenience function for quick regime detection
def detect_market_regimes(
    df: pd.DataFrame,
    config: Optional[RegimeConfig] = None
) -> pd.DataFrame:
    """
    Convenience function to detect market regimes on a dataframe

    Args:
        df: DataFrame with all required indicators
        config: Optional custom configuration

    Returns:
        DataFrame with added regime columns
    """
    classifier = MarketRegimeClassifier(config)
    return classifier.classify_dataframe(df)
