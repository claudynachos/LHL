# Database Migrations

This directory contains Alembic database migration scripts.

## Setup

Migrations are configured to use the `DATABASE_URL` environment variable from `backend/.env`.

## Creating a New Migration

```bash
cd backend
source venv/bin/activate
alembic revision --autogenerate -m "description of changes"
```

## Running Migrations

```bash
cd backend
source venv/bin/activate

# Upgrade to latest
alembic upgrade head

# Upgrade one step
alembic upgrade +1

# Downgrade one step
alembic downgrade -1

# See current revision
alembic current

# See migration history
alembic history
```

## Manual Migration

If you need to manually run SQL commands (like adding the `is_active` column that was already added), you can:

1. Use the migration script: `001_add_is_active_to_simulations.py`
2. Or run SQL directly:
   ```sql
   ALTER TABLE simulations ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
   UPDATE simulations SET is_active = TRUE WHERE is_active IS NULL;
   ```

## Initial Schema

For the complete database schema, see `database_schema.sql` in the backend directory.
