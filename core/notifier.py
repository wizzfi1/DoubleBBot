# telegram.py
import requests
import os

from notifications.telegram import send

from config.env import env
# =============================
# CONFIG (KEEP SECRETS HERE)
# =============================

# Option 1 (RECOMMENDED): environment variables
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Option 2 (fallback – only if you insist)
# BOT_TOKEN = "YOUR_BOT_TOKEN"
# CHAT_ID = "YOUR_CHAT_ID"


# =============================
# CORE SEND FUNCTION
# =============================

def send(message: str):
    """
    Sends a Telegram message to the configured chat.
    Safe to call from anywhere.
    """
    if not BOT_TOKEN or not CHAT_ID:
        print("⚠️ Telegram not configured (missing token or chat id)")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }

    try:
        r = requests.post(url, json=payload, timeout=5)
        if r.status_code != 200:
            print(f"❌ Telegram error: {r.text}")
    except Exception as e:
        print(f"❌ Telegram send failed: {e}")
