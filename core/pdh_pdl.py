# core/pdh_pdl.py

import MetaTrader5 as mt5

from datetime import datetime, timedelta
import pandas as pd

class DailyLiquidity:
    def __init__(self, symbol):
        self.symbol = symbol

    def fetch_pdh_pdl(self):
        """
        LIVE MODE: previous day relative to today
        """
        today = datetime.utcnow().date()
        prev_day = today - timedelta(days=1)

        start = datetime.combine(prev_day, datetime.min.time())
        end = datetime.combine(prev_day, datetime.max.time())

        rates = mt5.copy_rates_range(
            self.symbol,
            mt5.TIMEFRAME_H1,
            datetime.combine(prev_day, datetime.min.time()),
            datetime.combine(prev_day, datetime.max.time())
        )

        df = pd.DataFrame(rates)
        pdh = df["high"].max()
        pdl = df["low"].min()

        return pdh, pdl

    def is_taken_by_close(self, level, direction="UP"):
        rates = mt5.copy_rates_from_pos(
            self.symbol,
            mt5.TIMEFRAME_M5,
            0,
            3
        )

        last_close = rates[-1]["close"]

        if direction == "UP":
            return last_close > level
        else:
            return last_close < level

    def mark_used(self, level):
        self.used_levels.add(round(level, 5))

    def is_unused(self, level):
        return round(level, 5) not in self.used_levels
