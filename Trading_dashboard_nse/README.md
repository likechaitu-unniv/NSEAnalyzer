# Trading Dashboard — Stock Insights

This update adds a simple Stock Insights page and a backend proxy to fetch real-time equity quotes from NSE.

New features
- Route: `/stock/<symbol>` — UI page for a single stock (e.g. `/stock/RELIANCE`).
- API: `/api/quote/<symbol>` — server-side proxy that calls `https://www.nseindia.com/api/quote-equity?symbol=...` and returns JSON.

How it works
- A new helper `fetch_quote_equity(symbol)` was added to `utils.py` which prefetches the NSE homepage (to obtain cookies) and requests the quote API.
- `apps.py` exposes `/api/quote/<symbol>` that returns the NSE response under the `data` key.
- A new template `templates/stock_insights.html` polls the API every 5 seconds and displays key fields.
- The main dashboard `templates/dashboard.html` has a quick link button to open `/stock/RELIANCE`.

Notes & caveats
- NSE sometimes blocks automated requests; the proxy uses the same request headers and a session to reduce blocking but may still fail if NSE blocks the host/IP.
- The page shows raw JSON as a fallback to help debugging.

Try it
1. Start the Flask app (from the project root):

```bash
python apps.py
```

2. Open: `http://localhost:5000/stock/RELIANCE`
