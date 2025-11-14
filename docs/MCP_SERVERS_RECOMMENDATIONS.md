# MCP Servery pro CryptoAnalyzer

*Datum vytvoření: 2025-11-11*

---

## 🔌 Co je MCP (Model Context Protocol)?

**MCP je jako "USB-C pro AI"** - standardizovaný protokol, který umožňuje AI modelům (jako Claude) připojit se k externím zdrojům dat a nástrojům bez nutnosti custom integrace.

### Rozdíl mezi AI Agent Frameworky vs. MCP Servery:

| | **AI Agent Frameworky** (CrewAI, LangChain) | **MCP Servery** |
|---|---|---|
| **Co to je** | Orchestrační layer pro agenty | Standardizované datové konektory |
| **Účel** | Řídit workflow a koordinovat AI agenty | Poskytnout AI přístup k datům/nástrojům |
| **Příklad** | "Jak agenti spolupracují" | "Ke kterým zdrojům agenti přistupují" |
| **Úroveň** | High-level (orchestrace) | Low-level (data access) |
| **Analogie** | Dirigent orchestru | Hudební nástroje |

**MCP servery jsou KOMPLEMENTÁRNÍ k AI frameworkům** - používají se společně!

---

## Klíčové Koncepty MCP

### Tři Core Primitives:

1. **Tools** - Funkce, které AI může volat (např. `get_current_price()`)
2. **Resources** - Data, ke kterým AI může přistupovat (např. databázové tabulky)
3. **Prompts** - Šablony pro AI workflows (např. "Analyze trading opportunity")

### Architektura:

```
┌─────────────────┐
│   MCP Client    │  ← AI aplikace (Claude, GPT, etc.)
│  (AI Agent)     │
└────────┬────────┘
         │ MCP Protocol
         ▼
┌─────────────────┐
│   MCP Server    │  ← Poskytuje přístup k datům/nástrojům
│ (PostgreSQL)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Data Source    │  ← Skutečná data (databáze, API, soubory)
│  (PostgreSQL)   │
└─────────────────┘
```

---

## 🎯 Top 10 MCP Serverů pro CryptoAnalyzer

### **1. PostgreSQL MCP Server** ⭐ NEJVYŠŠÍ PRIORITA
- **Co poskytuje**: Přímý SQL přístup k vaší PostgreSQL databázi
- **Využití**:
  ```python
  # AI může přímo dotazovat vaši databázi
  "Najdi všechny dny kde BTC kleslo více než 5% a RSI bylo pod 30"
  # MCP server automaticky přeloží na SQL a vrátí výsledky
  ```
- **Benefit**: Zero-code přístup k historickým datům pro AI agenty
- **Instalace**: `npm install @modelcontextprotocol/server-postgres`
- **Dokumentace**: https://github.com/modelcontextprotocol/servers/tree/main/src/postgres

### **2. Filesystem MCP Server**
- **Co poskytuje**: Bezpečný přístup k souborům (čtení/zápis)
- **Využití**:
  - AI může číst vaše strategy JSONs z `strategies/` adresáře
  - Automaticky generovat nové strategie a ukládat je
  - Analyzovat backtest výsledky z `reports/`
- **Security**: Konfigurovatelné access controls
- **Instalace**: `npm install @modelcontextprotocol/server-filesystem`
- **Dokumentace**: https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem

### **3. Git MCP Server**
- **Co poskytuje**: Práce s Git repozitářem (čtení, search, manipulace)
- **Využití**:
  - AI může analyzovat historii commitů
  - Najít kdy byla určitá strategie změněna
  - Automaticky commitovat nové strategie
  - Search přes celou codebase historii
- **Instalace**: `npm install @modelcontextprotocol/server-git`
- **Dokumentace**: https://github.com/modelcontextprotocol/servers/tree/main/src/git

### **4. Memory MCP Server**
- **Co poskytuje**: Persistentní paměť pro AI (knowledge graph)
- **Využití**:
  - AI si pamatuje vaše preference pro trading strategie
  - Uchovává kontext napříč sessions
  - "Pamatuj si, že preferuji konzervativní strategie s max 2% drawdown"
- **Kritické pro**: Long-running AI asistenty
- **Instalace**: `npm install @modelcontextprotocol/server-memory`
- **Dokumentace**: https://github.com/modelcontextprotocol/servers/tree/main/src/memory

### **5. Alpaca MCP Server** (TRADING REFERENCE!)
- **Co poskytuje**: Stock/options trading přes Alpaca API
- **Využití**:
  - Referenční implementace pro trading MCP server
  - Live trading execution pattern
  - Real-time market data integration
  - Portfolio management pattern
