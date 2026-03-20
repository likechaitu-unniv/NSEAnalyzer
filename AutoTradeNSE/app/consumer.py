"""
app/consumer.py
Reads events from the shared multiprocessing.Queue in an asyncio loop,
runs all metric computations, saves results to SQLite, and broadcasts
to all connected WebSocket clients.
"""

import asyncio
import multiprocessing as mp
import sqlite3
import json
from datetime import datetime
from typing import Optional
import logging

from metrics.metrics import (
    compute_greeks, compute_pcr, compute_max_pain,
    compute_iv_skew, compute_oi_delta,
)

# ── Module-level state ────────────────────────────────────────────────────────
_queue: Optional[mp.Queue] = None
_ws_clients: set = set()

logger = logging.getLogger(__name__)

# Latest snapshot — served to new WebSocket connections immediately
_state = {
    "nifty":     {},
    "banknifty": {},
    "vix":       {},
    "metrics":   {},
}


def set_queue(q: mp.Queue):
    global _queue
    _queue = q


def register_ws(ws):
    _ws_clients.add(ws)


def unregister_ws(ws):
    _ws_clients.discard(ws)


async def broadcast(payload: dict):
    msg = json.dumps(payload)
    dead = set()
    for ws in list(_ws_clients):
        try:
            await ws.send_text(msg)
        except Exception:
            dead.add(ws)
    # remove dead clients without rebinding the module variable
    if dead:
        _ws_clients.difference_update(dead)


# ── SQLite persistence ────────────────────────────────────────────────────────
DB_PATH = "nse_options.db"


def init_db():
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS metric_snapshots (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            ts        TEXT,
            symbol    TEXT,
            event     TEXT,
            payload   TEXT
        )
    """)
    con.commit()
    con.close()


def save_snapshot(ts: str, symbol: str, event: str, payload: dict):
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "INSERT INTO metric_snapshots (ts, symbol, event, payload) VALUES (?,?,?,?)",
        (ts, symbol, event, json.dumps(payload))
    )
    con.commit()
    con.close()


# ── Main consumer loop ────────────────────────────────────────────────────────
async def consume_loop():
    """
    Runs forever inside FastAPI's asyncio event loop.
    Drains the multiprocessing Queue in small batches every 0.5s.
    """
    init_db()
    loop = asyncio.get_event_loop()

    while True:
        if _queue is None:
            await asyncio.sleep(1)
            continue

        # Drain up to 20 events per tick (non-blocking)
        for _ in range(20):
            try:
                event = await loop.run_in_executor(None, _queue.get_nowait)
            except Exception:
                break

            kind = event.get("event")

            if kind == "vix":
                _state["vix"] = event
                await broadcast({"type": "vix", "data": event})

            elif kind == "quote":
                sym = event["symbol"].lower()
                _state[sym] = event
                await broadcast({"type": "quote", "data": event})

            elif kind == "chain":
                await _process_chain(event)

        await asyncio.sleep(0.5)


async def _process_chain(event: dict):
    symbol   = event["symbol"].lower()
    records  = event["records"]
    ts       = event["ts"]
    vix_val  = _state["vix"].get("vix", 15.0)
    quote    = _state.get(symbol, {})
    ltp      = quote.get("ltp", 0)
    pct_chg  = quote.get("pct", 0)

    if not records:
        return

    # Run all metrics (CPU-light enough for main thread)
    records_with_greeks = compute_greeks(records, vix_val)
    pcr      = compute_pcr(records)
    max_pain = compute_max_pain(records)
    iv_skew  = compute_iv_skew(records, ltp)
    oi_delta = compute_oi_delta(records, pct_chg)

    payload = {
        "symbol":   symbol.upper(),
        "ts":       ts,
        "pcr":      pcr,
        "max_pain": max_pain,
        "iv_skew":  iv_skew,
        "oi_delta": oi_delta[:20],  # top 20 strikes for WS bandwidth
    }

    _state["metrics"][symbol] = payload

    # Persist and push
    save_snapshot(ts, symbol.upper(), "chain_metrics", payload)
    await broadcast({"type": "chain_metrics", "data": payload})
    logger.info("[consumer] %s PCR=%s MaxPain=%s", symbol.upper(), pcr.get('pcr_oi'), max_pain.get('max_pain'))
