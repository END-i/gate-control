# Alembic Bootstrap Commands

Run from project root.

1. Initialize Alembic:

```bash
backend/.venv/bin/python -m alembic -c backend/alembic.ini init backend/alembic
```

2. Generate first migration after setting `sqlalchemy.url` and importing model metadata in `alembic/env.py`:

```bash
backend/.venv/bin/python -m alembic -c backend/alembic.ini revision --autogenerate -m "initial schema"
```

3. Apply migration:

```bash
backend/.venv/bin/python -m alembic -c backend/alembic.ini upgrade head
```
