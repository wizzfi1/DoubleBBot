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
from core.event_logger import (
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

send(
    "🚀 *Live Demo Trading Started*\n"
    f"Symbol: {SYMBOL}\n"
    "Risk: $3000\n"
    "TP: Previous-Day PDH / PDL\n"
    "Flip: LIMIT | RR ≥ 5"
)


# =============================
# STRATEGY STATE (CRITICAL)
# =============================
active_event = False        # 🔒 one liquidity event at a time
detector = None

trade_taken = False
flip_used = False

current_direction = None
flip_direction = None
tp_level = None
trade_session = None

last_primary_ticket = None


# =============================
# HELPERS
# =============================
def get_previous_day_levels(h1_df: pd.DataFrame):
    """
    Returns PDH / PDL for the previous UTC calendar day.
    """
    h1_df = h1_df.copy()
    h1_df["date"] = h1_df["time"].dt.date

    today = datetime.now(timezone.utc).date()
    prev_day = today - timedelta(days=1)

    prev = h1_df[h1_df["date"] == prev_day]

    if prev.empty:
        return None, None

    return prev["high"].max(), prev["low"].min()


def get_last_closed_trade():
    deals = mt5.history_deals_get(
        datetime.now(timezone.utc) - timedelta(hours=12),
        datetime.now(timezone.utc),
    )

    if not deals:
        return None

    deals = [d for d in deals if d.symbol == SYMBOL]
    if not deals:
        return None

    return sorted(deals, key=lambda d: d.time, reverse=True)[0]


# =============================
# MAIN LOOP
# =============================
while True:
    now = datetime.now(timezone.utc)

    # ---------------------------
    # SESSION FILTER
    # ---------------------------
    if not in_session(now):
        time.sleep(CHECK_INTERVAL)
        continue

    # ---------------------------
    # NEWS BLACKOUT
    # ---------------------------
    if in_news_blackout(SYMBOL, now):
        time.sleep(CHECK_INTERVAL)
        continue

    # ---------------------------
    # FETCH DATA
    # ---------------------------
    rates_m5 = mt5.copy_rates_from_pos(SYMBOL, mt5.TIMEFRAME_M5, 0, 300)
    rates_h1 = mt5.copy_rates_from_pos(SYMBOL, mt5.TIMEFRAME_H1, 0, 72)

    if rates_m5 is None or rates_h1 is None:
        time.sleep(CHECK_INTERVAL)
        continue

    m5 = pd.DataFrame(rates_m5)
    h1 = pd.DataFrame(rates_h1)

    m5["time"] = pd.to_datetime(m5["time"], unit="s", utc=True)
    h1["time"] = pd.to_datetime(h1["time"], unit="s", utc=True)

    last = m5.iloc[-1]
    last_time = last["time"]

    # =============================
    # PREVIOUS-DAY PDH / PDL
    # =============================
    pdh, pdl = get_previous_day_levels(h1)

    if pdh is None or pdl is None:
        time.sleep(CHECK_INTERVAL)
        continue

    # =============================
    # ARM LIQUIDITY EVENT (ONE ONLY)
    # =============================
    if not active_event:
        if last["high"] >= pdh:
            active_event = True
            detector = DoubleBreakDetector(pdh, "SELL")

            current_direction = "SELL"
            flip_direction = "BUY"
            tp_level = pdl
            trade_session = get_session(last_time)

            log_pdh_taken(SYMBOL, last["high"])

        elif last["low"] <= pdl:
            active_event = True
            detector = DoubleBreakDetector(pdl, "BUY")

            current_direction = "BUY"
            flip_direction = "SELL"
            tp_level = pdh
            trade_session = get_session(last_time)

            log_pdl_taken(SYMBOL, last["low"])

    # =============================
    # PRIMARY ENTRY
    # =============================
    if detector and not trade_taken:
        entry_index = detector.update(m5, len(m5) - 1)

        if entry_index is not None:
            trade_taken = True

            class Signal:
                pass

            Signal.direction = current_direction
            plan = entry_engine.build_trade_plan(Signal(), tp_level)

            if not plan.valid:
                continue

            rr = abs(tp_level - plan.entry_price) / abs(
                plan.entry_price - plan.stop_loss
            )

            log_double_break(SYMBOL, current_direction, detector.breaks)
            log_entry(
                SYMBOL,
                current_direction,
                plan.entry_price,
                plan.stop_loss,
                tp_level,
                rr,
            )

            if ENABLE_TRADING:
                lot = risk_manager.calculate_lot_size(
                    plan.entry_price, plan.stop_loss
                )

                ticket = executor.place_limit(
                    direction=plan.direction,
                    lot=lot,
                    entry=plan.entry_price,
                    sl=plan.stop_loss,
                    tp=tp_level,
                )

                last_primary_ticket = ticket

    # =============================
    # FLIP MONITOR (LIMIT | RR ≥ 5)
    # =============================
    if ENABLE_FLIP and trade_taken and not flip_used:
        deal = get_last_closed_trade()

        if deal and deal.position_id == last_primary_ticket:
            if deal.reason == mt5.DEAL_REASON_SL:
                exit_time = datetime.fromtimestamp(deal.time, timezone.utc)

                if get_session(exit_time) == trade_session:
                    class FlipSignal:
                        pass

                    FlipSignal.direction = flip_direction
                    flip_plan = entry_engine.build_trade_plan(
                        FlipSignal(), tp_level
                    )

                    if flip_plan.valid:
                        flip_rr = abs(tp_level - flip_plan.entry_price) / abs(
                            flip_plan.entry_price - flip_plan.stop_loss
                        )

                        if flip_rr >= 5:
                            lot = risk_manager.calculate_lot_size(
                                flip_plan.entry_price,
                                flip_plan.stop_loss,
                            )

                            executor.place_limit(
                                direction=flip_plan.direction,
                                lot=lot,
                                entry=flip_plan.entry_price,
                                sl=flip_plan.stop_loss,
                                tp=tp_level,
                            )

                            log_flip(
                                SYMBOL,
                                flip_plan.direction,
                                flip_plan.entry_price,
                                flip_plan.stop_loss,
                                tp_level,
                                flip_rr,
                            )

                    flip_used = True

    # =============================
    # EVENT RESET (ONLY HERE)
    # =============================
    if detector and detector.completed:
        active_event = False
        detector = None

        trade_taken = False
        flip_used = False
        last_primary_ticket = None

    time.sleep(CHECK_INTERVAL)
