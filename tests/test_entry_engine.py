# tests/test_entry_engine.py

import pandas as pd
from core.entry_engine import EntryEngine


class DummySignal:
    def __init__(self, direction):
        self.direction = direction


def make_df(rows):
    return pd.DataFrame(
        rows, columns=["open", "high", "low", "close"]
    )


def test_buy_entry_valid_with_pullback():
    engine = EntryEngine("EURUSD")

    # BUY logic:
    # 1) bullish move
    # 2) bearish pullback (required)
    df = make_df([
        (1.10, 1.11, 1.09, 1.11),   # bullish
        (1.11, 1.12, 1.105, 1.106), # bearish pullback
        (1.106, 1.115, 1.105, 1.114),
    ])

    engine.df = df

    signal = DummySignal("BUY")
    tp = 1.13

    plan = engine.build_trade_plan(signal, tp)

    assert plan.valid is True
    assert plan.entry_price > plan.stop_loss
    assert plan.entry_price < tp


def test_sell_entry_valid_with_pullback():
    engine = EntryEngine("EURUSD")

    # SELL logic:
    # 1) bearish move
    # 2) bullish pullback (required)
    df = make_df([
        (1.20, 1.21, 1.19, 1.19),   # bearish
        (1.19, 1.205, 1.185, 1.20), # bullish pullback
        (1.20, 1.195, 1.18, 1.185),
    ])

    engine.df = df

    signal = DummySignal("SELL")
    tp = 1.17

    plan = engine.build_trade_plan(signal, tp)

    assert plan.valid is True
    assert plan.entry_price < plan.stop_loss
    assert plan.entry_price > tp
