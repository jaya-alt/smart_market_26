"""
Central configuration for the Supermarket Ops Agent.

Everything here is either a fixed relative path inside the project
or read from an environment variable with a safe default. No API
keys or secrets live in this file -- those stay in .env (see
.env.example) and are loaded by python-dotenv where needed.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ============================================================
# BASE PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

GENERATED_DIR = BASE_DIR / "generated"
INVOICE_DIR = GENERATED_DIR / "invoices"
REPORT_DIR = GENERATED_DIR / "reports"

for _dir in (GENERATED_DIR, INVOICE_DIR, REPORT_DIR):
    _dir.mkdir(parents=True, exist_ok=True)


# ============================================================
# DATABASE
# ============================================================
#
# Defaults to a local SQLite file so the project runs with zero
# extra setup. Point DATABASE_URL at a Postgres instance (e.g.
# postgresql+psycopg2://user:pass@host:5432/dbname) for production
# use without changing any code.

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{(BASE_DIR / 'supermarket.db').as_posix()}"
)


# ============================================================
# LLM / AGENT
# ============================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
AGENT_MAX_ITERATIONS = int(os.getenv("AGENT_MAX_ITERATIONS", "10"))


# ============================================================
# TELEGRAM
# ============================================================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


# ============================================================
# STORE / INVOICE BRANDING (safe to keep defaults)
# ============================================================

STORE_NAME = os.getenv("STORE_NAME", "SUPER MARKET")
STORE_ADDRESS = os.getenv("STORE_ADDRESS", "")
STORE_GSTIN = os.getenv("STORE_GSTIN", "")
STORE_PHONE = os.getenv("STORE_PHONE", "")
