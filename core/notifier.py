# core/notifier.py

from datetime import datetime, timezone

# IMPORT YOUR EXISTING TELEGRAM MODULE
from notifications.telegram import send as telegram_send
# ⬆️ adjust this import path ONLY if needed:
# from notifications.telegram import send as telegram_send


def timestamp():
    return datetime.now(timezone.utc).strftime("%H:%M:%S UTC")


def send(message: str):
    telegram_send(message)
