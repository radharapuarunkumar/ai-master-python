"""Alembic environment configuration — async SQLAlchemy + asyncpg.

This module is executed by Alembic whenever you run a migration command.
It wires up the async engine, imports every model so that ``Base.metadata``
is fully populated, and delegates to either the *offline* (SQL script) or
*online* (live DB connection) migration runner.
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

# ---------------------------------------------------------------------------
# Import the declarative Base so Alembic knows about every table.
# Make sure every model module is imported here (or via app.models.__init__)
# so that Base.metadata.tables is fully populated before autogenerate runs.
# ---------------------------------------------------------------------------
from app.models.base import Base  # noqa: F401 — side-effect import

# Import all model modules to register them with Base.metadata
import app.models  # noqa: F401 — triggers __init__.py which imports all models

# Import settings to read DATABASE_URL from .env / environment
from app.config import settings

# ---------------------------------------------------------------------------
# Alembic Config object — provides access to values in alembic.ini
# ---------------------------------------------------------------------------
config = context.config

# Set up Python logging from the alembic.ini [loggers] section
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override the placeholder sqlalchemy.url with the real DATABASE_URL
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# This is the metadata Alembic will compare against the live database
# when you run `alembic revision --autogenerate`.
target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Offline migrations — generate raw SQL without connecting to the DB
# ---------------------------------------------------------------------------
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Configures the context with just a URL (no Engine needed).
    Calls to ``context.execute()`` emit the given SQL string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Compare types (e.g. VARCHAR(100) → VARCHAR(255)) during autogenerate
        compare_type=True,
        # Compare server defaults during autogenerate
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online migrations — connect to the database via asyncpg
# ---------------------------------------------------------------------------
def do_run_migrations(connection) -> None:  # noqa: ANN001
    """Helper executed inside the async connection context."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations within a connection."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # short-lived migration connection
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using an async engine."""
    asyncio.run(run_async_migrations())


# ---------------------------------------------------------------------------
# Entry point — Alembic calls this when executing any migration command
# ---------------------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
