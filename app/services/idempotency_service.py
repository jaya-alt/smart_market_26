"""
Idempotency guard for inbound messages from any channel.

Telegram's own delivery guarantees are "at least once" -- a network
retry, or the bot restarting mid-poll, can hand the same update to
the process twice. Without a guard, that would mean the agent runs
twice for the same message, which for a supermarket ops agent means
a real risk of double-billing or double-crediting khata. This module
records every update we've started processing so a duplicate can be
detected and skipped before it ever reaches the agent.
"""

from app.database.db import SessionLocal
from app.database.models import ProcessedUpdate


def is_duplicate(source, update_id):
    """
    Returns True and records the update if it has NOT been seen
    before (i.e. False means "go ahead, this is new"). Returns True
    if it HAS already been processed, so the caller should skip it.
    """

    db = SessionLocal()

    try:
        existing = (
            db.query(ProcessedUpdate)
            .filter(
                ProcessedUpdate.source == source,
                ProcessedUpdate.update_id == str(update_id)
            )
            .first()
        )

        if existing:
            return True

        db.add(ProcessedUpdate(source=source, update_id=str(update_id)))
        db.commit()

        return False

    except Exception:
        db.rollback()
        # Fail open: if the idempotency check itself breaks, we'd
        # rather still answer the owner's message than silently
        # drop it. The unique constraint on (source, update_id)
        # still protects against a literal duplicate INSERT.
        return False

    finally:
        db.close()
