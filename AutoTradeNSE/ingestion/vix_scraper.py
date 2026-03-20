"""
ingestion/vix_scraper.py
Polls NSE's allIndices endpoint every 10 seconds to extract India VIX.
"""

import multiprocessing as mp
import time
from datetime import datetime

from ingestion.nse_session import make_session, safe_get, VIX_URL

POLL_INTERVAL = 10


def run_vix_scraper(queue: mp.Queue):
    print("[vix_scraper] started")
    session = make_session()

    while True:
        raw = safe_get(session, VIX_URL)
        if raw:
            indices = raw.get("data", [])
            vix_entry = next((x for x in indices if x.get("index") == "INDIA VIX"), None)
            if vix_entry:
                event = {
                    "event": "vix",
                    "ts":    datetime.utcnow().isoformat(),
                    "vix":   vix_entry.get("last", 0),
                    "chg":   vix_entry.get("variation", 0),
                    "pct":   vix_entry.get("percentChange", 0),
                }
                try:
                    queue.put_nowait(event)
                except Exception:
                    pass
                print(f"[vix_scraper] VIX={event['vix']:.2f}")

        time.sleep(POLL_INTERVAL)
