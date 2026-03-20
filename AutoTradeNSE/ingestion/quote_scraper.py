"""
ingestion/quote_scraper.py
Polls NSE for Nifty and BankNifty underlying LTP every 5 seconds.
"""

import multiprocessing as mp
import time
from datetime import datetime

from ingestion.nse_session import make_session, safe_get, VIX_URL

SYMBOLS       = ["NIFTY", 
                 #"BANKNIFTY"
                 ]
POLL_INTERVAL = 10


def run_quote_scraper(queue: mp.Queue):
    print("[quote_scraper] started")
    session = make_session()

    while True:
        raw = safe_get(session, VIX_URL)   # allIndices carries Nifty/BankNifty too
        if raw:
            indices = raw.get("data", [])
            for entry in indices:
                name = entry.get("index", "")
                if "NIFTY BANK" in name:
                    sym = "BANKNIFTY"
                elif name == "NIFTY 50":
                    sym = "NIFTY"
                else:
                    continue

                event = {
                    "event":  "quote",
                    "symbol": sym,
                    "ts":     datetime.utcnow().isoformat(),
                    "ltp":    entry.get("last", 0),
                    "open":   entry.get("open", 0),
                    "high":   entry.get("high", 0),
                    "low":    entry.get("low", 0),
                    "pct":    entry.get("percentChange", 0),
                }
                try:
                    queue.put_nowait(event)
                except Exception:
                    print("[quote_scraper] queue is full — dropping event")
                    pass

            print(f"[quote_scraper] quotes pushed")

        time.sleep(POLL_INTERVAL)
