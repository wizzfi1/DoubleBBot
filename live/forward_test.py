import sys
import os
import time
from datetime import datetime, timezone, timedelta

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import MetaTrader5 as mt5
import pandas as pd

from config.settings import SYMBOL
from core.mt5_connector import connect
from core.session_filter import in_session, get_session
from core.news_blackout import in_news_blackout
from core.double_break_detector import DoubleBreakDetector
from core.entry_engine import EntryEngine
from core.risk_manager import RiskManager
from execution.orders import OrderExecutor
from core.event_context import EventContext
from core.event_logger import (
    log_levels,
    log_pdh_taken,
    log_pdl_taken,
    log_double_break,
    log_entry,
    log_flip,
)
from core.notifier import send


# =============================
# CONFIG
# =============================
ENABLE_TRADING = True
ENABLE_FLIP = True
CHECK_INTERVAL = 10


# =============================
# INIT
# =============================
connect(SYMBOL)

entry_engine = EntryEngine(SYMBOL)
risk_manager = RiskManager(SYMBOL)
executor = OrderExecutor(SYMBOL)

event = EventContext()

send(
    "🚀 *Live Demo Trading Started*\n"
    f"Symbol: {SYMBOL}\n"
    "Risk: $3000\n"
    "TP: Previous-Day PDH / PDL\n"
    "Flip: LIMIT | RR ≥ 5"
)

# =============================
# DAILY LEVEL LOG STATE
# =============================
last_levels_date = None


# =============================
# HELPERS
# =============================
def get_previous_day_levels(h1):
    h1 = h1.copy()
    h1["date"] = h1["time"].dt.date
    prev = datetime.now(timezone.utc).date() - timedelta(days=1)
    day = h1[h1["date"] == prev]
    if day.empty:
        return None, None
    return day["high"].max(), day["low"].min()


def last_closed_trade():
    deals = mt5.history_deals_get(
        datetime.now(timezone.utc) - timedelta(hours=12),
        datetime.now(timezone.utc),
    )
    if not deals:
        return None
    deals = [d for d in deals if d.symbol == SYMBOL]
    return sorted(deals, key=lambda d: d.time, reverse=True)[0] if deals else None


# =============================
# MAIN LOOP
# =============================
while True:
    now = datetime.now(timezone.utc)

    if not in_session(now) or in_news_blackout(SYMBOL, now):
        time.sleep(CHECK_INTERVAL)
        continue

    m5 = pd.DataFrame(mt5.copy_rates_from_pos(SYMBOL, mt5.TIMEFRAME_M5, 0, 300))
    h1 = pd.DataFrame(mt5.copy_rates_from_pos(SYMBOL, mt5.TIMEFRAME_H1, 0, 72))

    if m5.empty or h1.empty:
        time.sleep(CHECK_INTERVAL)
        continue

    m5["time"] = pd.to_datetime(m5["time"], unit="s", utc=True)
    h1["time"] = pd.to_datetime(h1["time"], unit="s", utc=True)

    last = m5.iloc[-1]
    pdh, pdl = get_previous_day_levels(h1)

    if pdh is None:
        time.sleep(CHECK_INTERVAL)
        continue

   
    today = datetime.now(timezone.utc).date()

    if last_levels_date != today:
        log_levels(SYMBOL, pdh, pdl)
        last_levels_date = today


    # =============================
    # ARM EVENT
    # =============================
    if not event.active:
        if last["high"] >= pdh:
            event.arm(
                detector=DoubleBreakDetector(pdh, "SELL"),
                direction="SELL",
                flip_direction="BUY",
                tp=pdl,
                session=get_session(last["time"]),
            )
            log_pdh_taken(SYMBOL, last["high"], pdh)

        elif last["low"] <= pdl:
            event.arm(
                detector=DoubleBreakDetector(pdl, "BUY"),
                direction="BUY",
                flip_direction="SELL",
                tp=pdh,
                session=get_session(last["time"]),
            )
            log_pdl_taken(SYMBOL, last["low"], pdl)

    # =============================
    # PRIMARY
    # =============================
    if event.allow_primary:
        idx = event.detector.update(m5, len(m5) - 1)
        if idx is not None:
            plan = entry_engine.build_trade_plan(
                type("Signal", (), {"direction": event.direction})(),
                event.tp_level,
            )

            rr = abs(event.tp_level - plan.entry_price) / abs(
                plan.entry_price - plan.stop_loss
            )

            if not plan.valid or rr < 5:
                event.resolve()
                continue

            lot = risk_manager.calculate_lot_size(
                plan.entry_price, plan.stop_loss
            )

            ticket = executor.place_limit(
                plan.direction,
                lot,
                plan.entry_price,
                plan.stop_loss,
                event.tp_level,
                is_flip=False
            )


            if ticket:
                log_double_break(SYMBOL, event.direction, event.detector.breaks)
                log_entry(
                    SYMBOL, plan.direction,
                    plan.entry_price, plan.stop_loss, event.tp_level, rr
                )
                event.primary_placed(ticket)

    # =============================
    # FLIP
    # =============================
    if ENABLE_FLIP and event.allow_flip:
        deal = last_closed_trade()
        if deal and deal.position_id == event.primary_ticket:
            if deal.reason == mt5.DEAL_REASON_SL and get_session(
                datetime.fromtimestamp(deal.time, timezone.utc)
            ) == event.session:

                plan = entry_engine.build_trade_plan(
                    type("Signal", (), {"direction": event.flip_direction})(),
                    event.tp_level,
                )

                rr = abs(event.tp_level - plan.entry_price) / abs(
                    plan.entry_price - plan.stop_loss
                )

                if plan.valid and rr >= 5:
                    lot = risk_manager.calculate_lot_size(
                        plan.entry_price, plan.stop_loss
                    )
                    ticket = executor.place_limit(
                        plan.direction, lot,
                        plan.entry_price, plan.stop_loss, event.tp_level
                    )
                    if ticket:
                        log_flip(
                            SYMBOL, plan.direction,
                            plan.entry_price, plan.stop_loss, event.tp_level, rr
                        )
                        event.flip_placed()

                event.resolve()

    time.sleep(CHECK_INTERVAL)
