"""Alembic environment configuration for Cognitude LLM monitoring platform."""
import os
import sys
sys.path.append(os.getcwd())

from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from alembic import context

import sys
from os.path import abspath, dirname
sys.path.insert(0, dirname(dirname(abspath(__file__))))

# Import your models for autogenerate support
from app.database import Base
from app.models import *


@compiles(JSONB, "sqlite")
def _jsonb_sqlite(element, compiler, **kw):
    """Allow migrations to run against SQLite by mapping JSONB to JSON."""
    return "JSON"

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata for autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Use DATABASE_URL from environment if available, fallback to config
    database_url = os.getenv("DATABASE_URL")
    
    if database_url:
        # Use the DATABASE_URL from environment
        from sqlalchemy import create_engine
        connectable = create_engine(database_url)
    else:
        # Fallback to alembic.ini configuration
        connectable = engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
