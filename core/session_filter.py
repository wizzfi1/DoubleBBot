# core/session_filter.py

from datetime import datetime, timezone
from config.settings import LONDON_SESSION, NEWYORK_SESSION

<<<<<<< HEAD
def _in_session(now, session):
    start, end = session
    return start <= now.time() <= end

def session_allowed():
    now = datetime.now(timezone.utc)

    if _in_session(now, LONDON_SESSION):
        return "LONDON"

    if _in_session(now, NEWYORK_SESSION):
        return "NEWYORK"

    return None
=======

# =============================
# INTERNAL HELPERS
# =============================

def _in_session(now: datetime, session: tuple) -> bool:
    start, end = session
    return start <= now.time() <= end


def _in_london(now: datetime) -> bool:
    return _in_session(now, LONDON_SESSION)


def _in_newyork(now: datetime) -> bool:
    return _in_session(now, NEWYORK_SESSION)


# =============================
# PUBLIC API (USE THESE)
# =============================

def in_session(now: datetime) -> bool:
    """
    Returns True if current time is in London or NY session
    """
    return _in_london(now) or _in_newyork(now)


def get_session(now: datetime):
    """
    Returns session name or None
    """
    if _in_london(now):
        return "LONDON"
    if _in_newyork(now):
        return "NY"
    return None


def session_allowed():
    """
    Backward-compatible helper for older code
    """
    now = datetime.now(timezone.utc)
    return get_session(now)
>>>>>>> master
