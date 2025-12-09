"""
Backtesting engine - core event loop and order execution.

The engine processes market data chronologically, generates trading signals,
executes orders, and tracks portfolio performance.
"""

from datetime import datetime
from typing import Optional, Dict, Any
import pandas as pd
from .events import MarketEvent, SignalEvent, OrderEvent, FillEvent
from .portfolio import Portfolio
from core.indicators.regime import MarketRegimeClassifier
from core.indicators.technical import add_all_indicators


class BacktestEngine:
    """
    Event-driven backtesting engine.

    Processes data chronologically to prevent look-ahead bias:
    1. Read next bar -> MarketEvent
    2. Strategy evaluates -> SignalEvent
    3. Portfolio generates -> OrderEvent
    4. Execute order -> FillEvent
    5. Update portfolio -> Record equity

    Attributes:
        data: Historical OHLCV data (pandas DataFrame)
        strategy: Trading strategy instance
        portfolio: Portfolio manager
        commission_rate: Trading fee (as decimal, e.g., 0.001 = 0.1%)
        slippage_rate: Price impact (as decimal, e.g., 0.0005 = 0.05%)
        initial_capital: Starting cash
    """

    def __init__(
        self,
        data: pd.DataFrame,
        strategy,
        initial_capital: float = 10000.0,
        commission_rate: float = 0.001,
        slippage_rate: float = 0.0005,
        position_size_pct: float = 1.0,
        enable_regime_detection: bool = True
    ):
        """
        Initialize backtesting engine.

        Args:
            data: DataFrame with OHLCV columns and datetime index
            strategy: Strategy instance implementing calculate_signals()
            initial_capital: Starting portfolio value
            commission_rate: Trading fee as decimal (0.001 = 0.1%)
            slippage_rate: Price impact as decimal (0.0005 = 0.05%)
            position_size_pct: Fraction of capital to use per trade (0.0 to 1.0)
            enable_regime_detection: Enable market regime classification (default: True)
        """
        self.data = data
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        self.position_size_pct = max(0.0, min(1.0, position_size_pct))
        self.enable_regime_detection = enable_regime_detection

        self.portfolio = Portfolio(initial_capital)
        self.symbol = 'BTC/USDT'  # Default symbol

        # Regime classifier
        self.regime_classifier = None
        self.data_with_indicators = None
        if self.enable_regime_detection:
            self._prepare_regime_data()

        # Statistics
        self.bars_processed = 0
        self.signals_generated = 0
        self.orders_executed = 0

    def run(self) -> Dict[str, Any]:
        """
        Run backtest on historical data.

        Returns:
            Dict containing:
                - portfolio: Portfolio instance with full history
                - metrics: Performance metrics dictionary
                - equity_curve: List of (timestamp, value) tuples
                - trades: List of Trade objects
        """
        print(f"Starting backtest with {len(self.data)} bars...")
        print(f"Initial capital: ${self.initial_capital:,.2f}")
        print(f"Commission: {self.commission_rate*100:.2f}%, Slippage: {self.slippage_rate*100:.2f}%")
        print("-" * 60)

        # Initialize strategy if it has an initialize method (for CompositeStrategy)
        if hasattr(self.strategy, 'initialize'):
            print("Initializing strategy...")
            self.strategy.initialize(self.data)
            print("Strategy initialized!")
            print("-" * 60)

        # Main event loop - process each bar chronologically
        for timestamp, bar in self.data.iterrows():
            self.bars_processed += 1

            # 1. Create MarketEvent
            market_event = self._create_market_event(timestamp, bar)

            # 2. Strategy generates signal
            signal_event = self._generate_signal(market_event)

            # 3. Process signal � Order � Fill
            if signal_event:
                self._process_signal(signal_event, bar)

            # 4. Record portfolio value
            current_price = bar['close']
            portfolio_value = self.portfolio.current_value({self.symbol: current_price})
            self.portfolio.record_equity(timestamp, portfolio_value)

        # Backtest complete
        print("-" * 60)
        print(f"Backtest complete!")
        print(f"Bars processed: {self.bars_processed}")
        print(f"Signals generated: {self.signals_generated}")
        print(f"Orders executed: {self.orders_executed}")
        print(f"Total trades: {self.portfolio.total_trades()}")

        # Calculate metrics
        from .metrics import MetricsCalculator
        metrics_calc = MetricsCalculator(self.portfolio)
        metrics = metrics_calc.calculate_all()

        return {
            'portfolio': self.portfolio,
            'metrics': metrics,
            'equity_curve': self.portfolio.equity_curve,
            'trades': self.portfolio.trades
        }

    def _prepare_regime_data(self):
        """
        Prepare data with indicators and regime classification.
        Called during initialization if regime detection is enabled.
        """
        print("Preparing regime data...")
        # Add all technical indicators
        self.data_with_indicators = add_all_indicators(self.data.copy())

        # Initialize regime classifier
        self.regime_classifier = MarketRegimeClassifier()

        # Classify regimes for entire dataset
        self.data_with_indicators = self.regime_classifier.classify_dataframe(
            self.data_with_indicators
        )
        print(f"Regime data prepared ({len(self.data_with_indicators)} bars)")

    def _create_market_event(self, timestamp: datetime, bar: pd.Series) -> MarketEvent:
        """
        Create MarketEvent from data bar.

        Args:
            timestamp: Bar timestamp
            bar: Series with OHLCV data

        Returns:
            MarketEvent instance with regime metadata (if enabled)
        """
        ohlcv = {
            'open': float(bar['open']),
            'high': float(bar['high']),
            'low': float(bar['low']),
            'close': float(bar['close']),
            'volume': float(bar['volume'])
        }

        metadata = {}

        # Add regime data if available
        if self.enable_regime_detection and self.data_with_indicators is not None:
            try:
                # Get regime data for this timestamp from preprocessed DataFrame
                regime_row = self.data_with_indicators.loc[timestamp]
                metadata['regime'] = {
                    'simplified': regime_row.get('simplified_regime'),
                    'full_regime': regime_row.get('full_regime'),
                    'trend_state': regime_row.get('trend_state'),
                    'volatility_state': regime_row.get('volatility_state'),
                    'momentum_state': regime_row.get('momentum_state'),
                    'confidence': regime_row.get('regime_confidence', 0.0)
                }
            except (KeyError, AttributeError):
                # Regime data not available for this bar
                pass

        return MarketEvent(timestamp, self.symbol, ohlcv, metadata)

    def _generate_signal(self, market_event: MarketEvent) -> Optional[SignalEvent]:
        """
        Let strategy evaluate market data and generate signal.

        Args:
            market_event: New market data

        Returns:
            SignalEvent or None if no signal
        """
        # Add market data to strategy's buffer
        self.strategy.add_market_data(market_event)

        # Calculate signals
        signal = self.strategy.calculate_signals(market_event)

        if signal and signal.signal_type != 'HOLD':
            self.signals_generated += 1

        return signal

    def _process_signal(self, signal: SignalEvent, bar: pd.Series):
        """
        Convert signal to order and execute.

        Args:
            signal: SignalEvent from strategy
            bar: Current price bar
        """
        current_price = bar['close']

        if signal.signal_type == 'BUY':
            # Check if we already have a position
            if not self.portfolio.has_position(self.symbol):
                # Calculate position size
                order = self._create_buy_order(signal, current_price)
                if order:
                    fill = self._execute_order(order, current_price)
                    self.portfolio.update_from_fill(fill, current_price)
                    self.orders_executed += 1

        elif signal.signal_type == 'SELL':
            # Check if we have a position to sell
            if self.portfolio.has_position(self.symbol):
                order = self._create_sell_order(signal, current_price)
                if order:
                    fill = self._execute_order(order, current_price)
                    self.portfolio.update_from_fill(fill, current_price)
                    self.orders_executed += 1

    def _create_buy_order(self, signal: SignalEvent, current_price: float) -> Optional[OrderEvent]:
        """
        Create buy order based on signal.

        Args:
            signal: Buy signal
            current_price: Current market price

        Returns:
            OrderEvent or None if insufficient capital
        """
        # Calculate quantity based on available capital
        available_capital = self.portfolio.current_cash * self.position_size_pct

        # Account for commission
        max_cost = available_capital / (1 + self.commission_rate)
        quantity = max_cost / current_price

        if quantity > 0:
            return OrderEvent(
                timestamp=signal.timestamp,
                symbol=signal.symbol,
                order_type='MARKET',
                quantity=quantity,
                direction='BUY'
            )
        return None

    def _create_sell_order(self, signal: SignalEvent, current_price: float) -> Optional[OrderEvent]:
        """
        Create sell order based on signal.

        Args:
            signal: Sell signal
            current_price: Current market price

        Returns:
            OrderEvent or None if no position
        """
        position = self.portfolio.get_position(signal.symbol)
        if position and position.quantity > 0:
            return OrderEvent(
                timestamp=signal.timestamp,
                symbol=signal.symbol,
                order_type='MARKET',
                quantity=position.quantity,
                direction='SELL'
            )
        return None

    def _execute_order(self, order: OrderEvent, market_price: float) -> FillEvent:
        """
        Execute order with slippage and commission.

        Args:
            order: OrderEvent to execute
            market_price: Current market price

        Returns:
            FillEvent with execution details
        """
        # Apply slippage
        if order.direction == 'BUY':
            # Buy at higher price (unfavorable slippage)
            fill_price = market_price * (1 + self.slippage_rate)
        else:
            # Sell at lower price (unfavorable slippage)
            fill_price = market_price * (1 - self.slippage_rate)

        # Calculate commission
        trade_value = order.quantity * fill_price
        commission = trade_value * self.commission_rate

        return FillEvent(
            timestamp=order.timestamp,
            symbol=order.symbol,
            quantity=order.quantity,
            direction=order.direction,
            fill_price=fill_price,
            commission=commission,
            slippage=self.slippage_rate
        )

    def get_summary(self) -> str:
        """Get backtest summary as formatted string."""
        final_value = self.portfolio.equity_curve[-1][1] if self.portfolio.equity_curve else self.initial_capital
        total_return = self.portfolio.total_return()

        summary = f"""
Backtest Summary
================
Initial Capital: ${self.initial_capital:,.2f}
Final Value:     ${final_value:,.2f}
Total Return:    {total_return:.2f}%

Trades:          {self.portfolio.total_trades()}
Win Rate:        {self.portfolio.win_rate():.2f}%
Winning Trades:  {len(self.portfolio.winning_trades())}
Losing Trades:   {len(self.portfolio.losing_trades())}

Bars Processed:  {self.bars_processed}
Signals:         {self.signals_generated}
Orders:          {self.orders_executed}
        """
        return summary
