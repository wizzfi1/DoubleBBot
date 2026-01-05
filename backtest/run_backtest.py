# backtest/run_backtest.py

ENABLE_FLIP = True   # <-- PRIMARY-ONLY MODE


import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import MetaTrader5 as mt5
import pandas as pd
import matplotlib.pyplot as plt
from datetime import time

from core.mt5_connector import connect
from core.entry_engine import EntryEngine
from config.settings import SYMBOL
from core.double_break_detector import DoubleBreakDetector

from core.news_blackout import in_news_blackout
from core.event_logger import (
    log_pdh_taken,
    log_pdl_taken,
    log_double_break,
    log_entry,
    log_sl,
    log_flip
)
# =============================
# BACKTEST CONFIG
# =============================
START_BARS = 30000
INITIAL_BALANCE = 100_000
RISK_PER_TRADE = 3000

RR_TARGET = 5
BE_RR = 4


# =============================
# SESSION FILTER
# =============================
LONDON_START = time(7, 0)
LONDON_END   = time(16, 0)

NY_START = time(13, 0)
NY_END   = time(21, 0)


def in_session(t):
    tm = t.time()
    return (
        LONDON_START <= tm <= LONDON_END or
        NY_START <= tm <= NY_END
    )

def get_session(t):
    tm = t.time()
    if LONDON_START <= tm <= LONDON_END:
        return "LONDON"
    if NY_START <= tm <= NY_END:
        return "NY"
    return None



# =============================
# DATA LOADERS
# =============================
def fetch_m5(symbol, bars):
    rates = mt5.copy_rates_from_pos(
        symbol,
        mt5.TIMEFRAME_M5,
        0,
        bars
    )
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    return df


def fetch_h1(symbol, bars):
    rates = mt5.copy_rates_from_pos(
        symbol,
        mt5.TIMEFRAME_H1,
        0,
        bars
    )
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    return df


