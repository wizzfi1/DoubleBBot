# core/session_filter.py

from datetime import datetime, timezone
from config.settings import LONDON_SESSION, NEWYORK_SESSION

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
