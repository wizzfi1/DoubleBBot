# core/session_filter.py

from datetime import datetime, timezone
from config.settings import LONDON_SESSION, NEWYORK_SESSION


# =============================
# INTERNAL HELPERS
# =============================
def _in_session(now, session):
    start, end = session
    return start <= now.time() <= end


# =============================
# PUBLIC API (USE THESE)
# =============================
def in_session(dt):
    """
    Returns True if dt is within London or New York session.
    """
    return (
        _in_session(dt, LONDON_SESSION)
        or _in_session(dt, NEWYORK_SESSION)
    )


def get_session(dt):
    """
    Returns session name: 'LONDON', 'NY', or None
    """
    if _in_session(dt, LONDON_SESSION):
        return "LONDON"
    if _in_session(dt, NEWYORK_SESSION):
        return "NY"
    return None


def session_allowed():
    """
    Backward compatibility helper (optional).
    """
    now = datetime.now(timezone.utc)
    return get_session(now)
