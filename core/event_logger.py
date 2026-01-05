# core/event_logger.py

from core.notifier import send, timestamp


def log_pdh_taken(symbol, price):
    send(
        f"📌 *{symbol} — PDH TAKEN*\n"
        f"Price swept PDH at `{price}`\n"
        f"Waiting for M5 structure…\n"
        f"`{timestamp()} UTC`"
    )


def log_pdl_taken(symbol, price):
    send(
        f"📌 *{symbol} — PDL TAKEN*\n"
        f"Price swept PDL at `{price}`\n"
        f"Waiting for M5 structure…\n"
        f"`{timestamp()} UTC`"
    )


def log_double_break(symbol, direction, breaks):
    send(
        f"🔍 *{symbol} — DOUBLE BREAK ({direction})*\n"
        f"Breaks: {breaks}\n"
        f"Waiting for entry candle…\n"
        f"`{timestamp()} UTC`"
    )


def log_entry(symbol, direction, entry, sl, tp, rr):
    send(
        f"🚀 *{symbol} — {direction} ENTRY*\n"
        f"Entry: `{entry}`\n"
        f"SL: `{sl}`\n"
        f"TP: `{tp}`\n"
        f"RR: `{rr:.2f}R`\n"
        f"`{timestamp()} UTC`"
    )


def log_sl(symbol):
    send(
        f"❌ *{symbol} — STOP LOSS HIT*\n"
        f"Primary trade invalidated\n"
        f"`{timestamp()} UTC`"
    )


def log_flip(symbol, direction, rr, session):
    send(
        f"🔁 *{symbol} — FLIP EXECUTED ({direction})*\n"
        f"*Reason:*\n"
        f"• Clean SL on primary\n"
        f"• Same session ({session})\n"
        f"• RR = `{rr:.2f}R`\n"
        f"`{timestamp()} UTC`"
    )