- **Poznámka**: Alpaca nepodporuje crypto, ale **použijte jako template pro Binance MCP Server!**
- **Dokumentace**: https://github.com/modelcontextprotocol/servers (community servers)

### **6. AlphaVantage MCP Server**
- **Co poskytuje**: 100+ finančních API (stocks, forex, crypto fundamentals)
- **Využití**:
  - Získat makro data (FED rates, inflation, etc.)
  - Korelace mezi BTC a stock market
  - Alternative data pro strategie
  - Crypto fundamentals (market cap, circulating supply)
- **Limit**: Free tier má 25 requests/day
- **Dokumentace**: https://github.com/modelcontextprotocol/servers (community servers)

### **7. Apify MCP Server** (WEB SCRAPING!)
- **Co poskytuje**: 6,000+ pre-built scrapers pro weby, e-commerce, social media
- **Využití**:
  - Scrape crypto sentiment z Twitter/Reddit
  - Extrahovat data z CoinMarketCap, CoinGecko
  - Monitoring TradingView ideas/charts
  - Fear & Greed Index scraping
  - Whale transaction monitoring
- **Benefit**: Ready-made scrapers, nemusíte psát vlastní
- **Pricing**: Pay-as-you-go (free tier available)
- **Dokumentace**: https://docs.apify.com/platform/integrations/model-context-protocol

### **8. Fetch MCP Server**
- **Co poskytuje**: Fetch web content a konverze pro LLM
- **Využití**:
  - Získat aktuální crypto news z CoinDesk, Cointelegraph
  - Analyzovat blog posty o trading strategiích
  - Extrahovat data z exchange announcementů
  - Monitoring regulatorních změn (SEC, EU MiCA)
- **Instalace**: `npm install @modelcontextprotocol/server-fetch`
- **Dokumentace**: https://github.com/modelcontextprotocol/servers/tree/main/src/fetch

### **9. Time MCP Server**
- **Co poskytuje**: Time a timezone konverze
- **Využití**:
  - Důležité pro crypto trading (24/7 global markets)
  - Konverze UTC timestamps z Binance
  - Timezone-aware backtest analýza
  - Synchronizace s exchange časovými zónami
- **Instalace**: `npm install @modelcontextprotocol/server-time`
- **Dokumentace**: https://github.com/modelcontextprotocol/servers/tree/main/src/time

### **10. Custom Binance MCP Server** (VYTVOŘIT!)
- **Co by poskytoval**: Direct Binance API přístup přes MCP
- **Využití**:
  - Real-time market data (klines, tickers, orderbook)
  - Order execution (buy/sell/limit/stop-loss)
  - Account balances a position tracking
  - Trade history a PnL reporting
  - WebSocket streams pro real-time updates
- **Implementace**: Vytvořit vlastní MCP server podle vašeho `data/fetcher.py`
- **Tools**:
  - `get_current_price(symbol)`
  - `get_klines(symbol, interval, limit)`
  - `get_orderbook(symbol, depth)`
  - `place_order(symbol, side, quantity, price)`
  - `get_account_balance()`
- **Template**: Použít Alpaca MCP server jako referenci

---

## 🏗️ Jak MCP Servery Integrovat do CryptoAnalyzer

### Architektura s MCP:

```
┌─────────────────────────────────────────┐
│   AI Agent Layer (CrewAI/LangChain)     │
│   - Technical Analyst Agent             │
│   - Sentiment Analyst Agent             │
│   - Risk Manager Agent                  │
└─────────────┬───────────────────────────┘
              │
              │ MCP Protocol
              ▼
┌────────────────────��────────────────────┐
│         MCP Server Layer                │
│  ┌──────────┐  ┌──────────┐  ┌────────┐│
│  │PostgreSQL│  │Filesystem│  │ Binance││
│  │  Server  │  │  Server  │  │ Server ││
│  └──────────┘  └──────────┘  └────────┘│
│  ┌──────────┐  ┌──────────┐  ┌────────┐│
│  │   Git    │  │  Memory  │  │  Apify ││
│  │  Server  │  │  Server  │  │ Server ││
│  └──────────┘  └──────────┘  └────────┘│
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│         Data Sources                    │
│  - PostgreSQL DB (historical data)      │
│  - Strategy JSONs (filesystem)          │
│  - Binance API (live data)              │
│  - Web (news, sentiment)                │
└─────────────────────────────────────────┘
```

### Konkrétní Implementace:

