import MetaTrader5 as mt5

class TradeWatcher:
    def __init__(self, magic):
        self.magic = magic
        self.checked_tickets = set()

    def check_sl_hit(self):
        deals = mt5.history_deals_get(0, mt5.time_current())
        if deals is None:
            return None

        for d in deals:
            if d.magic != self.magic:
                continue
            if d.ticket in self.checked_tickets:
                continue

            self.checked_tickets.add(d.ticket)

            # SL hit = negative profit & reason DEAL_REASON_SL
            if d.profit < 0 and d.reason == mt5.DEAL_REASON_SL:
                return d

        return None
