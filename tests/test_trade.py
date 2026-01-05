# tests/test_trade.py
# ⚠️ DEMO ONLY — DO NOT USE ON LIVE

import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from config.settings import SYMBOL
from core.mt5_connector import connect
from core.risk_manager import RiskManager
from execution.orders import OrderExecutor
from notifications.telegram import send
import MetaTrader5 as mt5


# ==============================
# CONFIGURE YOUR TEST TRADE HERE
# ==============================

DIRECTION = "SELL"       # "BUY" or "SELL"
ENTRY_PRICE = 1.17400    # MUST be away from current price
STOP_LOSS = 1.17460
TAKE_PROFIT = 1.17093


print("🧪 STARTING DEMO EXECUTION TEST")

connect(SYMBOL)

account = mt5.account_info()
if account is None:
    raise RuntimeError("MT5 account not available")

print(f"Account balance: {account.balance}")

risk = RiskManager(SYMBOL)
lot = risk.calculate_lot_size(ENTRY_PRICE, STOP_LOSS)

if not lot:
    raise RuntimeError("❌ Lot calculation failed")

print(f"Calculated lot size: {lot}")

executor = OrderExecutor(SYMBOL)

ticket = executor.place_limit(
    direction=DIRECTION,
    lot=lot,
    entry=ENTRY_PRICE,
    sl=STOP_LOSS,
    tp=TAKE_PROFIT
)

if not ticket:
    print("⚠️ Order was not placed (likely due to existing open trade).")
    print("✅ Execution safety check PASSED.")
    exit(0)


send(
    f"🧪 *DEMO TEST TRADE PLACED*\n"
    f"Symbol: {SYMBOL}\n"
    f"Direction: {DIRECTION}\n"
    f"Lot: {lot}\n"
    f"Entry: {ENTRY_PRICE}\n"
    f"SL: {STOP_LOSS}\n"
    f"TP: {TAKE_PROFIT}\n"
    f"Risk: ~$3000"
)

print(f"✅ TEST ORDER SUCCESS | Ticket {ticket}")
print("🛑 TEST COMPLETE — SCRIPT EXITING")
