# core/entry_engine.py

import MetaTrader5 as mt5
import pandas as pd
from dataclasses import dataclass
from typing import Optional

from config.settings import SYMBOL, LTF, MIN_RR


@dataclass
class TradePlan:
    direction: str
    entry_price: float
    stop_loss: float
    rr: float
    valid: bool
    reason: str


class EntryEngine:
    def __init__(self, symbol: str):
        self.symbol = symbol

    # ---------------------------------------------
    def fetch_m5(self, bars=50):
        rates = mt5.copy_rates_from_pos(
            self.symbol,
            LTF,
            0,
            bars
        )
        df = pd.DataFrame(rates)
        return df

    # ---------------------------------------------
    def find_last_opposite_candle(self, df, direction: str):
        """
        SELL → last bullish candle
        BUY  → last bearish candle
        """
        for i in reversed(range(len(df) - 1)):
            candle = df.iloc[i]
            if direction == "SELL" and candle["close"] > candle["open"]:
                return candle
            if direction == "BUY" and candle["close"] < candle["open"]:
                return candle
        return None

    # ---------------------------------------------
    def calculate_rr(self, entry, sl, tp):
        risk = abs(entry - sl)
        reward = abs(tp - entry)
        if risk == 0:
            return 0
        return reward / risk

    # ---------------------------------------------
    def build_trade_plan(self, signal, tp_level: float) -> TradePlan:
        df = self.fetch_m5()

        candle = self.find_last_opposite_candle(df, signal.direction)
        if candle is None:
            return TradePlan(
                signal.direction, 0, 0, 0, False,
                "No opposite candle found"
            )

        entry = candle["open"]

        if signal.direction == "SELL":
            sl = candle["high"]
        else:
            sl = candle["low"]

        rr = self.calculate_rr(entry, sl, tp_level)

        if rr < MIN_RR:
            return TradePlan(
                signal.direction, entry, sl, rr, False,
                f"RR too low ({rr:.2f})"
            )

        return TradePlan(
            signal.direction, entry, sl, rr, True,
            "Valid trade plan"
        )
