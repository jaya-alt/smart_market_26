"""
Create all database tables (idempotent -- safe to re-run; it only
creates tables that don't already exist, it never drops or alters
existing ones).

Usage:
    python init_db.py            # create tables
    python -m app.database.seed  # optionally load sample products
"""

from app.database.db import engine, Base
from app.database import models  # noqa: F401  (import registers the models)

Base.metadata.create_all(bind=engine)

print("Database ready (tables created if they did not already exist).")
