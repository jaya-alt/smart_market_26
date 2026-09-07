from datetime import datetime, date, timedelta


def parse_natural_date(date_input=None):
    """
    Convert natural language date input into a Python date object.

    Supported examples:
    - today
    - yesterday
    - tomorrow
    - 2026-09-03
    - September 3
    - Sep 3
    """

    if not date_input:
        return date.today()

    if isinstance(date_input, date):
        return date_input

    date_text = str(date_input).strip().lower()

    # ========================================================
    # TODAY
    # ========================================================

    if date_text == "today":
        return date.today()

    # ========================================================
    # YESTERDAY
    # ========================================================

    if date_text == "yesterday":
        return date.today() - timedelta(days=1)

    # ========================================================
    # TOMORROW
    # ========================================================

    if date_text == "tomorrow":
        return date.today() + timedelta(days=1)

    # ========================================================
    # YYYY-MM-DD
    # ========================================================

    try:
        return datetime.strptime(
            date_text,
            "%Y-%m-%d"
        ).date()

    except ValueError:
        pass

    # ========================================================
    # MONTH DAY YEAR
    # Example: September 3 2026
    # ========================================================

    formats = [
        "%B %d %Y",
        "%b %d %Y",
        "%d %B %Y",
        "%d %b %Y",
        "%B %d",
        "%b %d",
        "%d %B",
        "%d %b"
    ]

    for date_format in formats:

        try:
            parsed_date = datetime.strptime(
                date_input,
                date_format
            )

            # If year is not provided,
            # use the current year
            if parsed_date.year == 1900:

                parsed_date = parsed_date.replace(
                    year=date.today().year
                )

            return parsed_date.date()

        except ValueError:
            continue

    # ========================================================
    # INVALID DATE
    # ========================================================

    return None