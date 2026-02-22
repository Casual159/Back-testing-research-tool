# Footprint Scalping - Ideas & Considerations

**Status:** 💡 Discussion Phase
**Created:** 2025-11-08
**Priority:** Future Consideration

---

## 📝 Overview

Footprint scalping je trading approach založený na analýze **order flow** - sledování skutečných objednávek na trhu (bid/ask, volume profiling, trade aggression).

## 🎯 Klíčové koncepty

### 1. **Footprint Charts**
- Zobrazují volume na jednotlivých price levelech
- Rozlišují buying vs selling pressure
- Delta (buy volume - sell volume) na každém levelu

### 2. **Order Flow Analysis**
- Aggressor identification (kdo inicioval obchod - buyer/seller)
- Volume clustering na klíčových levelech
- Imbalance detection (náhlé změny v order flow)

### 3. **Market Microstructure**
- Bid/Ask spread analysis
- Order book depth
- Liquidity pockets

## 🤔 Otázky k diskusi

### Data Requirements
- [ ] Máme přístup k trade-by-trade datům z Binance?
- [ ] Potřebujeme historical order book snapshots?
- [ ] Jaká je granularita dat (tick data)?
- [ ] Kolik storage to bude požadovat?

### Technical Challenges
- [ ] Real-time processing order flow dat
- [ ] Footprint chart visualization (custom charting)
- [ ] Integration s existujícím backtesting frameworkem
- [ ] Latency requirements

### Strategy Ideas
- [ ] Volume imbalance scalping (high buy/sell pressure asymmetry)
- [ ] Support/Resistance level confirmation (volume clustering)
- [ ] Iceberg order detection (hidden liquidity)
- [ ] Stop hunt identification (sharp volume spikes)

## 📊 Data Sources

### Binance API
- **Trades endpoint** (`/api/v3/trades`) - Recent trades
- **AggTrades endpoint** (`/api/v3/aggTrades`) - Aggregated trades
- **Order Book Depth** (`/api/v3/depth`) - Current order book
- **WebSocket Streams** - Real-time trade/depth updates

### Binance Public Data
- Historical trades (tick data)
- Order book snapshots (limited availability)

## 🚧 Implementation Considerations

### Phase 1: Research & Feasibility
1. Analyze available data from Binance API
2. Estimate storage requirements for tick data
3. Research existing footprint charting libraries
4. Prototype simple order flow metrics

### Phase 2: Data Collection
1. Extend data fetcher for trade-by-trade data
2. Design storage schema for order flow data
3. Implement real-time WebSocket collectors
4. Build order book reconstruction logic

### Phase 3: Visualization
1. Create footprint chart component
2. Volume profile visualization
3. Delta heatmaps
4. Order flow indicators

### Phase 4: Strategy Development
1. Define entry/exit rules based on order flow
2. Backtest with historical tick data
3. Paper trading validation
4. Live trading (if successful)

## 📚 Resources to Review

- [ ] Binance API documentation (trades & order book)
- [ ] Footprint charting best practices
- [ ] Order flow trading literature
- [ ] Existing Python libraries (e.g., `python-binance`, `ccxt`)

## 💭 Notes

- Footprint scalping je **high-frequency** approach - může vyžadovat low latency infrastructure
- Storage requirements mohou být **significant** (tick data = velký volume)
- Může vyžadovat **real-time processing** - odlišné od current batch backtesting
- **Risk management** je kritický (scalping má tight stop-losses)

## ✅ Action Items

- [ ] **Prodiskutovat strategii** - Je footprint scalping správný směr pro tento projekt?
- [ ] **Data access** - Ověřit dostupnost tick dat z Binance
- [ ] **Storage estimation** - Spočítat storage requirements
- [ ] **Prototype** - Malý proof-of-concept s order flow vizualizací
- [ ] **Decide** - Go/No-go rozhodnutí po initial research

---

**Next Steps:** Prodiskutovat a zvážit, zda má smysl investovat čas do footprint scalping vs. jiné trading approaches.
