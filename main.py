# main.py

from config.settings import SYMBOL
from core.mt5_connector import connect
from core.session_filter import session_allowed
from core.pdh_pdl import DailyLiquidity
from core.news_blackout import in_news_blackout

connect(SYMBOL)

liq = DailyLiquidity(SYMBOL)

pdh, pdl = liq.fetch_pdh_pdl()
print(f"PDH: {pdh}")
print(f"PDL: {pdl}")

session = session_allowed()
print(f"Session: {session}")

print("News blackout:", in_news_blackout())
