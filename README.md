# QR Karaoke Backend

This repository contains the backend for the QR Karaoke system (FastAPI + SQLAlchemy).

Quick local dev notes

1. Activate the virtual environment (Windows PowerShell):

```powershell
& .venv\Scripts\Activate.ps1
```

2. Install dependencies (if not already):

```powershell
pip install -r requirements.txt
```

3. If you've pulled changes that include DB schema updates, run the migration helper once to ensure the SQLite schema is compatible:

```powershell
python apply_migration.py
```

This script performs a minimal schema check and will add the `stock` column to the `productos` table if missing. It's intentionally minimal: for production or frequent schema changes, use a proper migration tool.

4. Start the app (development):

```powershell
python -m uvicorn main:app --reload --host 0.0.0.0
```

Recommendation: Use Alembic for migrations

- For any non-trivial project you should use Alembic to manage schema migrations. Alembic will let you generate, apply, and roll back migrations safely and is the standard approach with SQLAlchemy.
- If you'd like, I can scaffold Alembic in this repo and create an initial migration for the current models so future schema changes are tracked reliably.

If you want me to add Alembic scaffolding and a starter migration, say so and I'll implement it next.

Alembic usage (now scaffolded)

- Create a new revision after you change models:

```powershell
.venv\Scripts\Activate.ps1
alembic revision --autogenerate -m "describe change"
```

- Apply migrations to the DB:

```powershell
alembic upgrade head
```

- Inspect current revision:

```powershell
alembic current
```

Notes:
- The Alembic env is configured to use the project's `SQLALCHEMY_DATABASE_URL` defined in `database.py`.
- I added an initial empty revision (it marks the current state). Autogenerate will create migrations for subsequent model changes.

Environment variables and .env

- Alembic's `env.py` will attempt to load a local `.env` file (using `python-dotenv`) when you run alembic commands. If a `DATABASE_URL` or `SQLALCHEMY_DATABASE_URL` environment variable is present it will be used as the database URL for migrations. Otherwise Alembic falls back to `alembic.ini` or the project `database.py` setting.

Make sure `python-dotenv` is installed in the environment (it's included in `requirements.txt`) if you plan to rely on a `.env` file.
