# core/risk_manager.py

import MetaTrader5 as mt5
import math
from typing import Optional

from config.settings import RISK_PER_TRADE


class RiskManager:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.info = mt5.symbol_info(symbol)

        if self.info is None:
            raise RuntimeError(f"Failed to get symbol info for {symbol}")

    # -------------------------------------------------
    def calculate_lot_size(self, entry_price: float, stop_loss: float) -> Optional[float]:
        """
        Calculates lot size based on fixed USD risk.
        Returns None if calculation is invalid.
        """

        price_distance = abs(entry_price - stop_loss)
        if price_distance <= 0:
            return None

        # Tick properties
        tick_size = self.info.trade_tick_size
        tick_value = self.info.trade_tick_value

        if tick_size <= 0 or tick_value <= 0:
            return None

        # Value per lot per price unit
        value_per_price = tick_value / tick_size

        # Raw lot size
        lot = RISK_PER_TRADE / (price_distance * value_per_price)

        # Broker constraints
        min_lot = self.info.volume_min
        max_lot = self.info.volume_max
        step = self.info.volume_step

        # Clamp
        lot = max(min_lot, min(lot, max_lot))

        # Normalize to step
        lot = math.floor(lot / step) * step

        if lot < min_lot:
            return None

        return round(lot, 2)
