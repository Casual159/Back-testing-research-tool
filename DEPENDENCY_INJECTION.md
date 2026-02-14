# Dependency Injection Guide

Dependency Injection (DI) v FastAPI automatizuje poskytování závislostí (databáze, config, atd.) do endpoint funkcí.

## Před a Po

### ❌ Před (bez DI)

```python
@app.get("/api/data/stats")
def get_data_stats():
    # Ručně vytváříš storage v každém endpointu
    storage = PostgresStorage(config['database'])
    try:
        df = storage.get_data_stats()
        # ... zpracování
        return stats
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        storage.close()  # Musíš pamatovat zavřít!
```

**Problémy:**
- Opakující se kód v každém endpointu
- Snadné zapomenout `storage.close()`
- Těžké testování (musíš mockovat config)
- Žádný connection pooling

### ✅ Po (s DI)

```python
from api.dependencies import get_db_storage

@app.get("/api/data/stats")
def get_data_stats(storage: PostgresStorage = Depends(get_db_storage)):
    # Storage už máš, připravený k použití!
    df = storage.get_data_stats()
    # ... zpracování
    return stats
    # Storage se automaticky zavře po requestu
```

**Výhody:**
- Méně kódu
- Automatické cleanup
- Snadné testování (override v testech)
- Konzistentní error handling

---

## Dostupné Dependencies

### 1. `get_config()` - Konfigurace

```python
from api.dependencies import get_config

@app.get("/endpoint")
def endpoint(config: dict = Depends(get_config)):
    db_config = config['database']
    api_key = config.get('anthropic_api_key')
    # ...
```

**Kdy použít:** Když potřebuješ přístup ke konfiguraci.

---

### 2. `get_db_storage()` - Databáze

```python
from api.dependencies import get_db_storage

@app.get("/strategies")
def list_strategies(storage: PostgresStorage = Depends(get_db_storage)):
    query = "SELECT * FROM strategies"
    storage.cursor.execute(query)
    rows = storage.cursor.fetchall()
    return rows
    # Storage se automaticky zavře
```

**Kdy použít:** Když potřebuješ přístup k databázi.

**Co dělá:**
- Vytvoří PostgresStorage
- Předá ti ho
- Po requestu automaticky zavře connection
- Při chybě loguje a vrátí 500

---

### 3. `get_request_id()` - Request ID

```python
from api.dependencies import get_request_id
from core.logging_config import get_logger

logger = get_logger(__name__)

@app.post("/backtest/run")
def run_backtest(
    request: BacktestRequest,
    request_id: str = Depends(get_request_id)
):
    logger.info("starting_backtest", request_id=request_id)
    # ...
    return results
```

**Kdy použít:** Když chceš logovat s request ID.

---

### 4. `require_api_key()` - API Key Auth

```python
from api.dependencies import require_api_key

@app.delete("/admin/clear-cache")
def clear_cache(api_key: str = Depends(require_api_key)):
    # Tento endpoint vyžaduje API key v headeru
    # X-API-Key: your-secret-key
    cache.clear()
    return {"status": "cleared"}
```

**Kdy použít:** Pro admin endpointy, které potřebují autentizaci.

---

## Kombinování Dependencies

Můžeš použít více dependencies v jednom endpointu:

```python
@app.post("/backtest/run")
def run_backtest(
    request: BacktestRequest,
    storage: PostgresStorage = Depends(get_db_storage),
    config: dict = Depends(get_config),
    request_id: str = Depends(get_request_id)
):
    logger.info("starting_backtest", request_id=request_id)

    # Máš přístup ke všemu
    df = storage.get_candles(request.symbol, request.timeframe)
    api_key = config['anthropic_api_key']

    # ...
    return results
```

---

## Testování s DI

DI dělá testování mnohem snazší:

```python
from fastapi.testclient import TestClient
from api.main import app
from api.dependencies import get_db_storage

# Mock storage
class MockStorage:
    def get_data_stats(self):
        return pd.DataFrame(...)

# Override dependency
def override_get_db_storage():
    yield MockStorage()

app.dependency_overrides[get_db_storage] = override_get_db_storage

# Test
client = TestClient(app)
response = client.get("/api/data/stats")
assert response.status_code == 200
```

Žádná reálná databáze není potřeba!

---

## Migrace Existujících Endpointů

### Před

```python
@app.get("/api/strategies")
def list_strategies():
    try:
        with PostgresStorage(config['database']) as storage:
            query = "SELECT * FROM strategies"
            storage.cursor.execute(query)
            rows = storage.cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        raise HTTPException(500, str(e))
```

### Po

```python
from api.dependencies import get_db_storage

@app.get("/api/strategies")
def list_strategies(storage: PostgresStorage = Depends(get_db_storage)):
    query = "SELECT * FROM strategies"
    storage.cursor.execute(query)
    rows = storage.cursor.fetchall()
    return [dict(row) for row in rows]
```

**Rozdíl:**
- ✂️ Méně kódu (žádný try/except, context manager)
- ✅ Automatické cleanup
- ✅ Konzistentní error handling

---

## Vlastní Dependencies

Můžeš vytvořit své vlastní:

```python
# api/dependencies.py

def get_current_user(
    api_key: str = Depends(require_api_key),
    storage: PostgresStorage = Depends(get_db_storage)
) -> dict:
    """Get current user from API key."""
    query = "SELECT * FROM users WHERE api_key = %s"
    storage.cursor.execute(query, (api_key,))
    user = storage.cursor.fetchone()

    if not user:
        raise HTTPException(401, "Invalid API key")

    return dict(user)
```

Pak v endpointech:

```python
@app.get("/me")
def get_profile(user: dict = Depends(get_current_user)):
    return {
        "username": user['username'],
        "email": user['email']
    }
```

---

## Best Practices

### 1. Používej DI pro vše, co je sdílené
- ✅ Database connections
- ✅ Configuration
- ✅ Logger context
- ✅ Authentication
- ❌ Request-specific data (to je v parametrech)

### 2. Nevolej dependencies ručně
```python
# ❌ Špatně
def endpoint():
    config = get_config()  # Nefunguje!

# ✅ Správně
def endpoint(config: dict = Depends(get_config)):
    # config je automaticky injected
```

### 3. Testuj s override
```python
# V testech
app.dependency_overrides[get_db_storage] = lambda: MockStorage()
```

### 4. Cleanup je automatický
```python
# ❌ Nepotřebuješ
def endpoint(storage = Depends(get_db_storage)):
    try:
        ...
    finally:
        storage.close()  # Zbytečné!

# ✅ DI to dělá za tebe
def endpoint(storage = Depends(get_db_storage)):
    # storage se zavře automaticky
```

---

## Postupná Migrace

Nemusíš refactorovat všechno najednou:

1. **Nové endpointy** - používej DI od začátku
2. **Staré endpointy** - nech jak jsou, dokud je neupravuješ
3. **Když edituju starý endpoint** - přepni na DI

Staré i nové endpointy můžou koexistovat!

---

## Shrnutí

| Feature | Bez DI | S DI |
|---------|--------|------|
| **Kód v endpointu** | 10-15 řádků | 3-5 řádků |
| **Error handling** | Ručně v každém endpointu | Automatické |
| **Connection cleanup** | Musíš pamatovat | Automatické |
| **Testování** | Složité (real DB) | Snadné (mock) |
| **Type hints** | Chybí | Plně typed |
| **Reusability** | Kopírování kódu | Sdílené dependencies |

**Doporučení:** Začni používat DI pro nové endpointy. Efekt uvidíš okamžitě!
