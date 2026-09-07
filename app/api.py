"""
Legacy entrypoint, kept for backward compatibility with anything
that runs `uvicorn app.api:app`.

app/main.py is the canonical, actively maintained FastAPI app (chat,
inventory, billing, khata, invoices, reports, file downloads). This
module just re-exports it so both entrypoints work identically and
there is only one implementation to keep correct.
"""

from app.main import app  # noqa: F401

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.api:app", host="127.0.0.1", port=8000, reload=True)
