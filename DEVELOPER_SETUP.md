# Developer Setup Guide

Kompletní návod pro nastavení vývojového prostředí s novými code quality nástroji.

---

## ✅ Co jsme přidali

### 1. Pre-commit Hooks
- **Black** - automatické formátování kódu
- **flake8** - linting (code quality)
- **isort** - řazení importů
- **mypy** - type checking
- **bandit** - security issues

### 2. API Schema Validation
- Vylepšené Pydantic modely s validacemi
- Automatické error messages
- OpenAPI dokumentace

### 3. Structured Logging
- JSON-formátované logy (pro agregaci)
- Request ID tracking
- Context-aware logging

### 4. Error Handling
- Centrální error handler
- Request ID v response headers
- Automatické logování chyb

### 5. Database Migrations
- Alembic pro verzované DB změny
- Automatické deployment
- Rollback podpora

### 6. Dependency Injection
- Automatické poskytování závislostí
- Snadné testování
- Connection pooling

---

## 🚀 Quick Start

### 1. Aktualizuj dependencies

```bash
# Aktivuj virtual environment
source venv/bin/activate

# Nainstaluj nové balíčky
pip install -r requirements.txt
```

### 2. Nastav pre-commit hooks

```bash
# Nainstaluj git hooks
pre-commit install

# (Volitelné) Spusť na všech souborech
pre-commit run --all-files
```

Nyní při každém `git commit` se automaticky spustí code quality checks!

### 3. Inicializuj Alembic

```bash
# Označ současný stav DB jako baseline
alembic stamp head

# Nebo vytvoř baseline migration
alembic revision -m "initial_schema"
```

### 4. Spusť aplikaci

```bash
# Stejně jako vždy
./start-dev.sh
```

**Nové features:**
- Logy obsahují request IDs
- Chyby se automaticky logují
- API validace je přísnější (lepší error messages)

---

## 📚 Dokumentace

| Téma | Soubor | Co se dozvíš |
|------|--------|--------------|
| **Pre-commit hooks** | [SETUP_PRECOMMIT.md](SETUP_PRECOMMIT.md) | Jak nainstalovat, používat, konfigurovat |
| **Database migrations** | [ALEMBIC_GUIDE.md](ALEMBIC_GUIDE.md) | Jak vytvářet, aplikovat, rollbackovat migrace |
| **Dependency Injection** | [DEPENDENCY_INJECTION.md](DEPENDENCY_INJECTION.md) | Jak používat DI v endpointech |

---

## 🔧 Nové soubory

### Konfigurace

| Soubor | Účel |
|--------|------|
| `.pre-commit-config.yaml` | Konfigurace pre-commit hooks |
| `pyproject.toml` | Konfigurace nástrojů (black, mypy, pytest, atd.) |
| `alembic.ini` | Konfigurace Alembic |
| `alembic/env.py` | Alembic environment setup |

### Kód

| Soubor | Účel |
|--------|------|
| `api/schemas.py` | Validované Pydantic modely |
| `api/middleware.py` | Request ID, error handling, logging middleware |
| `api/dependencies.py` | DI providers (storage, config, atd.) |
| `core/logging_config.py` | Structured logging setup |

---

## 🎯 Workflow

### Denní vývoj

```bash
# 1. Udělej změny v kódu
vim core/backtest/strategies/my_strategy.py

# 2. Commitni (hooks se spustí automaticky)
git add .
git commit -m "add new strategy"

# ✓ black - reformatted 1 file
# ✓ flake8 - passed
# ✓ mypy - passed
# → Commit succeeds

# 3. Push
git push
```

### Změna DB schématu

```bash
# 1. Vytvoř migration
alembic revision -m "add tags to strategies"

# 2. Edituj migration file
vim alembic/versions/abc123_add_tags_to_strategies.py

def upgrade():
    op.add_column('strategies',
        sa.Column('tags', sa.ARRAY(sa.String())))

def downgrade():
    op.drop_column('strategies', 'tags')

# 3. Aplikuj
alembic upgrade head

# 4. Test rollback
alembic downgrade -1
alembic upgrade head

# 5. Commit
git add alembic/versions/*
git commit -m "Migration: add tags to strategies"
```

### Nový API endpoint

```python
# api/main.py
from api.dependencies import get_db_storage
from api.schemas import MyRequest, MyResponse

@app.post("/api/my-endpoint", response_model=MyResponse)
def my_endpoint(
    request: MyRequest,  # Automatická validace!
    storage: PostgresStorage = Depends(get_db_storage)  # DI!
):
    # Schema je validované
    # Storage je připravený
    # Request ID je v logu

    data = storage.query(...)
    return MyResponse(...)
    # Storage se automaticky zavře
```

---

## 🧪 Testování

### Spusť testy

```bash
# Všechny testy
pytest

# S coverage
pytest --cov=core --cov=agent --cov=api

# Konkrétní test
pytest tests/test_backtest.py::test_ma_crossover
```

### S DI mocking

