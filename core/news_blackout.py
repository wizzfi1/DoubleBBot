# core/news_blackout.py

from datetime import datetime, timedelta

# HARD-CODED HIGH IMPACT EVENTS (UTC)
# Replace or automate later if needed
HIGH_IMPACT_EVENTS = [
    # Example:
    # ("USD", datetime(2024, 6, 14, 12, 30)),  # CPI
]

BLACKOUT_MINUTES = 15


def in_news_blackout(symbol, now=None):
    """
    Returns True if within blackout window of high-impact news
    """
    if now is None:
        now = datetime.utcnow()

    currency = symbol[:3]  # EURUSD → EUR

    for curr, event_time in HIGH_IMPACT_EVENTS:
        if curr in symbol:
            if abs((now - event_time).total_seconds()) <= BLACKOUT_MINUTES * 60:
                return True

    return False
