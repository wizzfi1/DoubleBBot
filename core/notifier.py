# notifications/telegram.py
from datetime import datetime

import requests

# 🔴 FILL THESE
TELEGRAM_TOKEN = "7723542142:AAE7krpSyFLRHRuJW9k82-JtOiV_MZokjN0"
CHAT_ID = "640925280"


def send(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print("Telegram error:", e)


def timestamp():
    return datetime.utcnow().strftime("%H:%M:%S")