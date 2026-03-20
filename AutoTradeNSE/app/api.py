"""
app/api.py
FastAPI application — REST endpoints + WebSocket for live metric push.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from typing import Optional
import logging
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from app.consumer import consume_loop, register_ws, unregister_ws, _state
from ingestion.nse_session import make_session, safe_get, build_chain_url, get_expiry_dates

logger = logging.getLogger(__name__)

app = FastAPI(title="NSE Options Analytics")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    asyncio.create_task(consume_loop())


# ── REST endpoints ────────────────────────────────────────────────────────────

@app.get("/api/metrics/{symbol}")
def get_metrics(symbol: str):
    """Latest computed metrics snapshot for a symbol."""
    return _state["metrics"].get(symbol.lower(), {})


@app.get("/api/vix")
def get_vix():
    return _state.get("vix", {})


@app.get("/api/quote/{symbol}")
def get_quote(symbol: str):
    return _state.get(symbol.lower(), {})


@app.get("/api/health")
def health():
    return {"status": "ok"}


# Proxy endpoint to fetch option-chain from NSE (includes optional expiry)
@app.get("/api/option-chain-indices")
def option_chain_indices(symbol: str, expiry: Optional[str] = None):
    """Proxy to NSE option-chain-v3 endpoint.

    If `expiry` is not provided, the endpoint will attempt to pick the nearest
    expiry by querying the chain metadata first.
    """
    session = make_session()

    # If expiry not provided, try to obtain available expiries
    if not expiry:
        expiries = get_expiry_dates(session, symbol)
        if expiries:
            expiry = expiries[0]
            logger.debug("selected expiry for %s: %s", symbol, expiry)

    url = build_chain_url(symbol, expiry)
    logger.debug("proxy requesting chain URL: %s", url)
    raw = safe_get(session, url)
    if raw is None:
        raise HTTPException(status_code=502, detail="Upstream NSE request failed")
    return raw


# ── WebSocket ─────────────────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """
    Clients connect here to receive live metric updates.
    On connect, sends the full current state immediately.
    """
    await ws.accept()
    register_ws(ws)
    try:
        # Push current state to new client immediately
        import json
        await ws.send_text(json.dumps({"type": "snapshot", "data": _state}))
        # Keep connection alive — messages come via broadcast()
        while True:
            await asyncio.sleep(30)
            await ws.send_text('{"type":"ping"}')
    except WebSocketDisconnect:
        pass
    finally:
        unregister_ws(ws)