# =============================
# BACKTEST ENGINE
# =============================
class Backtester:
    def __init__(self):
        self.balance = INITIAL_BALANCE
        self.equity = [INITIAL_BALANCE]
        self.trades = []

        self.entry_engine = EntryEngine(SYMBOL)

        self.stats = {
            "sell_trades": 0,
            "buy_trades": 0,
            "flip_trades": 0,
        }

    # -----------------------------------------
    def run(self):
        m5 = fetch_m5(SYMBOL, START_BARS)
        h1 = fetch_h1(SYMBOL, START_BARS // 12)

        if m5.empty or h1.empty:
            print("❌ No historical data")
            return

        h1.set_index("time", inplace=True)

        detector = None
        trade_taken = False
        flip_used = False

        for i in range(50, len(m5)):
            candle = m5.iloc[i]
            t = candle["time"]

            if not in_session(t):
                continue

            # -------------------------------
            # PDH / PDL from previous 24 H1 bars
            # -------------------------------
            h1_window = h1[h1.index < t].tail(24)
            if len(h1_window) < 24:
                continue

            pdh = h1_window["high"].max()
            pdl = h1_window["low"].min()

            # -------------------------------
            # ARM LIQUIDITY EVENT
            # -------------------------------
            if detector is None:
                # SELL SIDE (PDH taken)
                if candle["high"] >= pdh:
                    detector = DoubleBreakDetector(pdh, "SELL")
                    direction = "SELL"
                    tp_level = pdl
                    flip_direction = "BUY"

                # BUY SIDE (PDL taken)
                elif candle["low"] <= pdl:
                    detector = DoubleBreakDetector(pdl, "BUY")
                    direction = "BUY"
                    tp_level = pdh
                    flip_direction = "SELL"

            # -------------------------------
            # PATTERN TRACKING
            # -------------------------------
            if detector and not trade_taken:
                entry_index = detector.update(m5, i)

                if entry_index is not None:
                    trade_taken = True

                    class Signal:
                        pass

                    Signal.direction = direction
                    plan = self.entry_engine.build_trade_plan(
                        Signal(), tp_level
                    )

                    if not plan.valid:
                        detector = None
                        trade_taken = False
                        flip_used = False
                        continue

                    outcome = self.simulate_trade(
                        m5,
                        entry_index,
                        plan,
                        allow_flip=ENABLE_FLIP,
                        flip_used=flip_used,
                        flip_direction=flip_direction,
                        flip_tp=tp_level,
                    )

                    for trade in outcome["trades"]:
                        self.trades.append(trade)

                    self.balance += outcome["pnl"]
                    self.equity.append(self.balance)
                    
                    if in_news_blackout(SYMBOL, t.to_pydatetime()):
                        continue

                    if direction == "SELL":
                        self.stats["sell_trades"] += 1
                    else:
                        self.stats["buy_trades"] += 1

                    if outcome["flipped"]:
                        self.stats["flip_trades"] += 1

            # -------------------------------
            # RESET AFTER EVENT RESOLUTION
            # -------------------------------
            if detector and detector.completed:
                detector = None
                trade_taken = False
                flip_used = False

        self.export_results()

    # -----------------------------------------
    def simulate_trade(
        self,
        m5,
        entry_index,
        plan,
        allow_flip,
        flip_used,
        flip_direction,
        flip_tp,
    ):
        trades = []
        pnl = 0
        flipped = False

        # -------------------------------
        # PRIMARY TRADE
        # -------------------------------
        primary = self.manage_trade(m5, entry_index, plan)
        primary["record"]["is_flip"] = False
        trades.append(primary["record"])
        pnl += primary["pnl"]

        # -------------------------------
        # HARD FLIP GATE
        # -------------------------------
        if (
            not allow_flip or
            flip_used or
            primary["exit_reason"] != "SL"
        ):
            return {
                "trades": trades,
                "pnl": pnl,
                "flipped": False
            }

        # -------------------------------
        # SAME SESSION CHECK
        # -------------------------------
        primary_exit_time = m5.iloc[primary["exit_index"]]["time"]
        primary_session = get_session(m5.iloc[entry_index]["time"])
        exit_session = get_session(primary_exit_time)

        if primary_session is None or exit_session != primary_session:
            return {
                "trades": trades,
                "pnl": pnl,
                "flipped": False
            }

        # -------------------------------
        # BUILD FLIP PLAN
        # -------------------------------
        class FlipSignal:
            pass

        FlipSignal.direction = flip_direction
        flip_plan = self.entry_engine.build_trade_plan(
            FlipSignal(), flip_tp
        )

        if not flip_plan.valid:
            return {
                "trades": trades,
                "pnl": pnl,
                "flipped": False
            }

        # -------------------------------
        # 5R MINIMUM CHECK
        # -------------------------------
        flip_risk = abs(
            flip_plan.entry_price - flip_plan.stop_loss
        )

        if flip_risk <= 0:
            return {
                "trades": trades,
                "pnl": pnl,
                "flipped": False
            }

        flip_rr = abs(
            flip_tp - flip_plan.entry_price
        ) / flip_risk

        if flip_rr < 5:
            return {
                "trades": trades,
                "pnl": pnl,
                "flipped": False
            }

        # -------------------------------
        # EXECUTE FLIP (FULL $3000 RISK)
        # -------------------------------
        flip = self.manage_trade(
            m5,
            primary["exit_index"],
            flip_plan
        )
        flip["record"]["is_flip"] = True
        trades.append(flip["record"])
        pnl += flip["pnl"]
        flipped = True

        return {
            "trades": trades,
            "pnl": pnl,
            "flipped": flipped
        }

    # -----------------------------------------
    def manage_trade(self, m5, entry_index, plan):
        entry = plan.entry_price
        sl = plan.stop_loss
        risk = abs(entry - sl)

        if plan.direction == "SELL":
            tp = entry - risk * RR_TARGET
            be_level = entry - risk * BE_RR
        else:
            tp = entry + risk * RR_TARGET
            be_level = entry + risk * BE_RR

        sl_moved_to_be = False

        for j in range(entry_index + 1, len(m5)):
            row = m5.iloc[j]

            # ---------------------------
            # BE TRIGGER
            # ---------------------------
            if not sl_moved_to_be:
                if (
                    plan.direction == "SELL"
                    and row["low"] <= be_level
                ) or (
                    plan.direction == "BUY"
                    and row["high"] >= be_level
                ):
                    sl = entry
                    sl_moved_to_be = True

            # ---------------------------
            # SL
            # ---------------------------
            if (
                plan.direction == "SELL"
                and row["high"] >= sl
            ) or (
                plan.direction == "BUY"
                and row["low"] <= sl
            ):
                r = 0 if sl_moved_to_be else -1
                return {
                    "pnl": r * RISK_PER_TRADE,
                    "exit_reason": "BE" if sl_moved_to_be else "SL",
                    "exit_index": j,
                    "record": {
                        "direction": plan.direction,
                        "result": "BE" if sl_moved_to_be else "SL",
                        "R": r
                    }
                }

            # ---------------------------
            # TP
            # ---------------------------
            if (
                plan.direction == "SELL"
                and row["low"] <= tp
            ) or (
                plan.direction == "BUY"
                and row["high"] >= tp
            ):
                return {
                    "pnl": RR_TARGET * RISK_PER_TRADE,
                    "exit_reason": "TP",
                    "exit_index": j,
                    "record": {
                        "direction": plan.direction,
                        "result": "TP",
                        "R": RR_TARGET
                    }
                }

        return {
            "pnl": 0,
            "exit_reason": "NONE",
            "exit_index": len(m5) - 1,
            "record": {
                "direction": plan.direction,
                "result": "NONE",
                "R": 0
            }
        }

    # -----------------------------------------
    def export_results(self):
        df = pd.DataFrame(self.trades)

        print("\n📊 FINAL BACKTEST RESULTS")
        print(self.stats)

        if df.empty:
            print("❌ No trades")
            return

        df.to_csv("backtest_results.csv", index=False)

        winrate = (df["R"] > 0).mean()
        expectancy = df["R"].mean()

        print(f"Trades: {len(df)}")
        print(f"Winrate: {winrate:.2%}")
        print(f"Expectancy (R): {expectancy:.2f}")
        print(f"Final Balance: {self.balance:,.2f}")

        plt.figure(figsize=(10, 5))
        plt.plot(self.equity)
        plt.title("Equity Curve")
        plt.xlabel("Trades")
        plt.ylabel("Balance")
        plt.grid(True)
        plt.show()


        # ---------------------------
        # FLIP-ONLY STATISTICS
        # ---------------------------
        flips = df[df["is_flip"] == True]
        primaries = df[df["is_flip"] == False]

        print("\n--- PRIMARY vs FLIP BREAKDOWN ---")

        if not primaries.empty:
            print(
                f"Primary Trades: {len(primaries)} | "
                f"Winrate: {(primaries['R'] > 0).mean():.2%} | "
                f"Expectancy: {primaries['R'].mean():.2f}R"
            )

        if not flips.empty:
            print(
                f"Flip Trades: {len(flips)} | "
                f"Winrate: {(flips['R'] > 0).mean():.2%} | "
                f"Expectancy: {flips['R'].mean():.2f}R"
            )


        # ---------------------------
        # FLIP DRAWDOWN CONTRIBUTION
        # ---------------------------
        df["equity_step"] = df["R"] * RISK_PER_TRADE
        df["equity_curve"] = INITIAL_BALANCE + df["equity_step"].cumsum()

        df["peak"] = df["equity_curve"].cummax()
        df["drawdown"] = df["equity_curve"] - df["peak"]

        flip_dd = df[df["is_flip"] == True]["drawdown"].min()
        primary_dd = df[df["is_flip"] == False]["drawdown"].min()

        print("\n--- DRAWDOWN CONTRIBUTION ---")
        print(f"Primary Max Drawdown: {primary_dd:,.2f}")
        print(f"Flip Max Drawdown: {flip_dd:,.2f}")



# =============================
# RUN
# =============================
if __name__ == "__main__":
    connect(SYMBOL)
    bt = Backtester()
    bt.run()
