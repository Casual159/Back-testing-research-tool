# AI Quick Start Guide

**Purpose:** Get AI (Claude) up to speed in under 60 seconds  
**Last Updated:** 2024-12-05  
**Project:** Back-testing Research Tool

---

## ⚡ 30-Second Context

**What is this project?**  
AI-enhanced backtesting tool for cryptocurrency trading strategies combining deterministic Python core with AI conversational interface.

**Core Technology Stack:**
- **Backend:** Python 3.12 + FastAPI
- **Frontend:** Next.js 15 + React + TypeScript
- **Database:** PostgreSQL
- **Charts:** Plotly.js
- **AI:** Claude (you!) via MCP servers (future)

**Your Role as AI:**
- Help implement features deterministically
- Generate documentation from code
- Suggest trading strategies and analysis approaches
- **CRITICAL:** NEVER execute trades autonomously - always require human approval

---

## 📚 Read These First (Priority Order)

### ⭐ Essential (Read Before Doing Anything)
1. **[[Project Root]]** - Main navigation hub, project overview
2. **[[01-Architecture/_AI_CONTEXT]]** - System architecture quick reference
3. **[[02-Components/_AI_CONTEXT]]** - Available components and when to use them

### 📖 Task-Specific (Read When Relevant)
4. **[[04-Workflows/_AI_CONTEXT]]** - How to perform common development tasks
5. **[[05-Reference/_GENERATED/README]]** - Auto-generated schemas and API docs
6. **[[99-Meta/AI_Session_Notes/_TEMPLATE]]** - Session notes template

### 🔍 Deep Dive (Optional, Context-Dependent)
- Latest session: **[[99-Meta/AI_Session_Notes/]]** (check most recent date)
- Research ideas: **[[06-Research/]]**
- Feature specs: **[[03-Features/]]**

---

## 🎯 Common Tasks → Quick Navigation

| I Need To... | Read This First |
|-------------|----------------|
| Understand project architecture | [[01-Architecture/System Overview]] |
| Add a new technical indicator | [[04-Workflows/FOR_AI_Adding_Indicator]] |
| Create a new API endpoint | [[04-Workflows/FOR_AI_Creating_Endpoint]] |
| Work with database schema | [[05-Reference/_GENERATED/database_schema.sql]] |
| Fix backtesting bug | [[02-Components/Backtesting Engine#Known Issues]] |
| Understand data fetching | [[02-Components/Data Layer]] |
| Generate documentation | [[04-Workflows/FOR_AI_Generating_Docs]] |
| Create chart visualization | [[02-Components/Frontend#Chart Components]] |
| Review API endpoints | [[05-Reference/_GENERATED/api_endpoints.json]] |

---

## 🚨 Critical Rules for AI

### 1. **Always Read `_AI_CONTEXT.md` First**
Before diving into any section, read the `_AI_CONTEXT.md` file in that folder. It contains:
- Quick decision trees
- Component availability status
- Critical gotchas
- Links to detailed docs

### 2. **Check `_GENERATED/` for Latest Truth**
Auto-generated documentation is always current:
- **API schemas:** Regenerated from FastAPI routes
- **Database schemas:** Extracted from PostgreSQL
- **Type definitions:** Generated from Python type hints

**Never trust memory - always check `_GENERATED/` files!**

### 3. **Never Modify Core Trading Logic Without Approval**
These files require explicit human approval before changes:
- `core/backtest/engine.py` - Backtesting engine
- `core/backtest/portfolio.py` - Position tracking
- `core/data/storage.py` - Database operations
- Any file handling money/trades/risk

### 4. **Always Use Database Deduplication**
Every PostgreSQL insert MUST use:
```sql
INSERT INTO candles (...) VALUES (...)
ON CONFLICT (symbol, timeframe, open_time) DO NOTHING
```

### 5. **Validate AI-Generated Code**
- Never trust AI-generated calculations without validation
- Always write deterministic tests
- Cross-reference with existing implementations

---

## 🔄 After Your Session

**Required Actions:**

1. **Create Session Note**
   - Use template: [[99-Meta/AI_Session_Notes/_TEMPLATE]]
   - Save as: `99-Meta/AI_Session_Notes/YYYY-MM-DD_topic.md`
   - Include: What changed, why, what's next

2. **Update `_GENERATED/` Docs** (if applicable)
   - If you modified API endpoints → run `python scripts/generate_api_docs.py`
   - If you modified database schema → run `python scripts/generate_db_schema.py`
   - If you modified types → run `python scripts/generate_types.py`

3. **Update Relevant `_AI_CONTEXT.md`** (if needed)
   - Added new component? Update `02-Components/_AI_CONTEXT.md`
   - Changed workflow? Update `04-Workflows/_AI_CONTEXT.md`

4. **Link New Documents**
   - Use Obsidian `[[wikilinks]]` syntax
   - Create bidirectional links where relevant
   - Update parent documents with new references

---

## 🧭 Navigation Philosophy

**This documentation uses a "Hub and Spoke" model:**

```
Project Root (Hub)
    ├─→ 01-Architecture (Spoke) ─→ _AI_CONTEXT (Mini-hub) ─→ Detailed docs
    ├─→ 02-Components (Spoke) ─→ _AI_CONTEXT (Mini-hub) ─→ Detailed docs
    ├─→ 03-Features (Spoke) ─→ Feature-specific docs
    ├─→ 04-Workflows (Spoke) ─→ _AI_CONTEXT (Mini-hub) ─→ Task guides
    ├─→ 05-Reference (Spoke) ─→ _GENERATED/ (Auto-updated)
    ├─→ 06-Research (Spoke) ─→ Experiment notes
    └─→ 99-Meta (Spoke) ─→ Session notes, TODOs
```

**Always start at a hub (`_AI_CONTEXT.md` or `Project Root.md`), then follow spokes.**

---

## 💡 Documentation Standards

### For AI-Focused Documents
- **Explicit over implicit** - no ambiguity
- **Structured data** - tables, lists, code blocks
- **File locations** - always include `file.py:line_number`
- **Decision trees** - "If X, then Y" logic
- **Edge cases** - what can go wrong?

### For Human-Focused Documents
- **Visual first** - diagrams, flowcharts
- **TL;DR sections** - quick overview at top
- **Examples** - real code snippets
- **Context** - why, not just how

### Linking Best Practices
- Use `[[Document Name]]` for same folder
- Use `[[folder/Document Name]]` for different folders
- Use `[[Document Name#Section]]` for specific sections
- Create bidirectional links (mention both docs in each other)

---

## 🏁 Ready to Start?

**Your next steps:**

1. **Read** [[Project Root]] for project overview
2. **Navigate to** relevant `_AI_CONTEXT.md` for your task
3. **Follow** the decision tree to find specific documentation
4. **Execute** your task with context
5. **Document** your session in `99-Meta/AI_Session_Notes/`

---

**Philosophy:** "AI for Intent, Code for Execution"

**Remember:** This documentation is for YOU (AI) to understand the project quickly and work effectively. Humans have their own visual/high-level docs in the same files (dual-layer approach).

**Good luck! 🚀**
