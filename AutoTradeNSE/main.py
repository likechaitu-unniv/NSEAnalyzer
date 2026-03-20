"""
main.py  —  NSE Options Data System
Spawns 3 parallel scraper processes, then starts the FastAPI server.
Run:  python main.py
"""

import multiprocessing as mp
import time
import signal
import sys
import threading
import uvicorn
import logging

from logging_config import setup_logging
from typing import List, Tuple, Callable

from ingestion.chain_scraper import run_chain_scraper
from ingestion.vix_scraper   import run_vix_scraper
from ingestion.quote_scraper import run_quote_scraper
from app.consumer            import set_queue
from app.api                 import app

logger = logging.getLogger(__name__)

# ── shared typed event queue ─────────────────────────────────────────────────
DATA_QUEUE: mp.Queue = mp.Queue(maxsize=500)

SCRAPERS: List[Tuple[str, Callable]] = [
    ("chain_scraper", run_chain_scraper),
    #("vix_scraper",   run_vix_scraper),
    #("quote_scraper", run_quote_scraper),
]


def spawn_scrapers(queue: mp.Queue) -> List[mp.Process]:
    processes = []
    for name, target in SCRAPERS:
        p = mp.Process(target=target, args=(queue,), name=name, daemon=True)
        p.start()
        logger.info(f"[main] started {name} (pid={p.pid})")
        processes.append(p)
    return processes


def watchdog(processes: List[mp.Process], queue: mp.Queue):
    """Restart any scraper that dies unexpectedly."""
    while True:
        time.sleep(10)
        for i, (name, target) in enumerate(SCRAPERS):
            p = processes[i]
            if not p.is_alive():
                logger.warning(f"[watchdog] {name} died — restarting")
                new_p = mp.Process(target=target, args=(queue,), name=name, daemon=True)
                new_p.start()
                processes[i] = new_p


def shutdown(sig, frame):
    logger.info("[main] shutting down")
    sys.exit(0)


if __name__ == "__main__":
    # On Windows, spawn is already the default — setting it again raises
    # RuntimeError: context has already been set. This guard prevents that.
    if mp.get_start_method(allow_none=True) is None:
        mp.set_start_method("spawn")

    # initialize logging for the application (console at DEBUG by default)
    setup_logging(level=logging.DEBUG)

    signal.signal(signal.SIGINT, shutdown)

    set_queue(DATA_QUEUE)

    processes = spawn_scrapers(DATA_QUEUE)

    t = threading.Thread(target=watchdog, args=(processes, DATA_QUEUE), daemon=True)
    t.start()

    logger.info("[main] starting FastAPI on http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
