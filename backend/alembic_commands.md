# Alembic Bootstrap Commands

Run from backend directory.

1. Initialize Alembic:

```bash
alembic init alembic
```

2. Generate first migration after setting `sqlalchemy.url` and importing model metadata in `alembic/env.py`:

```bash
alembic revision --autogenerate -m "initial schema"
```

3. Apply migration:

```bash
alembic upgrade head
```