#### 1️⃣ **Setup PostgreSQL MCP Server**
```bash
# Instalace
npm install -g @modelcontextprotocol/server-postgres

# Konfigurace pro Claude Desktop (~/.config/claude/claude_desktop_config.json)
{
  "mcpServers": {
    "postgres": {
      "command": "mcp-server-postgres",
      "args": ["postgresql://localhost/cryptoanalyzer"]
    }
  }
}
```

#### 2️⃣ **Použití v Python s LangChain**
```python
from langchain_anthropic import ChatAnthropic
from langchain.agents import create_mcp_agent

# Claude s MCP připojením
llm = ChatAnthropic(model="claude-3-5-sonnet-20250129")

# Agent s přístupem k PostgreSQL přes MCP
agent = create_mcp_agent(
    llm=llm,
    mcp_servers=["postgres", "filesystem", "git"]
)

# Natural language dotazy
response = agent.run(
    "Find all days in 2024 where BTC dropped more than 5% "
    "and RSI was below 30. Then save the results to a JSON file."
)
# MCP server automaticky:
# 1. Přeloží to na SQL dotaz
# 2. Dotáže PostgreSQL
# 3. Použije filesystem server k uložení JSON
```

#### 3️⃣ **Vytvořit Custom Binance MCP Server**
```python
# mcp_servers/binance_server.py
from mcp import Server, Tool
from binance.client import Client
import os

server = Server("binance-mcp")

@server.tool()
async def get_current_price(symbol: str) -> dict:
    """
    Get current price for a symbol from Binance

    Args:
        symbol: Trading pair (e.g., 'BTCUSDT')

    Returns:
        Dict with symbol and price
    """
    client = Client()
    ticker = client.get_symbol_ticker(symbol=symbol)
    return ticker

@server.tool()
async def get_klines(
    symbol: str,
    interval: str,
    limit: int = 100,
    start_time: int = None,
    end_time: int = None
) -> list:
    """
    Get historical klines/candlestick data

    Args:
        symbol: Trading pair (e.g., 'BTCUSDT')
        interval: Kline interval ('1m', '5m', '1h', '1d', etc.)
        limit: Number of klines to return (max 1000)
        start_time: Optional start timestamp (ms)
        end_time: Optional end timestamp (ms)

    Returns:
        List of klines [timestamp, open, high, low, close, volume, ...]
    """
    client = Client(
        api_key=os.getenv('BINANCE_API_KEY'),
        api_secret=os.getenv('BINANCE_API_SECRET')
    )
    klines = client.get_klines(
        symbol=symbol,
        interval=interval,
        limit=limit,
        startTime=start_time,
        endTime=end_time
    )
    return klines

@server.tool()
async def get_orderbook(symbol: str, depth: int = 100) -> dict:
    """
    Get order book depth for a symbol

    Args:
        symbol: Trading pair (e.g., 'BTCUSDT')
        depth: Order book depth (5, 10, 20, 50, 100, 500, 1000, 5000)

    Returns:
        Dict with bids and asks
    """
    client = Client()
    orderbook = client.get_order_book(symbol=symbol, limit=depth)
    return orderbook

@server.resource(uri="binance://account/balance")
async def get_account_balance() -> dict:
    """Get account balances"""
    client = Client(
        api_key=os.getenv('BINANCE_API_KEY'),
        api_secret=os.getenv('BINANCE_API_SECRET'),
        testnet=os.getenv('BINANCE_TESTNET', 'true').lower() == 'true'
    )
    account = client.get_account()
    return {
        'balances': [
            b for b in account['balances']
            if float(b['free']) > 0 or float(b['locked']) > 0
        ]
    }

# Spustit server
if __name__ == "__main__":
    server.run()
```

**Spuštění Binance MCP Serveru**:
```bash
# V pyproject.toml nebo setup.py přidat entry point
[project.scripts]
mcp-server-binance = "mcp_servers.binance_server:main"

# Instalace
pip install -e .

# Konfigurace v Claude Desktop
{
  "mcpServers": {
    "binance": {
      "command": "mcp-server-binance",
      "env": {
        "BINANCE_API_KEY": "your_api_key",
        "BINANCE_API_SECRET": "your_api_secret",
        "BINANCE_TESTNET": "true"
      }
    }
  }
}
```

---

## 📊 MCP Servery vs. AI Agent Frameworky - Kdy co použít?

### Příklad Workflow:

**Úkol**: "Najdi nejlepší trading příležitosti z včerejška a vytvoř novou strategii"

