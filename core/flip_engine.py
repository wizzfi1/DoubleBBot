# core/flip_engine.py

import MetaTrader5 as mt5
from typing import Optional

from core.entry_engine import EntryEngine
from core.risk_manager import RiskManager
from execution.orders import OrderExecutor
from config.settings import SYMBOL


class FlipEngine:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.flipped_today = False

    # -------------------------------------------------
    def can_flip(self) -> bool:
        return not self.flipped_today

    # -------------------------------------------------
    def handle_flip(
        self,
        stopped_direction: str,
        pdh: float,
        pdl: float
    ) -> Optional[int]:

        if not self.can_flip():
            print("⛔ Flip already used for this event.")
            return None

        flip_direction = "BUY" if stopped_direction == "SELL" else "SELL"
        tp_level = pdh if flip_direction == "BUY" else pdl

        entry_engine = EntryEngine(self.symbol)
        risk = RiskManager(self.symbol)
        executor = OrderExecutor(self.symbol)

        # Build synthetic signal-like object
        class _Signal:
            direction = flip_direction

        plan = entry_engine.build_trade_plan(_Signal(), tp_level)

        if not plan.valid:
            print("⛔ Flip trade invalid:", plan.reason)
            return None

        lot = risk.calculate_lot_size(plan.entry_price, plan.stop_loss)
        if not lot:
            print("⛔ Flip lot sizing failed")
            return None

        ticket = executor.place_limit(
            direction=plan.direction,
            lot=lot,
            entry=plan.entry_price,
            sl=plan.stop_loss,
            tp=tp_level
        )

        if ticket:
            self.flipped_today = True
            print("🔁 Flip trade placed")

        return ticket
