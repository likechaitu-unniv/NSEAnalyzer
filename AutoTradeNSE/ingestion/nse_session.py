"""
ingestion/nse_session.py
NSE requires a browser-like session with a valid cookie before accepting API calls.
This module handles session creation and automatic cookie refresh.
"""

import requests
import time
import logging
import json
import re
from datetime import datetime
from typing import Optional, List
from urllib.parse import quote

logger = logging.getLogger(__name__)

NSE_BASE   = "https://www.nseindia.com"
NSE_HOME   = f"{NSE_BASE}/"
OPTION_CHAIN_PAGE = f"{NSE_BASE}/option-chain"
# Use the v3 option-chain endpoint and include the type=Indices parameter
CHAIN_URL  = f"{NSE_BASE}/api/option-chain-v3?type=Indices&symbol={{symbol}}"
VIX_URL    = f"{NSE_BASE}/api/allIndices"
QUOTE_URL  = f"{NSE_BASE}/api/quote-derivative?symbol={{symbol}}"

# When querying expiry metadata, use a far-future expiry so the API
# returns the full expiry list. This sentinel expiry is only used to
# retrieve metadata and does not need to be a real traded expiry.
META_EXPIRY_FOR_METADATA = "31-Mar-2030"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/",
}


def make_session() -> requests.Session:
    """Create a session with a valid NSE cookie."""
    session = requests.Session()
    session.headers.update(HEADERS)
    # Hit the home page to get cookies
    try:
        logger.debug("Initializing NSE session: GET %s", NSE_HOME)
        resp = session.get(NSE_HOME, timeout=10)
        try:
            size = len(resp.content) if resp.content is not None else 0
        except Exception:
            size = 0
        logger.debug("Init response: status=%s bytes=%d", getattr(resp, "status_code", None), size)
        time.sleep(1)

        # Also request the option-chain page to obtain any JS-set cookies and
        # ensure the server will return full option-chain JSON (some NSE APIs
        # require the option-chain referer/context).
        try:
            logger.debug("Fetching option-chain page: GET %s", OPTION_CHAIN_PAGE)
            resp2 = session.get(OPTION_CHAIN_PAGE, timeout=10)
            size2 = len(resp2.content) if resp2.content is not None else 0
            logger.debug("Option-chain response: status=%s bytes=%d", getattr(resp2, "status_code", None), size2)
            time.sleep(1)
        except Exception as e:
            logger.debug("option-chain page request failed: %s", e)
    except Exception as e:
        logger.warning("cookie init failed: %s", e)
    return session


def safe_get(session: requests.Session, url: str, retries: int = 3) -> Optional[dict]:
    """GET with auto-retry and session refresh on 401/403."""
    for attempt in range(retries):
        try:
            logger.debug("GET %s (attempt %d/%d)", url, attempt + 1, retries)
            resp = session.get(url, timeout=10)
            try:
                size = len(resp.content) if resp.content is not None else 0
            except Exception:
                size = 0
            logger.debug("Response for %s: status=%s bytes=%d", url, getattr(resp, "status_code", None), size)

            if resp.status_code in (401, 403):
                logger.info("session expired (status=%s), refreshing cookie", resp.status_code)
                logger.debug("Refreshing cookie via GET %s", NSE_HOME)
                session.get(NSE_HOME, timeout=10)
                time.sleep(2)
                continue
            resp.raise_for_status()
            try:
                return resp.json()
            except Exception as e:
                logger.warning("JSON decode failed for %s: %s", url, e)
                return None
        except Exception as e:
            logger.warning("attempt %d failed for %s: %s", attempt + 1, url, e)
            time.sleep(2 * (attempt + 1))
    return None


def build_chain_url(symbol: str, expiry: Optional[str] = None) -> str:
    """Return the option-chain API URL for `symbol` and optional `expiry`.
    Example:
        /api/option-chain-v3?type=Indices&symbol=NIFTY&expiry=24-MAR-2026
    """
    base = CHAIN_URL.format(symbol=symbol)
    if expiry:
        safe_expiry = quote(expiry, safe="")
        return f"{base}&expiry={safe_expiry}"
    return base


def get_expiry_dates(session: requests.Session, symbol: str) -> List[str]:
    """Fetch the chain metadata and return the available expiry dates.

    Returns an empty list on error.
    """
    # Prepare base and metadata URLs. Initialize `base_url` early so any
    # later references to a fallback URL won't raise UnboundLocalError.
    base_url = CHAIN_URL.format(symbol=symbol)
    # Query the v3 endpoint with a sentinel expiry to encourage the API
    # to return the full set of expiry dates (some NSE responses vary
    # depending on the requested expiry).
    meta_url = build_chain_url(symbol, META_EXPIRY_FOR_METADATA)
    logger.debug("get_expiry_dates: querying metadata URL %s", meta_url)
    raw = safe_get(session, meta_url)
    if not raw:
        logger.debug("metadata URL did not return data for %s, falling back to base URL %s", symbol, base_url)
        raw = safe_get(session, base_url)
    if not raw:
        logger.debug("get_expiry_dates: no response for %s", symbol)
        return []

    try:
        # Common v2/v3 location
        if isinstance(raw, dict):
            records = raw.get("records") if isinstance(raw.get("records"), dict) else None
            if records:
                ed = records.get("expiryDates")
                if ed:
                    logger.debug("expiryDates (records) for %s: %s", symbol, ed)
                    return ed

            # top-level expiryDates
            ed_top = raw.get("expiryDates")
            if ed_top:
                logger.debug("expiryDates (top) for %s: %s", symbol, ed_top)
                return ed_top

            # try extracting from data rows
            data = None
            if records and isinstance(records.get("data"), list):
                data = records.get("data")
            elif isinstance(raw.get("data"), list):
                data = raw.get("data")

            if data:
                exps = []
                for row in data:
                    if isinstance(row, dict):
                        exp = row.get("expiryDate") or row.get("expiry")
                        if exp and isinstance(exp, str):
                            if exp not in exps:
                                exps.append(exp)
                if exps:
                    logger.debug("expiryDates (from data) for %s: %s", symbol, exps)
                    return exps

        # Fallback: regex search in serialized JSON
        raw_str = json.dumps(raw)
        matches = re.findall(r"\d{1,2}-[A-Za-z]{3}-\d{4}", raw_str)
        if matches:
            # preserve order + dedupe
            seen = []
            for m in matches:
                if m not in seen:
                    seen.append(m)

            # try to sort expiries chronologically when possible
            def _parse(d: str):
                for fmt in ("%d-%b-%Y", "%d-%b-%y"):
                    try:
                        return datetime.strptime(d, fmt)
                    except Exception:
                        continue
                return None

            parsed = [( _parse(d), d) for d in seen]
            # sort keeping Nones at the end
            parsed.sort(key=lambda x: (x[0] is None, x[0] or datetime.max))
            sorted_matches = [d for _, d in parsed]
            logger.debug("expiryDates (regex) for %s: %s", symbol, sorted_matches)
            return sorted_matches

        logger.debug("no expiry dates found for %s", symbol)
        return []
    except Exception:
        logger.exception("failed to extract expiry dates for %s", symbol)
        return []
