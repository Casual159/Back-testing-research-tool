#!/usr/bin/env python3
"""Test the regime API endpoint"""
import requests
import json
from collections import Counter

# Fetch regime data
response = requests.get("http://localhost:8000/api/data/regime/BTCUSDT/1h")
data = response.json()

print(f"Total candles: {len(data)}")
print(f"Date range: {data[0]['time']} to {data[-1]['time']}")
print()

# Count regime distribution
regime_counts = Counter(d['regime'] for d in data)
print("Regime Distribution:")
for regime, count in regime_counts.most_common():
    pct = (count / len(data)) * 100
    print(f"  {regime}: {count} ({pct:.1f}%)")

print()
print("Last 5 regimes:")
for d in data[-5:]:
    print(f"  {d['regime']:12s} | {d['full_regime']:30s} | confidence: {d['confidence']:.2f} | color: {d['color']}")

print()
print("Sample regime types found:")
seen_regimes = set()
for d in data:
    regime = d['regime']
    if regime not in seen_regimes:
        seen_regimes.add(regime)
        print(f"  ✅ {regime:12s} - {d['full_regime']:30s} - {d['color']}")
        if len(seen_regimes) >= 5:
            break
