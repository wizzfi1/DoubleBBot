# tests/test_double_break_detector.py

import pandas as pd
from core.double_break_detector import DoubleBreakDetector


def make_m5_df(rows):
    return pd.DataFrame(
        rows,
        columns=["open", "high", "low", "close"]
    )


def test_no_breaks():
    df = make_m5_df([
        (1.10, 1.11, 1.09, 1.10),
        (1.10, 1.11, 1.09, 1.10),
        (1.10, 1.11, 1.09, 1.10),
    ])

    detector = DoubleBreakDetector(1.12, "SELL")

    for i in range(2, len(df)):
        assert detector.update(df, i) is None

    assert detector.breaks == []
    assert detector.completed is False


def test_single_break_not_enough():
    df = make_m5_df([
        (1.10, 1.11, 1.09, 1.10),
        (1.10, 1.11, 1.08, 1.09),
        (1.09, 1.10, 1.07, 1.08),
    ])

    detector = DoubleBreakDetector(1.12, "SELL")

    for i in range(2, len(df)):
        detector.update(df, i)

    assert len(detector.breaks) == 1
    assert detector.completed is False


def test_double_break_triggers_entry():
    df = make_m5_df([
        (1.10, 1.11, 1.09, 1.10),
        (1.10, 1.11, 1.08, 1.09),
        (1.09, 1.10, 1.07, 1.08),
        (1.08, 1.09, 1.08, 1.085),
        (1.085, 1.09, 1.06, 1.07),
    ])

    detector = DoubleBreakDetector(1.12, "SELL")

    entry_index = None
    for i in range(2, len(df)):
        res = detector.update(df, i)
        if res is not None:
            entry_index = res

    assert detector.completed is True
    assert entry_index == 4
    assert len(detector.breaks) == 2


def test_detector_expiry():
    df = make_m5_df([
        (1.10, 1.11, 1.09, 1.10)
    ] * 30)

    detector = DoubleBreakDetector(
        1.12,
        "SELL",
        max_candles=5
    )

    for i in range(2, len(df)):
        detector.update(df, i)

    assert detector.completed is True
    assert len(detector.breaks) == 0
