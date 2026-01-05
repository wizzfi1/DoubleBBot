# core/pdh_pdl.py

import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta


class DailyLiquidity:
    def __init__(self, symbol):
        self.symbol = symbol

    # ---------------------------------------------
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
            start,
            end
        )

        if rates is None or len(rates) == 0:
            return None, None

        df = pd.DataFrame(rates)
        return df["high"].max(), df["low"].min()

    # ---------------------------------------------
    def fetch_pdh_pdl_for_date(self, day):
        """
        BACKTEST MODE: previous day relative to supplied date
        """
        prev_day = day - timedelta(days=1)

        start = datetime.combine(prev_day, datetime.min.time())
        end = datetime.combine(prev_day, datetime.max.time())

        rates = mt5.copy_rates_range(
            self.symbol,
            mt5.TIMEFRAME_H1,
            start,
            end
        )

        if rates is None or len(rates) == 0:
            return None, None

        df = pd.DataFrame(rates)
        return df["high"].max(), df["low"].min()
