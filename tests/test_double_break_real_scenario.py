import pandas as pd
from core.double_break_detector import DoubleBreakDetector


def make_df(rows):
    return pd.DataFrame(
        rows,
        columns=["open", "high", "low", "close"]
    )


def test_buy_double_break_after_structure_invalidation():
    """
    Exact reproduction of your chart:

    - PDL sweep → BUY
    - Initial attempt fails (structure invalidation)
    - New base forms
    - Swing high CONFIRMED
    - Break ①
    - Pullback
    - New swing high CONFIRMED
    - Break ② → ENTRY
    """

    df = make_df([
        # ---- initial move after PDL sweep ----
        (1.1660, 1.1670, 1.1655, 1.1668),
        (1.1668, 1.1672, 1.1662, 1.1664),

        # ---- structure invalidation (lower low) ----
        (1.1664, 1.1666, 1.1650, 1.1652),

        # ---- new base ----
        (1.1652, 1.1660, 1.1651, 1.1658),

        # ---- swing high candidate ----
        (1.1658, 1.1666, 1.1656, 1.1663),

        # ---- pullback CONFIRMS swing high ----
        (1.1663, 1.1664, 1.1659, 1.1660),

        # ---- first valid break (①) ----
        (1.1660, 1.1672, 1.1659, 1.1670),

        # ---- pullback ----
        (1.1670, 1.1671, 1.1663, 1.1665),

        # ---- second swing high candidate ----
        (1.1665, 1.1674, 1.1664, 1.1672),

        # ---- pullback CONFIRMS swing ----
        (1.1672, 1.1673, 1.1667, 1.1669),

        # ---- second valid break (②) ----
        (1.1669, 1.1685, 1.1668, 1.1680),
    ])

    detector = DoubleBreakDetector(
        liquidity_level=1.1675,
        direction="BUY",
        max_candles=30,
    )

    entry_index = None

    for i in range(len(df)):
        res = detector.update(df, i)
        if res is not None:
            entry_index = res

    # -----------------------------
    # ASSERTIONS
    # -----------------------------
    assert len(detector.breaks) == 2
    assert detector.completed is True
    assert entry_index == len(df) - 1
    assert detector.breaks[0] < detector.breaks[1]
