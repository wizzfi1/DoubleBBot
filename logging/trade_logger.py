# logging/trade_logger.py

from datetime import datetime
import json
import os


class TradeLogger:
    def __init__(self, filename="trade_log.json"):
        self.filename = filename
        if not os.path.exists(filename):
            with open(filename, "w") as f:
                json.dump([], f)

    # -------------------------------------------------
    def log(self, event: str, data: dict):
        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
            "data": data
        }

        with open(self.filename, "r+") as f:
            logs = json.load(f)
            logs.append(record)
            f.seek(0)
            json.dump(logs, f, indent=2)

        print(f"🧾 LOGGED: {event}")
