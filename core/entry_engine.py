# core/entry_engine.py

from dataclasses import dataclass
import pandas as pd


@dataclass
class TradePlan:
    direction: str
    entry_price: float
    stop_loss: float
    rr: float
    valid: bool
    reason: str = ""


class EntryEngine:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.df: pd.DataFrame | None = None

    # -------------------------------------------------
    def build_trade_plan(self, signal, tp: float) -> TradePlan:
        if self.df is None or len(self.df) < 3:
            return TradePlan(
                signal.direction, 0, 0, 0, False,
                "Not enough candles"
            )

        direction = signal.direction
        df = self.df.reset_index(drop=True)

        # --------------------------------------------
        # FIND OPPOSITE CANDLE (PULLBACK)
        # --------------------------------------------
        pullback_index = None

        if direction == "BUY":
            # bearish candle = close < open
            for i in range(len(df) - 2, -1, -1):
                if df.loc[i, "close"] < df.loc[i, "open"]:
                    pullback_index = i
                    break

        else:  # SELL
            # bullish candle = close > open
            for i in range(len(df) - 2, -1, -1):
                if df.loc[i, "close"] > df.loc[i, "open"]:
                    pullback_index = i
                    break

        if pullback_index is None:
            return TradePlan(
                direction, 0, 0, 0, False,
                "No opposite candle found"
            )

        # --------------------------------------------
        # ENTRY & STOP LOGIC
        # --------------------------------------------
        last = df.iloc[-1]

        if direction == "BUY":
            entry = last["high"]
            sl = df.loc[pullback_index, "low"]
        else:
            entry = last["low"]
            sl = df.loc[pullback_index, "high"]

        if entry == sl:
            return TradePlan(
                direction, 0, 0, 0, False,
                "Invalid price levels"
            )

        rr = abs(tp - entry) / abs(entry - sl)

        return TradePlan(
            direction=direction,
            entry_price=entry,
            stop_loss=sl,
            rr=rr,
            valid=True,
        )