```python
# 1. AI AGENT FRAMEWORK (CrewAI) - orchestrace
from crewai import Agent, Task, Crew

data_analyst = Agent(
    role='Data Analyst',
    goal='Find trading opportunities from historical data',
    # 👇 POUŽÍVÁ MCP SERVERY PRO PŘÍSTUP K DATŮM
    tools=[PostgreSQLTool(), BinanceTool()]  # MCP servery jako tools
)

strategy_creator = Agent(
    role='Strategy Creator',
    goal='Create new trading strategy based on opportunities',
    # 👇 POUŽÍVÁ MCP SERVERY PRO UKLÁDÁNÍ
    tools=[FilesystemTool(), GitTool()]  # MCP servery jako tools
)

# Crew orchestruje agenty
crew = Crew(agents=[data_analyst, strategy_creator])

# 2. MCP SERVERY - poskytují data/nástroje
# PostgreSQL MCP - vrací data z DB
# Binance MCP - real-time ceny
# Filesystem MCP - ukládá novou strategii
# Git MCP - commituje do repa

result = crew.kickoff()
```

**Tok informací**:
1. **CrewAI Agent** (high-level) řekne: "Potřebuji data z DB"
2. **PostgreSQL MCP Server** (low-level) provede SQL dotaz a vrátí data
3. **CrewAI Agent** analyzuje data
4. **CrewAI Agent** řekne: "Ulož novou strategii"
5. **Filesystem MCP Server** uloží JSON soubor
6. **Git MCP Server** commitne změnu

---

## 🚀 Implementační Plán pro CryptoAnalyzer

### Fáze 1: Basic MCP Setup (1 týden)
1. ✅ Nainstalovat PostgreSQL MCP server
2. ✅ Nainstalovat Filesystem MCP server
3. ✅ Nainstalovat Memory MCP server
4. ✅ Test: "AI dotazy na databázi"

### Fáze 2: Custom Binance MCP (2 týdny)
5. ✅ Vytvořit Binance MCP server (na základě vašeho `data/fetcher.py`)
6. ✅ Implementovat tools: `get_klines`, `get_ticker`, `get_orderbook`
7. ✅ Přidat resources: `account/balance`, `account/trades`
8. ✅ Test: "Real-time data přes MCP"

### Fáze 3: AI Agent Integration (2-3 týdny)
9. ✅ Nainstalovat LangChain/CrewAI
10. ✅ Připojit MCP servery jako tools
11. ✅ Vytvořit první AI agenta s MCP přístupem
12. ✅ Test: "End-to-end AI trading workflow"

### Fáze 4: Advanced MCP Servery (1-2 týdny)
13. ✅ Přidat Apify MCP (sentiment scraping)
14. ✅ Přidat Fetch MCP (news monitoring)
15. ✅ Přidat Git MCP (version control)
16. ✅ Test: "Multi-source data fusion"

---

## 📋 Srovnání MCP Serverů

| MCP Server | Priority | Složitost | Čas na setup | Benefit pro CryptoAnalyzer |
|------------|----------|-----------|--------------|----------------------------|
| PostgreSQL | ⭐⭐⭐⭐⭐ | Nízká | 1 hodina | Přímý SQL přístup k historickým datům |
| Filesystem | ⭐⭐⭐⭐⭐ | Velmi nízká | 30 min | Práce se strategy JSONs a backtest reports |
| Memory | ⭐⭐⭐⭐ | Nízká | 1 hodina | Persistent AI kontext a preference |
| Custom Binance | ⭐⭐⭐⭐⭐ | Střední | 1-2 týdny | Real-time trading data a execution |
| Git | ⭐⭐⭐ | Nízká | 30 min | Version control integrace |
| Apify | ⭐⭐⭐⭐ | Střední | 2-3 dny | Sentiment/alternative data scraping |
| Fetch | ⭐⭐⭐ | Velmi nízká | 30 min | News monitoring a content extraction |
| Time | ⭐⭐ | Velmi nízká | 15 min | Timezone handling pro global markets |
| Alpaca | ⭐⭐ | Nízká | 1 hodina | Reference implementace pro trading MCP |
| AlphaVantage | ⭐⭐ | Nízká | 1 hodina | Macro data a fundamentals |

---

## 🎁 Complete Stack: MCP + AI Agents

**Doporučená kombinace pro CryptoAnalyzer**:

