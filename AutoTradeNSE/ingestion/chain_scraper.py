"""
ingestion/chain_scraper.py
Polls NSE option chain for NIFTY and BANKNIFTY every 30 seconds.
Puts ChainEvent dicts onto the shared multiprocessing.Queue.
"""

import multiprocessing as mp
import time
from datetime import datetime
import logging

from logging_config import setup_logging

from ingestion.nse_session import (
    make_session,
    safe_get,
    CHAIN_URL,
    get_expiry_dates,
    build_chain_url,
)

SYMBOLS       = ["NIFTY",]
POLL_INTERVAL = 30   # seconds — NSE refreshes chain ~every 3 min, 30s is safe

logger = logging.getLogger(__name__)


def parse_chain(raw: dict, symbol: str) -> dict:
    """
    Flatten the NSE option chain JSON into a list of strike records.
    Each record: { strike, expiry, ce_oi, ce_iv, ce_ltp, pe_oi, pe_iv, pe_ltp }
    """
    logger.debug("parsing chain for %s...", symbol)
    records = []
    try:
        data = raw.get("records", {}).get("data", [])
        expiry_dates = raw.get("records", {}).get("expiryDates", [])
        underlying = raw.get("records", {}).get("underlyingValue", 0)
        for row in data:
            strike   = row.get("strikePrice", 0)
            expiry   = row.get("expiryDates", "")
            ce       = row.get("CE", {})
            pe       = row.get("PE", {})

            parsed = {
                "strike":     strike,
                "expiry":     expiry,
                "underlying": underlying,
                # Call side
                "ce_oi":      ce.get("openInterest", 0),
                "ce_chg_oi":  ce.get("changeinOpenInterest", 0),
                "ce_iv":      ce.get("impliedVolatility", 0),
                "ce_ltp":     ce.get("lastPrice", 0),
                "ce_volume":  ce.get("totalTradedVolume", 0),
                # Put side
                "pe_oi":      pe.get("openInterest", 0),
                "pe_chg_oi":  pe.get("changeinOpenInterest", 0),
                "pe_iv":      pe.get("impliedVolatility", 0),
                "pe_ltp":     pe.get("lastPrice", 0),
                "pe_volume":  pe.get("totalTradedVolume", 0),
            }

            
            records.append(parsed)
    except Exception:
        logger.exception("parse error for %s", symbol)

    return {
        "event":   "chain",
        "symbol":  symbol,
        "ts":      datetime.utcnow().isoformat(),
        "records": records,
    }


def run_chain_scraper(queue: mp.Queue):
    """Entry point — called as a separate Process."""
    # Ensure logging is configured inside the scraper process
    setup_logging(level=logging.INFO)
    logger.info("started")
    session = make_session()

    while True:
        for symbol in SYMBOLS:
            # Query available expiries and request the chain for the nearest expiry
            expiry_dates = get_expiry_dates(session, symbol)
            expiry = expiry_dates[0] if expiry_dates else None
            if expiry_dates:
                logger.debug("available expiries for %s: %s", symbol, expiry_dates)
                logger.debug("chosen expiry for %s: %s", symbol, expiry)
            else:
                logger.debug("no expiry found for %s; using base URL", symbol)

            url = build_chain_url(symbol, expiry)
            logger.info("requesting chain URL: %s", url)
            raw = safe_get(session, url)
            if raw:
                event = parse_chain(raw, symbol)
                logger.info("%s: parsed %d strikes", symbol, len(event["records"]))
                try:
                    queue.put_nowait(event)
                except Exception:
                    logger.debug("queue full, skipping this tick")
                logger.debug("%s: %d strikes queued", symbol, len(event["records"]))
            time.sleep(2)   # small gap between the two symbol fetches

        time.sleep(POLL_INTERVAL)
