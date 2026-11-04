from datetime import date


def has_medical_review(record):
    if not record or record.get("review_status") != "approved":
        return False

    reviewed_by = record.get("reviewed_by")
    reviewed_at = record.get("reviewed_at")
    source = record.get("source")
    if not all(isinstance(value, str) and value.strip() for value in (reviewed_by, reviewed_at, source)):
        return False

    try:
        date.fromisoformat(reviewed_at)
    except ValueError:
        return False

    return True
