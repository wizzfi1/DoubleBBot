import types
import MetaTrader5 as mt5
import pytest

from execution.orders import OrderExecutor


# ============================
# FIXTURES
# ============================

@pytest.fixture
def executor():
    return OrderExecutor("EURUSD")


@pytest.fixture
def mock_mt5(monkeypatch):
    """
    Fully mock MetaTrader5 API used by OrderExecutor
    """

    # --- mock positions_get ---
    def mock_positions_get(symbol=None):
        return []

    # --- mock order_send ---
    def mock_order_send(request):
        return types.SimpleNamespace(
            retcode=mt5.TRADE_RETCODE_DONE,
            order=123456
        )

    monkeypatch.setattr(mt5, "positions_get", mock_positions_get)
    monkeypatch.setattr(mt5, "order_send", mock_order_send)


# ============================
# TESTS
# ============================

def test_place_buy_limit_order(executor, mock_mt5):
    ticket = executor.place_limit(
        direction="BUY",
        lot=0.1,
        entry=1.1000,
        sl=1.0950,
        tp=1.1200,
        is_flip=False
    )

    assert ticket == 123456


def test_place_sell_limit_order(executor, mock_mt5):
    ticket = executor.place_limit(
        direction="SELL",
        lot=0.2,
        entry=1.2000,
        sl=1.2050,
        tp=1.1800,
        is_flip=False
    )

    assert ticket == 123456


def test_flip_trade_uses_flip_magic(monkeypatch):
    executor = OrderExecutor("EURUSD")

    captured_request = {}

    def mock_positions_get(symbol=None):
        return []

    def mock_order_send(request):
        captured_request.update(request)
        return types.SimpleNamespace(
            retcode=mt5.TRADE_RETCODE_DONE,
            order=999
        )

    monkeypatch.setattr(mt5, "positions_get", mock_positions_get)
    monkeypatch.setattr(mt5, "order_send", mock_order_send)

    ticket = executor.place_limit(
        direction="BUY",
        lot=0.1,
        entry=1.1000,
        sl=1.0950,
        tp=1.1200,
        is_flip=True
    )

    assert ticket == 999
    assert captured_request["magic"] != 0


def test_block_when_max_open_trades(monkeypatch):
    executor = OrderExecutor("EURUSD")

    def mock_positions_get(symbol=None):
        return [1, 2, 3]  # simulate open trades

    monkeypatch.setattr(mt5, "positions_get", mock_positions_get)

    ticket = executor.place_limit(
        direction="BUY",
        lot=0.1,
        entry=1.1000,
        sl=1.0950,
        tp=1.1200
    )

    assert ticket is None
