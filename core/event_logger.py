from datetime import datetime, timezone
from core.notifier import send


def timestamp():
    return datetime.now(timezone.utc).strftime("%H:%M:%S UTC")


def log_levels(symbol, pdh, pdl):
    send(
        f"📏 *{symbol} — DAILY LEVELS*\n"
        f"PDH: `{pdh:.5f}`\n"
        f"PDL: `{pdl:.5f}`\n"
        f"{timestamp()}"
    )


def log_pdh_taken(symbol, price, pdh):
    send(
        f"🚨 *{symbol} — PDH SWEPT*\n"
        f"High: `{price:.5f}`\n"
        f"PDH: `{pdh:.5f}`\n"
        f"Waiting for M5 structure…\n"
        f"{timestamp()}"
    )


def log_pdl_taken(symbol, price, pdl):
    send(
        f"🚨 *{symbol} — PDL SWEPT*\n"
        f"Low: `{price:.5f}`\n"
        f"PDL: `{pdl:.5f}`\n"
        f"Waiting for M5 structure…\n"
        f"{timestamp()}"
    )


def log_double_break(symbol, direction, breaks):
    send(
        f"🧱 *{symbol} — DOUBLE BREAK CONFIRMED*\n"
        f"Direction: {direction}\n"
        f"Breaks: {breaks}\n"
        f"{timestamp()}"
    )


def log_entry(symbol, direction, entry, sl, tp, rr):
    send(
        f"🎯 *{symbol} — ENTRY CONFIRMED*\n"
        f"Direction: {direction}\n"
        f"Entry: `{entry:.5f}`\n"
        f"SL: `{sl:.5f}`\n"
        f"TP: `{tp:.5f}`\n"
        f"RR: `{rr:.2f}R`\n"
        f"{timestamp()}"
    )


def log_flip(symbol, direction, entry, sl, tp, rr):
    send(
        f"🔁 *{symbol} — FLIP CONFIRMED*\n"
        f"Direction: {direction}\n"
        f"Entry: `{entry:.5f}`\n"
        f"SL: `{sl:.5f}`\n"
        f"TP: `{tp:.5f}`\n"
        f"RR: `{rr:.2f}R`\n"
        f"{timestamp()}"
    )
