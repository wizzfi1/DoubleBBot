# execution/breakeven.py

import MetaTrader5 as mt5
from typing import Optional

from config.settings import BE_RR


class BreakEvenManager:
    def __init__(self, symbol: str):
        self.symbol = symbol

    # -------------------------------------------------
    def manage(self):
        positions = mt5.positions_get(symbol=self.symbol)
        if positions is None:
            return

        for pos in positions:
            entry = pos.price_open
            sl = pos.sl
            tp = pos.tp
            current = pos.price_current

            # Calculate R
            risk = abs(entry - sl)
            reward = abs(current - entry)

            if risk <= 0:
                continue

            rr = reward / risk

            # Move SL to BE
            if rr >= BE_RR:
                if (
                    (pos.type == mt5.POSITION_TYPE_BUY and sl < entry) or
                    (pos.type == mt5.POSITION_TYPE_SELL and sl > entry)
                ):
                    self._move_sl_to_be(pos, entry)

    # -------------------------------------------------
    def _move_sl_to_be(self, pos, entry):
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": pos.ticket,
            "sl": entry,
            "tp": pos.tp,
        }

        result = mt5.order_send(request)

        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"🔒 SL moved to BE | Ticket {pos.ticket}")