```
┌─────────────────────────────────────────┐
│         Application Layer               │
│    Streamlit Dashboard + CLI            │
│    - Chart Generator                    │
│    - Backtesting UI                     │
│    - Strategy Composer                  │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│      AI Orchestration Layer             │
│    ┌──────────┐  ┌──────────┐          │
│    │ CrewAI   │  │LangChain │          │  ← AI AGENT FRAMEWORKY
│    └──────────┘  └──────────┘          │
│    ┌──────────┐                        │
│    │AgentOps  │  (Monitoring)          │
│    └──────────┘                        │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│         MCP Protocol Layer              │
│    Standardizované rozhraní             │  ← MCP STANDARD
│    - Tools (funkce pro AI)              │
│    - Resources (datové zdroje)          │
│    - Prompts (workflow šablony)         │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│         MCP Servers Layer               │
│  ┌──────────┐  ┌──────────┐  ┌────────┐│
│  │PostgreSQL│  │ Binance  │  │Filesys ││  ← MCP SERVERY
│  └──────────┘  └──────────┘  └────────┘│
│  ┌──────────┐  ┌──────────┐  ┌────────┐│
│  │   Git    │  │  Memory  │  │  Apify ││
│  └──────────┘  └──────────┘  └────────┘│
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│         Data Sources                    │
│  - PostgreSQL DB (historical OHLCV)     │
│  - Strategy JSONs (filesystem)          │
│  - Binance API (live market data)       │
│  - Web (news, sentiment, social media)  │
│  - Git Repo (version history)           │
└─────────────────────────────────────────┘
```

---

## 💡 Konkrétní Use Cases

### Use Case 1: AI-Powered Strategy Discovery
```python
# User request v Streamlit dashboardu
"Find trading opportunities where RSI < 30 and price dropped > 5% in last month"

# AI Agent workflow:
1. PostgreSQL MCP - dotaz na historická data
2. Analyze - AI analyzuje patterns
3. Binance MCP - check current market conditions
4. Filesystem MCP - save discovered opportunities as JSON
5. Git MCP - commit new findings
```

### Use Case 2: Automated Strategy Creation
```python
"Create a new conservative strategy based on last week's best trades"

# AI Agent workflow:
1. PostgreSQL MCP - get last week's trades with > 2% profit
2. Analyze - AI identifikuje společné vzory
3. Generate - vytvoří novou strategy JSON
4. Filesystem MCP - save strategy file
5. Git MCP - commit with message "AI-generated conservative strategy"
6. Trigger backtest - test nové strategie
```

### Use Case 3: Market Sentiment Analysis
```python
"What's the current market sentiment for BTC?"

# AI Agent workflow:
1. Fetch MCP - get latest crypto news from CoinDesk
2. Apify MCP - scrape Twitter/Reddit sentiment
3. Binance MCP - get current price action
4. Memory MCP - compare with historical sentiment data
5. Generate report - AI vytvoří sentiment summary
```

### Use Case 4: Real-time Trading Decision
```python
"Should I enter a long position on ETH right now?"

# AI Agent workflow:
1. Binance MCP - get current ETH price, orderbook, recent trades
2. PostgreSQL MCP - get historical performance in similar conditions
3. Technical indicators - calculate RSI, MACD, etc. from current data
4. Risk assessment - check portfolio balance, open positions
5. Memory MCP - recall user's risk preferences
6. Generate recommendation - AI provides entry/exit/stop-loss levels
```

---

## 🔗 Další Zdroje

### Oficiální Dokumentace:
- **MCP Specification**: https://spec.modelcontextprotocol.io/
- **MCP Servers Repository**: https://github.com/modelcontextprotocol/servers
- **Anthropic MCP Docs**: https://docs.anthropic.com/en/docs/agents-and-tools/mcp
- **Anthropic MCP Course**: https://anthropic.skilljar.com/introduction-to-model-context-protocol

### Community:
- **MCP Discord**: https://discord.gg/modelcontextprotocol
- **Reddit r/AnthropicAI**: Discussion o MCP implementacích

### Open Source Examples:
- **MCP Server Template**: https://github.com/modelcontextprotocol/typescript-sdk
- **Python MCP SDK**: https://github.com/modelcontextprotocol/python-sdk

---

## 🎯 Next Steps

1. **Quick Win**: Nainstalujte PostgreSQL + Filesystem MCP servery (< 2 hodiny)
2. **Test**: Vyzkoušejte natural language dotazy na vaši databázi
3. **Custom Build**: Vytvořte Binance MCP server (1-2 týdny)
4. **Integration**: Připojte MCP k CrewAI/LangChain agentům
5. **Production**: Nasaďte kompletní AI-powered trading system

---

**Doporučení**: Začněte s **PostgreSQL MCP + Filesystem MCP** pro quick win, pak postupně přidávejte další servery podle potřeby. Custom Binance MCP server bude game-changer pro váš projekt!
