
from __future__ import with_statement
import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
fileConfig(config.config_file_name)

# add project's path so imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables from .env so Alembic honors the project's config
try:
    # python-dotenv is already a dependency in requirements.txt
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # If python-dotenv isn't available, rely on actual environment variables
    pass

# Import your model's MetaData object here
from database import SQLALCHEMY_DATABASE_URL, Base
import models

# Prefer explicit environment variable DATABASE_URL or SQLALCHEMY_DATABASE_URL
env_db_url = os.getenv('DATABASE_URL') or os.getenv('SQLALCHEMY_DATABASE_URL')

target_metadata = models.Base.metadata


def run_migrations_offline():
    # Prefer env var if present, otherwise fall back to alembic.ini or database.py
    url = env_db_url or config.get_main_option("sqlalchemy.url") or SQLALCHEMY_DATABASE_URL
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    configuration = config.get_section(config.config_ini_section)
    # Allow environment variables (.env) to override the ini file
    configuration['sqlalchemy.url'] = env_db_url or configuration.get('sqlalchemy.url', SQLALCHEMY_DATABASE_URL)

    connectable = engine_from_config(
        configuration,
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
