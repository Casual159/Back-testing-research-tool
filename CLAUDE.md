# Claude Code Configuration

## Project Paths

- **Obsidian Vault**: `Backtesting_Obsidian/` - dokumentace projektu
  - `01-Architecture/` - architektonické dokumenty
  - `02-Components/` - komponenty systému
  - `04-Workflows/` - pracovní postupy
  - `05-Reference/` - referenční materiály
  - `99-Meta/` - meta dokumenty

## Key Directories

- `core/backtest/strategies/` - implementace strategií
- `core/backtest/strategies/composition/` - composable strategy framework
- `api/` - FastAPI backend
- `frontend/` - Next.js frontend
- `data/` - data storage layer
- `config/` - konfigurace

## Database

- PostgreSQL pro OHLCV data a market regimes
- Tabulky: `candles`, `market_regimes`

## Current Focus

- Agent implementation s native Claude tools
- Strategy domain design
