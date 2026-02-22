# Alembic Database Migrations Guide

Alembic manages database schema changes in a version-controlled way.

## Why Alembic?

**Before (manual SQL):**
- Write SQL migration scripts
- Manually track which migrations ran
- Hard to rollback changes
- No automated deployment

**With Alembic:**
- Versioned migrations
- Automatic tracking of applied migrations
- Easy rollback
- Same command works dev/staging/prod

---

## Quick Start

### 1. Create a new migration

```bash
# Describe what the migration does
alembic revision -m "add user_preferences table"

# This creates: alembic/versions/abc123_add_user_preferences_table.py
```

### 2. Edit the migration file

```python
# alembic/versions/abc123_add_user_preferences_table.py

def upgrade():
    """Apply the migration"""
    op.create_table(
        'user_preferences',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.String(50), nullable=False),
        sa.Column('theme', sa.String(20), default='light'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )
    op.create_index('idx_user_id', 'user_preferences', ['user_id'])

def downgrade():
    """Rollback the migration"""
    op.drop_index('idx_user_id')
    op.drop_table('user_preferences')
```

### 3. Apply the migration

```bash
# Apply all pending migrations
alembic upgrade head

# Apply one migration
alembic upgrade +1

# Rollback one migration
alembic downgrade -1
```

---

## Common Operations

### Add a column

```python
def upgrade():
    op.add_column('strategies',
        sa.Column('tags', sa.ARRAY(sa.String()), nullable=True)
    )

def downgrade():
    op.drop_column('strategies', 'tags')
```

### Modify a column

```python
def upgrade():
    # Change column type
    op.alter_column('backtest_reports', 'total_return',
        type_=sa.Numeric(precision=10, scale=2),
        existing_type=sa.Float()
    )

def downgrade():
    op.alter_column('backtest_reports', 'total_return',
        type_=sa.Float(),
        existing_type=sa.Numeric(precision=10, scale=2)
    )
```

### Create an index

```python
def upgrade():
    op.create_index('idx_symbol_timeframe', 'candles',
        ['symbol', 'timeframe']
    )

def downgrade():
    op.drop_index('idx_symbol_timeframe')
```

### Add a foreign key

```python
def upgrade():
    op.create_foreign_key(
        'fk_events_project_id',
        'timeline_events', 'projects',
        ['project_id'], ['id'],
        ondelete='CASCADE'
    )

def downgrade():
    op.drop_constraint('fk_events_project_id', 'timeline_events')
```

### Insert data

```python
from alembic import op
from sqlalchemy import table, column

def upgrade():
    # Create a temporary table representation
    strategies_table = table('strategies',
        column('name', sa.String),
        column('description', sa.String),
        column('class_name', sa.String)
    )

    # Insert default strategies
    op.bulk_insert(strategies_table, [
        {'name': 'MA Crossover', 'description': 'Moving average crossover', 'class_name': 'MovingAverageCrossover'},
        {'name': 'RSI Reversal', 'description': 'RSI mean reversion', 'class_name': 'RSIReversal'},
    ])
```

---

## Workflow

### Development
```bash
# 1. Make DB schema change
alembic revision -m "add feature X"

# 2. Edit migration file
# 3. Test migration
alembic upgrade head

# 4. Test rollback
alembic downgrade -1
alembic upgrade head

# 5. Commit migration file to git
git add alembic/versions/*
git commit -m "Migration: add feature X"
```

### Deployment (Production)
```bash
# On server
git pull
alembic upgrade head  # Apply new migrations
# Restart application
```

---

## Commands Reference

| Command | Description |
|---------|-------------|
| `alembic revision -m "message"` | Create new migration |
| `alembic upgrade head` | Apply all pending migrations |
| `alembic upgrade +1` | Apply next migration |
| `alembic downgrade -1` | Rollback last migration |
| `alembic downgrade base` | Rollback all migrations |
| `alembic current` | Show current revision |
| `alembic history` | Show migration history |
| `alembic show <revision>` | Show specific migration |

---

## Migration from SQL Scripts

You currently have SQL migrations in `migrations/` directory:
```
migrations/
├── 001_add_market_regimes.sql
├── 002_add_strategies.sql
├── 003_add_agent_tables.sql
├── 004_add_error_logs.sql
└── 005_add_projects.sql
```

### Strategy: Use both temporarily

1. **Keep using SQL for existing migrations** (already applied)
2. **Use Alembic for NEW migrations** going forward
3. Create an "initial" Alembic migration that represents current state:

```bash
# Create baseline migration
alembic revision -m "initial_schema_from_existing_sql"
```

In this migration, add a comment that this represents the state after SQL migration 005:
```python
"""initial_schema_from_existing_sql

This migration represents the database state after applying
SQL migrations 001-005. No actual changes are made.

Revision ID: abc123
Create Date: 2024-02-14
"""

def upgrade():
    # Database already has all tables from SQL migrations
    # This is just a baseline for future Alembic migrations
    pass

def downgrade():
    # Cannot rollback past this point with Alembic
    raise NotImplementedError("Cannot rollback initial schema")
```

Then:
```bash
# Mark this as applied without running it
alembic stamp head
```

Now all future migrations use Alembic!

---

## Troubleshooting

### "Target database is not up to date"
```bash
# Check current version
alembic current

# Check what migrations are pending
alembic history

# Apply missing migrations
alembic upgrade head
```

### Migration fails halfway
```bash
# Check what happened
alembic current

# Fix the migration file
# Re-run (Alembic is transactional, so safe to retry)
alembic upgrade head
```

### Need to undo a migration
```bash
# Rollback last migration
alembic downgrade -1

# Fix the migration file
# Re-apply
alembic upgrade head
```

---

## Best Practices

1. **Always test migrations locally first**
   ```bash
   # Test upgrade
   alembic upgrade head
   # Test downgrade
   alembic downgrade -1
   # Re-upgrade
   alembic upgrade head
   ```

2. **Keep migrations small and focused**
   - One migration = one logical change
   - Don't mix schema changes with data migrations

3. **Always write downgrade()**
   - Even if you think you'll never rollback
   - Makes testing easier

4. **Test with production-like data**
   - Large tables behave differently
   - Test migration performance

5. **Backup before production migrations**
   ```bash
   pg_dump trading_bot > backup_$(date +%Y%m%d).sql
   alembic upgrade head
   ```

---

## Integration with Deployment

### Docker
```dockerfile
# In Dockerfile
COPY alembic/ /app/alembic/
COPY alembic.ini /app/

# In entrypoint.sh
alembic upgrade head  # Run migrations
python api/main.py    # Start app
```

### Railway/Render
```bash
# In build command
pip install -r requirements.txt

# In start command
alembic upgrade head && uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

---

## Next Steps

1. Create baseline migration: `alembic revision -m "initial_schema"`
2. Mark as applied: `alembic stamp head`
3. Create your first real migration: `alembic revision -m "add_feature_x"`
4. Test it: `alembic upgrade head && alembic downgrade -1`
