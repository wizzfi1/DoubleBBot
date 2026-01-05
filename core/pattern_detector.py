# core/pattern_detector.py

import MetaTrader5 as mt5
import pandas as pd
from dataclasses import dataclass
from datetime import datetime

from config.settings import SYMBOL, LTF


@dataclass
class PatternSignal:
    pattern_type: str           # "PATTERN_1" or "PATTERN_2"
    direction: str              # "SELL" or "BUY"
    inducements: list           # list of price levels
    timestamp: datetime


class PatternDetector:
    def __init__(self, symbol: str, pdh: float, pdl: float):
        self.symbol = symbol
        self.pdh = pdh
        self.pdl = pdl

    # -------------------------------------------------
    def fetch_m5(self, bars=200):
        rates = mt5.copy_rates_from_pos(
            self.symbol,
            LTF,
            0,
            bars
        )
        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s")
        return df

    # -------------------------------------------------
    def detect_swing_highs(self, df):
        swings = []
        for i in range(2, len(df) - 2):
            high = df.loc[i, "high"]
            if (
                high > df.loc[i - 1, "high"] and
                high > df.loc[i - 2, "high"] and
                high > df.loc[i + 1, "high"] and
                high > df.loc[i + 2, "high"]
            ):
                swings.append((i, high))
        return swings

    # -------------------------------------------------
    def detect_inducements(self, df, direction="SELL"):
        inducements = []

        swings = self.detect_swing_highs(df)

        for idx, level in swings:
            candle = df.loc[idx]
            if direction == "SELL":
                if candle["close"] > candle["open"]:  # bullish
                    inducements.append((idx, level))
            else:
                if candle["close"] < candle["open"]:  # bearish
                    inducements.append((idx, level))

        return inducements

    # -------------------------------------------------
    def pattern_1_sell(self, df):
        inducements = self.detect_inducements(df, "SELL")

        post_pdh = [(i, lvl) for i, lvl in inducements if lvl > self.pdh]

        if len(post_pdh) < 2:
            return None

        first, second = post_pdh[-2], post_pdh[-1]

        last_close = df.iloc[-1]["close"]

        if last_close < first[1] and last_close < second[1]:
            return PatternSignal(
                pattern_type="PATTERN_1",
                direction="SELL",
                inducements=[first[1], second[1]],
                timestamp=df.iloc[-1]["time"]
            )

        return None

    # -------------------------------------------------
    def pattern_2_sell(self, df):
        inducements = self.detect_inducements(df, "SELL")

        post_pdh = [(i, lvl) for i, lvl in inducements if lvl > self.pdh]
        pre_pdh = [(i, lvl) for i, lvl in inducements if lvl < self.pdh]

        if not post_pdh or not pre_pdh:
            return None

        last_close = df.iloc[-1]["close"]

        swept = [
            lvl for _, lvl in post_pdh + pre_pdh
            if last_close < lvl
        ]

        if len(swept) >= 2:
            return PatternSignal(
                pattern_type="PATTERN_2",
                direction="SELL",
                inducements=swept,
                timestamp=df.iloc[-1]["time"]
            )

        return None

    # -------------------------------------------------
    def detect(self):
        df = self.fetch_m5()

        # SELL side (PDH logic)
        if df.iloc[-1]["close"] > self.pdh:
            p1 = self.pattern_1_sell(df)
            if p1:
                return p1

            p2 = self.pattern_2_sell(df)
            if p2:
                return p2

        return None
