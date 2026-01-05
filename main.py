# main.py

from config.settings import SYMBOL
from core.mt5_connector import connect
from core.session_filter import session_allowed
from core.pdh_pdl import DailyLiquidity
from core.news_blackout import in_news_blackout

from core.pattern_detector import PatternDetector

from core.entry_engine import EntryEngine

from core.risk_manager import RiskManager

from execution.orders import OrderExecutor

from execution.breakeven import BreakEvenManager

from notifications.telegram import send

connect(SYMBOL)

liq = DailyLiquidity(SYMBOL)

pdh, pdl = liq.fetch_pdh_pdl()
print(f"PDH: {pdh}")
print(f"PDL: {pdl}")

session = session_allowed()
print(f"Session: {session}")

print("News blackout:", in_news_blackout())


detector = PatternDetector(SYMBOL, pdh, pdl)
signal = detector.detect()

if signal:
    engine = EntryEngine(SYMBOL)

    # TP example (for SELL, use PDL)
    tp_level = pdl if signal.direction == "SELL" else pdh

    plan = engine.build_trade_plan(signal, tp_level)
    print("Trade Plan:", plan)

if signal and plan.valid:
    risk = RiskManager(SYMBOL)
    lot = risk.calculate_lot_size(plan.entry_price, plan.stop_loss)
    print("Calculated lot size:", lot)   

if signal and plan.valid and lot:
    executor = OrderExecutor(SYMBOL)

    ticket = executor.place_limit(
        direction=plan.direction,
        lot=lot,
        entry=plan.entry_price,
        sl=plan.stop_loss,
        tp=tp_level
    )

    print("Order Ticket:", ticket)     

print("Pattern Signal:", signal)

be = BreakEvenManager(SYMBOL)
be.manage()

send("✅ DoubleB Bot test message – Telegram connected")




