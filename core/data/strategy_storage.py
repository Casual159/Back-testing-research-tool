"""
Strategy Storage - CRUD operations for trading strategies

Handles database operations for strategies table.
Supports both built-in and composite strategies.
"""
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any

import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


@dataclass
class StrategyRecord:
    """Database record for a strategy"""
    id: int
    name: str
    description: str
    strategy_type: str  # 'builtin' | 'composite'
    builtin_class: Optional[str]
    entry_logic: Optional[Dict]
    exit_logic: Optional[Dict]
    parameters: Dict[str, Any]
    regime_filter: Optional[List[str]]
    sub_regime_filter: Optional[Dict]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class StrategyStorage:
    """Storage layer for trading strategies"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize strategy storage

        Args:
            config: Database config with keys: host, port, database, user, password
        """
        self.config = config
        self.conn = None

    def connect(self) -> bool:
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['database'],
                user=self.config['user'],
                password=self.config.get('password', '')
            )
            logger.info("StrategyStorage connected to database")
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False

    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def _ensure_connected(self):
        """Ensure we have a database connection"""
        if not self.conn or self.conn.closed:
            self.connect()

    def _row_to_record(self, row: Dict) -> StrategyRecord:
        """Convert database row to StrategyRecord"""
        return StrategyRecord(
            id=row['id'],
            name=row['name'],
            description=row['description'] or '',
            strategy_type=row['strategy_type'],
            builtin_class=row['builtin_class'],
            entry_logic=row['entry_logic'],
            exit_logic=row['exit_logic'],
            parameters=row['parameters'] or {},
            regime_filter=row['regime_filter'],
            sub_regime_filter=row['sub_regime_filter'],
            is_active=row['is_active'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    # =========================================================================
    # READ Operations
    # =========================================================================

    def list_strategies(self, active_only: bool = True) -> List[StrategyRecord]:
        """
        Get all strategies

        Args:
            active_only: If True, only return active strategies

        Returns:
            List of StrategyRecord objects
        """
        self._ensure_connected()

        query = """
            SELECT id, name, description, strategy_type, builtin_class,
                   entry_logic, exit_logic, parameters, regime_filter,
                   sub_regime_filter, is_active, created_at, updated_at
            FROM strategies
        """
        if active_only:
            query += " WHERE is_active = true"
        query += " ORDER BY name"

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            rows = cur.fetchall()

        return [self._row_to_record(row) for row in rows]

    def get_strategy(self, name: str) -> Optional[StrategyRecord]:
        """
        Get strategy by name

        Args:
            name: Strategy name

        Returns:
            StrategyRecord or None if not found
        """
        self._ensure_connected()

        query = """
            SELECT id, name, description, strategy_type, builtin_class,
                   entry_logic, exit_logic, parameters, regime_filter,
                   sub_regime_filter, is_active, created_at, updated_at
            FROM strategies
            WHERE name = %s AND is_active = true
        """

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (name,))
            row = cur.fetchone()

        return self._row_to_record(row) if row else None

    def get_strategy_by_id(self, strategy_id: int) -> Optional[StrategyRecord]:
        """Get strategy by ID"""
        self._ensure_connected()

        query = """
            SELECT id, name, description, strategy_type, builtin_class,
                   entry_logic, exit_logic, parameters, regime_filter,
                   sub_regime_filter, is_active, created_at, updated_at
            FROM strategies
            WHERE id = %s
        """

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (strategy_id,))
            row = cur.fetchone()

        return self._row_to_record(row) if row else None

    # =========================================================================
    # CREATE Operations
    # =========================================================================

    def create_strategy(
        self,
        name: str,
        description: str,
        strategy_type: str,
        entry_logic: Optional[Dict] = None,
        exit_logic: Optional[Dict] = None,
        parameters: Optional[Dict] = None,
        regime_filter: Optional[List[str]] = None,
        sub_regime_filter: Optional[Dict] = None,
        builtin_class: Optional[str] = None
    ) -> StrategyRecord:
        """
        Create a new strategy

        Args:
            name: Unique strategy name
            description: Strategy description
            strategy_type: 'builtin' or 'composite'
            entry_logic: LogicTree dict for composite strategies
            exit_logic: LogicTree dict for composite strategies
            parameters: Strategy parameters
            regime_filter: List of allowed regimes
            sub_regime_filter: Sub-regime filter dict
            builtin_class: Class name for builtin strategies

        Returns:
            Created StrategyRecord

        Raises:
            ValueError: If strategy with name already exists
        """
        self._ensure_connected()

        # Check if name already exists
        existing = self.get_strategy(name)
        if existing:
            raise ValueError(f"Strategy '{name}' already exists")

        query = """
            INSERT INTO strategies (
                name, description, strategy_type, builtin_class,
                entry_logic, exit_logic, parameters,
                regime_filter, sub_regime_filter
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            RETURNING id, created_at, updated_at
        """

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (
                name,
                description,
                strategy_type,
                builtin_class,
                json.dumps(entry_logic) if entry_logic else None,
                json.dumps(exit_logic) if exit_logic else None,
                json.dumps(parameters or {}),
                regime_filter,
                json.dumps(sub_regime_filter) if sub_regime_filter else None
            ))
            result = cur.fetchone()
            self.conn.commit()

        return StrategyRecord(
            id=result['id'],
            name=name,
            description=description,
            strategy_type=strategy_type,
            builtin_class=builtin_class,
            entry_logic=entry_logic,
            exit_logic=exit_logic,
            parameters=parameters or {},
            regime_filter=regime_filter,
            sub_regime_filter=sub_regime_filter,
            is_active=True,
            created_at=result['created_at'],
            updated_at=result['updated_at']
        )

    # =========================================================================
    # UPDATE Operations
    # =========================================================================

    def update_strategy(
        self,
        name: str,
        updates: Dict[str, Any]
    ) -> Optional[StrategyRecord]:
        """
        Update an existing strategy

        Args:
            name: Strategy name to update
            updates: Dict of fields to update

        Returns:
            Updated StrategyRecord or None if not found
        """
        self._ensure_connected()

        # Get existing strategy
        existing = self.get_strategy(name)
        if not existing:
            return None

        # Build update query dynamically
        allowed_fields = [
            'description', 'parameters', 'regime_filter',
            'sub_regime_filter', 'entry_logic', 'exit_logic'
        ]

        set_clauses = []
        values = []

        for field_name, value in updates.items():
            if field_name in allowed_fields:
                set_clauses.append(f"{field_name} = %s")
                # JSON encode dict/list values
                if isinstance(value, (dict, list)) and field_name != 'regime_filter':
                    values.append(json.dumps(value))
                else:
                    values.append(value)

        if not set_clauses:
            return existing

        set_clauses.append("updated_at = NOW()")
        values.append(name)

        query = f"""
            UPDATE strategies
            SET {', '.join(set_clauses)}
            WHERE name = %s
            RETURNING id
        """

        with self.conn.cursor() as cur:
            cur.execute(query, values)
            self.conn.commit()

        return self.get_strategy(name)

    # =========================================================================
    # DELETE Operations
    # =========================================================================

    def delete_strategy(self, name: str, hard_delete: bool = False) -> bool:
        """
        Delete a strategy (soft delete by default)

        Args:
            name: Strategy name to delete
            hard_delete: If True, permanently delete; else set is_active=false

        Returns:
            True if deleted, False if not found
        """
        self._ensure_connected()

        if hard_delete:
            query = "DELETE FROM strategies WHERE name = %s RETURNING id"
        else:
            query = "UPDATE strategies SET is_active = false, updated_at = NOW() WHERE name = %s RETURNING id"

        with self.conn.cursor() as cur:
            cur.execute(query, (name,))
            result = cur.fetchone()
            self.conn.commit()

        return result is not None

    # =========================================================================
    # Strategy Instantiation
    # =========================================================================

    def instantiate_strategy(self, record: StrategyRecord, override_params: Optional[Dict] = None):
        """
        Convert StrategyRecord to actual Strategy object

        Args:
            record: StrategyRecord from database
            override_params: Optional parameter overrides

        Returns:
            Strategy instance ready for backtesting
        """
        params = {**record.parameters}
        if override_params:
            params.update(override_params)

        if record.strategy_type == 'builtin':
            return self._instantiate_builtin(record, params)
        elif record.strategy_type == 'composite':
            return self._instantiate_composite(record, params)
        else:
            raise ValueError(f"Unknown strategy type: {record.strategy_type}")

    def _instantiate_builtin(self, record: StrategyRecord, params: Dict):
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

        cls = class_map.get(record.builtin_class)
        if not cls:
            raise ValueError(f"Unknown builtin class: {record.builtin_class}")

        return cls(**params)

    def _instantiate_composite(self, record: StrategyRecord, params: Dict):
        """Create composite strategy from JSON logic"""
        from core.backtest.strategies.composition import (
            CompositeStrategy, LogicTree
        )

        if not record.entry_logic or not record.exit_logic:
            raise ValueError("Composite strategy requires entry_logic and exit_logic")

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

    # =========================================================================
    # Backtest Results
    # =========================================================================

    def save_backtest_result(
        self,
        strategy_name: str,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float,
        metrics: Dict[str, Any],
        equity_curve: List,
        trades: List,
        config: Optional[Dict] = None,
        regime_stats: Optional[Dict] = None
    ) -> int:
        """
        Save backtest results to database

        Returns:
            ID of created backtest_results record
        """
        self._ensure_connected()

        # Get strategy ID
        strategy = self.get_strategy(strategy_name)
        strategy_id = strategy.id if strategy else None

        config = config or {}

        query = """
            INSERT INTO backtest_results (
                strategy_id, strategy_name, symbol, timeframe,
                start_date, end_date, initial_capital,
                commission_rate, slippage_rate, position_size_pct,
                total_return_pct, sharpe_ratio, max_drawdown_pct,
                win_rate_pct, total_trades, profit_factor,
                avg_trade_duration_hours, equity_curve, trades, regime_stats
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            RETURNING id
        """

        with self.conn.cursor() as cur:
            cur.execute(query, (
                strategy_id,
                strategy_name,
                symbol,
                timeframe,
                start_date,
                end_date,
                initial_capital,
                config.get('commission_rate'),
                config.get('slippage_rate'),
                config.get('position_size_pct'),
                metrics.get('total_return'),
                metrics.get('sharpe_ratio'),
                metrics.get('max_drawdown'),
                metrics.get('win_rate'),
                metrics.get('total_trades'),
                metrics.get('profit_factor'),
                metrics.get('avg_trade_duration_hours'),
                json.dumps(equity_curve),
                json.dumps(trades),
                json.dumps(regime_stats) if regime_stats else None
            ))
            result = cur.fetchone()
            self.conn.commit()

        return result[0]

    def get_backtest_results(
        self,
        strategy_name: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """Get recent backtest results"""
        self._ensure_connected()

        query = """
            SELECT id, strategy_name, symbol, timeframe,
                   start_date, end_date, initial_capital,
                   total_return_pct, sharpe_ratio, max_drawdown_pct,
                   win_rate_pct, total_trades, profit_factor,
                   created_at
            FROM backtest_results
        """

        params = []
        if strategy_name:
            query += " WHERE strategy_name = %s"
            params.append(strategy_name)

        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchall()