```python
# tests/test_api.py
from fastapi.testclient import TestClient
from api.main import app
from api.dependencies import get_db_storage

class MockStorage:
    def get_data_stats(self):
        return pd.DataFrame({"symbol": ["BTCUSDT"]})

app.dependency_overrides[get_db_storage] = lambda: MockStorage()

client = TestClient(app)
response = client.get("/api/data/stats")
assert response.status_code == 200
```

---

## 🐛 Troubleshooting

### Pre-commit hooks failují

```bash
# Spusť je ručně a podívej se na chyby
pre-commit run --all-files

# Autofix formátování
black .
isort .

# Check type errors
mypy core/ agent/ api/
```

### Alembic - "Target database is not up to date"

```bash
# Zjisti aktuální stav
alembic current
alembic history

# Aplikuj chybějící migrace
alembic upgrade head
```

### Import errors v DI

```bash
# Ujisti se že máš všechny dependencies
pip install -r requirements.txt

# Zkontroluj Python path
python -c "import api.dependencies"
```

### Structured logging - nejde to

```bash
# Ujisti se že máš structlog
pip install structlog python-json-logger

# Restart serveru
./start-dev.sh
```

---

## 📊 Co se změnilo v API

### Request/Response

**Před:**
```json
// Špatný request
POST /api/backtest/run
{"strategy_name": "", "start_date": "invalid"}

// Response
{"detail": "Internal server error"}
```

**Nyní:**
```json
// Stejný request
POST /api/backtest/run
{"strategy_name": "", "start_date": "invalid"}

// Response s detaily
{
  "detail": [
    {
      "loc": ["body", "strategy_name"],
      "msg": "ensure this value has at least 1 characters",
      "type": "value_error.any_str.min_length"
    },
    {
      "loc": ["body", "start_date"],
      "msg": "Invalid date format: invalid. Use YYYY-MM-DD",
      "type": "value_error"
    }
  ]
}
```

### Headers

Každý response nyní obsahuje:
```
X-Request-ID: 550e8400-e29b-41d4-a716-446655440000
```

Pro debugging:
```bash
curl -i http://localhost:8000/api/strategies
# Získej request ID z headeru
# Najdi ho v logách
```

---

## 🎨 Code Style

### Python

```python
# Black formatting (automatické)
def my_function(param1: str, param2: int) -> dict:
    """Docstring."""
    return {"key": "value"}

# Type hints (mypy check)
from typing import List, Optional

def process_data(data: List[dict], limit: Optional[int] = None) -> pd.DataFrame:
    ...

# Imports (isort - automatické)
# 1. Standard library
import os
import sys

# 2. Third party
import pandas as pd
from fastapi import FastAPI

# 3. Local
from core.backtest import Engine
```

### Všechno se autoformátuje při commitu!

---

## 🚦 Co dál?

### Volitelné (pokud chceš)

1. **GitHub Actions CI/CD**
   - Automatické testy na každý push
   - Type checking v cloudu
   - Badge v README

2. **Docker**
   - Portable development environment
   - Snadný deployment

3. **Monitoring**
   - Sentry (error tracking)
   - Logtail (log aggregation)

### Postupná migrace

Nemusíš refactorovat všechno najednou:

- ✅ Nové endpointy - použij DI + schemas
- ✅ Nové DB změny - použij Alembic
- ⏸️ Staré endpointy - nech jak jsou
- ⏸️ Staré migrace - SQL je OK

---

## 💡 Tips

### 1. Pre-commit bypass (nouzově)

```bash
git commit -m "hotfix" --no-verify
# Použij OPRAVDU jen v nouzi!
```

### 2. Formátování bez commitu

```bash
black api/ core/ agent/
isort .
```

### 3. Type checking

```bash
mypy api/main.py
mypy core/backtest/
```

### 4. Request ID v logu

```python
from core.logging_config import get_logger

logger = get_logger(__name__)
logger.info("processing_backtest",
    strategy="RSI",
    symbol="BTCUSDT")
# → Log obsahuje request_id automaticky!
```

---

## ❓ FAQ

**Q: Musím změnit existující kód?**
A: Ne! Všechno funguje zpětně kompatibilně. Nové features použij postupně.

**Q: Pre-commit hooks jsou pomalé**
A: Spouští se jen na změněných souborech. První run je vždy pomalejší.

**Q: Alembic vs SQL migrations?**
A: SQL migrace nech jak jsou. Nové změny dělej v Alembic.

**Q: Jak vypnu structured logging?**
A: V `api/main.py`: `setup_logging(json_logs=False)` (už je)

**Q: DI je složité**
A: Začni s `get_db_storage()`. Je to jen `= Depends(get_db_storage)`.

---

## 🎉 Shrnutí

Nainstalovali jsme:
- ✅ Pre-commit hooks (code quality)
- ✅ Lepší API validace (Pydantic)
- ✅ Structured logging (debugging)
- ✅ Error handling (konzistentní)
- ✅ Database migrations (Alembic)
- ✅ Dependency Injection (čistší kód)

**Next steps:**
1. `pip install -r requirements.txt`
2. `pre-commit install`
3. Pokračuj v normálním vývoji!

Máš otázky? Podívej se do dokumentačních souborů nebo se zeptej.
