# Database Migrations

## Current System: Alembic

All database migrations are now managed by **Alembic**.

### Create new migration
```bash
alembic revision -m "add new feature"
```

### Apply migrations
```bash
alembic upgrade head
```

### Rollback
```bash
alembic downgrade -1
```

See [ALEMBIC_GUIDE.md](../ALEMBIC_GUIDE.md) for full documentation.

---

## Archived SQL Migrations

Old SQL migrations have been moved to `migrations_archive/`:
- 001_add_market_regimes.sql
- 002_add_strategies.sql
- 003_add_agent_tables.sql
- 004_add_error_logs.sql
- 005_add_projects.sql

These were applied manually and are represented by the Alembic baseline migration:
`3a8136333301_baseline_from_sql_migrations.py`

**Do not apply these again!** They exist only for historical reference.
