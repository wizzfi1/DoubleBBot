# core/double_break_detector.py

import pandas as pd
from core.structure import is_swing_high, is_swing_low


class DoubleBreakDetector:
    """
    Detects TWO STRUCTURAL breaks after a liquidity sweep.

    BUY:
        - break & close above TWO confirmed swing highs

    SELL:
        - break & close below TWO confirmed swing lows
    """

    def __init__(self, liquidity_level: float, direction: str, max_candles: int = 25):
        self.liquidity_level = liquidity_level
        self.direction = direction  # "BUY" or "SELL"
        self.max_candles = max_candles

        self.breaks: list[float] = []
        self.completed = False

        self._candles_seen = 0
        self._last_swing = None

    # --------------------------------------------------
    def update(self, df: pd.DataFrame, i: int):
        """
        Returns entry index ONLY on second valid structural break.
        Otherwise returns None.
        """

        if self.completed:
            return None

        self._candles_seen += 1

        # -------------------------------
        # EXPIRY
        # -------------------------------
        if self._candles_seen > self.max_candles:
            self.completed = True
            return None

        if i < 2:
            return None

        prev = df.iloc[i - 1]
        curr = df.iloc[i]

        # ===============================
        # SELL → break swing LOWS
        # ===============================
        if self.direction == "SELL":
            if is_swing_low(df, i - 1):
                self._last_swing = prev["low"]

            if self._last_swing is None:
                return None

            # BREAK ONLY IF CLOSE BELOW SWING
            if curr["close"] < self._last_swing:
                self._register_break(self._last_swing)
                self._last_swing = None  # force new swing

        # ===============================
        # BUY → break swing HIGHS
        # ===============================
        else:
            if is_swing_high(df, i - 1):
                self._last_swing = prev["high"]

            if self._last_swing is None:
                return None

            # BREAK ONLY IF CLOSE ABOVE SWING
            if curr["close"] > self._last_swing:
                self._register_break(self._last_swing)
                self._last_swing = None  # force new swing

        # -------------------------------
        # ENTRY TRIGGER
        # -------------------------------
        if len(self.breaks) == 2:
            self.completed = True
            return i

        return None

    # --------------------------------------------------
    def _register_break(self, swing_level: float):
        """
        Registers ONLY swing levels — not raw price ticks.
        """
        if not self.breaks:
            self.breaks.append(float(swing_level))
            return

        if self.direction == "SELL" and swing_level < self.breaks[-1]:
            self.breaks.append(float(swing_level))

        elif self.direction == "BUY" and swing_level > self.breaks[-1]:
            self.breaks.append(float(swing_level))
