#!/usr/bin/env python3
"""
Backfill market regime data for all existing candle data.

This script:
1. Fetches all candles for each symbol/timeframe
2. Calculates regime classifications
3. Stores pre-computed regimes in database for fast AI queries
"""
import sys
sys.path.insert(0, '/Users/jakub/Back-testing-research-tool')

from core.data.storage import PostgresStorage
from core.indicators.technical import add_all_indicators
from core.indicators.regime import MarketRegimeClassifier
from config.config import load_config


def backfill_regimes(symbol: str, timeframe: str, storage: PostgresStorage):
    """Backfill regime data for a single symbol/timeframe"""
    print(f"\n{'='*70}")
    print(f"Processing: {symbol} {timeframe}")
    print(f"{'='*70}")

    # 1. Check if regimes already exist
    if storage.has_regimes(symbol, timeframe):
        print(f"⚠️  Regimes already exist for {symbol} {timeframe} - overwriting...")
        # Delete existing regimes
        deleted = storage.delete_regimes(symbol, timeframe)
        print(f"   Deleted {deleted} existing regime records")

    # 2. Fetch candle data
    print(f"\n1. Fetching candle data...")
    df = storage.get_candles(symbol, timeframe)
    print(f"   ✓ Loaded {len(df)} candles")

    if len(df) == 0:
        print(f"   ✗ No candle data found, skipping")
        return

    # 3. Add technical indicators
    print(f"\n2. Calculating technical indicators...")
    df = add_all_indicators(df)
    print(f"   ✓ Indicators calculated")

    # 4. Classify regimes
    print(f"\n3. Classifying market regimes...")
    classifier = MarketRegimeClassifier()
    regimes_df = classifier.classify_dataframe(df)
    print(f"   ✓ Regimes classified")

    # Show regime distribution
    regime_dist = regimes_df['simplified_regime'].value_counts()
    print(f"\n   Regime distribution:")
    for regime, count in regime_dist.items():
        pct = (count / len(regimes_df)) * 100
        print(f"     {regime:<15} {count:>6} ({pct:>5.1f}%)")

    avg_confidence = regimes_df['regime_confidence'].mean()
    print(f"\n   Average confidence: {avg_confidence:.2%}")

    # 5. Store in database
    print(f"\n4. Storing regime data...")
    inserted = storage.insert_regimes(symbol, timeframe, regimes_df)
    print(f"   ✓ Inserted {inserted} regime records")

    print(f"\n{'='*70}")
    print(f"✅ Completed: {symbol} {timeframe}")
    print(f"{'='*70}")


def backfill_all(auto_confirm: bool = False):
    """Backfill regime data for all available datasets"""
    print("="*70)
    print("MARKET REGIME BACKFILL")
    print("="*70)
    print("\nThis will calculate and store regime data for all available")
    print("candle datasets. This enables fast AI-driven queries.")
    print()

    # Load config
    config = load_config()

    # Get list of symbols/timeframes to process
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    timeframes = ['1h', '4h', '1d']

    print(f"Symbols: {', '.join(symbols)}")
    print(f"Timeframes: {', '.join(timeframes)}")
    print(f"Total datasets: {len(symbols) * len(timeframes)}")
    print()

    if not auto_confirm:
        response = input("Proceed with backfill? (y/n): ")
        if response.lower() != 'y':
            print("Aborted.")
            return
    else:
        print("Auto-confirm enabled, proceeding...")

    # Process each dataset
    with PostgresStorage(config['database']) as storage:
        total_processed = 0

        for symbol in symbols:
            for timeframe in timeframes:
                try:
                    backfill_regimes(symbol, timeframe, storage)
                    total_processed += 1
                except Exception as e:
                    print(f"\n✗ ERROR processing {symbol} {timeframe}: {e}")
                    import traceback
                    traceback.print_exc()
                    continue

        # Final summary
        print("\n" + "="*70)
        print("BACKFILL COMPLETE")
        print("="*70)
        print(f"\nDatasets processed: {total_processed}/{len(symbols) * len(timeframes)}")

        # Show regime stats
        print("\nRegime data statistics:")
        print("-"*70)
        stats = storage.get_regime_stats()
        for _, row in stats.iterrows():
            print(f"\n{row['symbol']} {row['timeframe']}")
            print(f"  Records:     {row['regime_count']:,}")
            print(f"  Range:       {row['first_regime']} -> {row['last_regime']}")
            print(f"  Avg conf:    {row['avg_confidence']:.2%}")
            print(f"  Version:     {row['classifier_version']}")

        print("\n" + "="*70)


if __name__ == '__main__':
    import sys
    auto_confirm = '--yes' in sys.argv or '-y' in sys.argv
    backfill_all(auto_confirm=auto_confirm)
