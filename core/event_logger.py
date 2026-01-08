# core/event_logger.py

from datetime import datetime, timezone
from core.notifier import send


# =========================
# TIME UTILITY
# =========================
def timestamp():
    return datetime.now(timezone.utc).strftime("%H:%M:%S UTC")


# =========================
# LIQUIDITY EVENTS
# =========================
def log_pdh_taken(symbol, price):
    send(
        f"📌 *{symbol} — PDH TAKEN*\n"
        f"Price swept PDH at {price}\n"
        f"Waiting for M5 structure…\n"
        f"{timestamp()}"
    )


def log_pdl_taken(symbol, price):
    send(
        f"📌 *{symbol} — PDL TAKEN*\n"
        f"Price swept PDL at {price}\n"
        f"Waiting for M5 structure…\n"
        f"{timestamp()}"
    )


# =========================
# STRUCTURE
# =========================
def log_double_break(symbol, direction, breaks):
    send(
        f"🧱 *{symbol} — DOUBLE BREAK CONFIRMED*\n"
        f"Direction: {direction}\n"
        f"Break count: {breaks}\n"
        f"{timestamp()}"
    )


# =========================
# ENTRY
# =========================
def log_entry(symbol, direction, entry, sl, tp, rr):
    send(
        f"🎯 *{symbol} — ENTRY PLACED*\n"
        f"Direction: {direction}\n"
        f"Entry: {entry}\n"
        f"SL: {sl}\n"
        f"TP: {tp}\n"
        f"RR: {rr:.2f}R\n"
        f"{timestamp()}"
    )


# =========================
# STOP LOSS
# =========================
def log_sl(symbol, direction, price):
    send(
        f"🛑 *{symbol} — STOP LOSS HIT*\n"
        f"Direction: {direction}\n"
        f"Exit price: {price}\n"
        f"{timestamp()}"
    )


# =========================
# FLIP
# =========================
def log_flip(symbol, direction, entry, sl, tp, rr):
    send(
        f"🔁 *{symbol} — FLIP TRADE PLACED*\n"
        f"Direction: {direction}\n"
        f"Entry: {entry}\n"
        f"SL: {sl}\n"
        f"TP: {tp}\n"
        f"RR: {rr:.2f}R\n"
        f"{timestamp()}"
    )
