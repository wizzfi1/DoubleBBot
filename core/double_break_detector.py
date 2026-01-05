# core/double_break_detector.py

from core.structure import is_swing_high, is_swing_low


class DoubleBreakDetector:
    def __init__(self, level, direction):
        """
        direction: 'SELL' (PDH logic) or 'BUY' (PDL logic)
        level: PDH or PDL
        """
        self.level = level
        self.direction = direction

        self.swings = []   # swing highs or lows
        self.breaks = []
        self.completed = False

    # -----------------------------------------
    def update(self, df, i):
        # -------------------------------
        # 1. Detect swings
        # -------------------------------
        if self.direction == "SELL":
            if is_swing_high(df, i - 1):
                self.swings.append(df.iloc[i - 1]["high"])
        else:
            if is_swing_low(df, i - 1):
                self.swings.append(df.iloc[i - 1]["low"])

        if len(self.swings) > 5:
            self.swings.pop(0)

        # -------------------------------
        # 2. Detect breaks
        # -------------------------------
        if self.swings:
            last = self.swings[-1]

            if (
                self.direction == "SELL" and
                df.iloc[i]["close"] > last
            ):
                self._add_break(last)

            if (
                self.direction == "BUY" and
                df.iloc[i]["close"] < last
            ):
                self._add_break(last)

        # -------------------------------
        # 3. Completion
        # -------------------------------
        if len(self.breaks) == 2:
            if self.direction == "SELL":
                level = min(self.breaks)
                if df.iloc[i]["close"] < level:
                    self.completed = True
                    return i + 1

            else:
                level = max(self.breaks)
                if df.iloc[i]["close"] > level:
                    self.completed = True
                    return i + 1

        return None

    # -----------------------------------------
    def _add_break(self, level):
        if not self.breaks or self.breaks[-1] != level:
            self.breaks.append(level)
            if len(self.breaks) > 2:
                self.breaks.pop(0)
