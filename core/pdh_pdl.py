# core/pdh_pdl.py

import MetaTrader5 as mt5
from datetime import datetime, timedelta
import pandas as pd

class DailyLiquidity:
    def __init__(self, symbol):
        self.symbol = symbol
        self.used_levels = set()  # one-time event enforcement

    def _get_previous_day(self):
        today = datetime.utcnow().date()
        prev_day = today - timedelta(days=1)
        return prev_day

    def fetch_pdh_pdl(self):
        prev_day = self._get_previous_day()

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
