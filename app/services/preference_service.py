from app.database.db import SessionLocal
from app.database.models import Preference


def set_preference(key, value):
    db = SessionLocal()

    try:
        if not key or not key.strip():
            return {
                "success": False,
                "message": "Preference key is required."
            }

        if value is None or str(value).strip() == "":
            return {
                "success": False,
                "message": "Preference value is required."
            }

        key = key.strip()
        value = str(value).strip()

        preference = (
            db.query(Preference)
            .filter(Preference.key == key)
            .first()
        )

        if preference:
            preference.value = value
        else:
            preference = Preference(
                key=key,
                value=value
            )
            db.add(preference)

        db.commit()

        return {
            "success": True,
            "message": "Preference saved successfully.",
            "key": key,
            "value": value
        }

    except Exception as e:
        db.rollback()

        return {
            "success": False,
            "message": str(e)
        }

    finally:
        db.close()


def get_preference(key):
    db = SessionLocal()

    try:
        preference = (
            db.query(Preference)
            .filter(Preference.key == key.strip())
            .first()
        )

        if not preference:
            return {
                "success": False,
                "message": f"No preference found for '{key}'."
            }

        return {
            "success": True,
            "key": preference.key,
            "value": preference.value
        }

    finally:
        db.close()


def get_all_preferences():
    db = SessionLocal()

    try:
        preferences = db.query(Preference).all()

        return {
            "success": True,
            "preferences": {
                preference.key: preference.value
                for preference in preferences
            }
        }

    finally:
        db.close()
        