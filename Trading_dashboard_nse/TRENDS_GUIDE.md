# Trend Data Storage & Dashboard Guide

## Overview
The Trend feature automatically captures market analysis data and stores it for historical tracking and visualization on the dashboard.

## What Gets Recorded

The system automatically records the following data at regular intervals:

- **Timestamp**: When the data was captured
- **Nifty Value**: Current Nifty 50 index value
- **PCR (OI)**: Put-Call Ratio based on Open Interest
- **PCR (Volume)**: Put-Call Ratio based on Trading Volume
- **Sentiment**: Market sentiment (bullish/bearish/neutral)
- **IV Rank**: Implied Volatility Rank
- **Call OI**: Total Call Open Interest
- **Put OI**: Total Put Open Interest

## Dashboard Pages

### 📈 Stocks (`/stocks`)
- Market breadth overview (gainers/losers)
- Top gaining and losing stocks table
- Auto-refreshes every 15 seconds

### 📊 Analysis (`/options`)
- Options chain analysis
- Trend Analysis (OI buildup, PCR, signals)
- Global Bias + Scalper Playbook
- Real-time Socket.IO updates

### ξ Greeks (`/greeks`)
- ATM CE/PE Greeks (Delta, Gamma, Theta, Vega)
- Portfolio Greeks with traffic-light indicators
- Greeks chain table with ±N strike filters

### 📉 Trends (`/trends`)
- Market Analysis card (advancers/decliners bar)
- CE vs PE Buildup card with sparkline
- PCR Analysis with visual bar
- Enhanced V2.0 Score (9-factor model)
- OI by Strike chart
- Strategy Recommendations

### 📖 Guide (`/guide`)
- This page — reference documentation

---

## Files Involved

### `trend_storage.py`
Core module for reading/writing trend data.

**Key Methods:**
- `write_trend(data)` — Write a single trend entry
- `read_all_trends()` — Get all stored trends
- `read_recent_trends(limit)` — Get N most recent trends
- `get_trend_statistics()` — Get summary statistics

### `apps.py`
Flask application with integrated trend recording.

**API Endpoints:**
- `GET /api/get-trends` — Retrieve trend data and statistics
- `GET /api/analyze-options` — Full options chain analysis
- `GET /api/analyze-stocks` — Stock breadth analysis
- `GET /api/strategy` — Strategy recommendations
- `GET /api/pcr-by-expiry` — PCR breakdown by expiry
- `GET /api/nifty-futures` — Live Nifty Futures price
- `GET /api/get-guide` — This guide content
- `POST /api/write-trend` — Manually record a trend

---

## Data Storage

Trends are stored in: `data/trend_history_<date>.json`

File structure:
```json
{
  "created_at": "2026-03-23T09:30:00",
  "last_updated": "2026-03-23T15:45:30",
  "trends": [
    {
      "timestamp": "2026-03-23T09:35:00",
      "nifty_value": 22456.50,
      "pcr_oi": 1.15,
      "pcr_volume": 1.08,
      "sentiment": "bullish",
      "iv_rank": 65,
      "call_oi": 234567,
      "put_oi": 245678
    }
  ]
}
```

---

## Sentiment Interpretation

| Sentiment | PCR (OI) | Meaning |
|-----------|----------|---------|
| **Bullish** | > 1.0 | More puts = market oversold, potential reversal up |
| **Neutral** | 0.7 – 1.0 | Balanced put-call ratio |
| **Bearish** | < 0.7 | More calls = market overbought, potential reversal down |

---

## Enhanced V2.0 Score (9 Factors)

| # | Factor | Bullish Range | Bearish Range |
|---|--------|--------------|---------------|
| 1 | Spot vs Max Pain | Spot > MaxPain | Spot < MaxPain |
| 2 | PCR (OI) | > 1.3 | < 0.7 |
| 3 | IV Skew (PE-CE%) | < -5% | > 10% |
| 4 | Gamma Diff (CE-PE) | > 0.001 | < -0.001 |
| 5 | ATM Delta (CE) | > 0.55 | < 0.45 |
| 6 | Theta Ratio (\|CE\|/\|PE\|) | < 0.9 | > 1.1 |
| 7 | VIX / VIX Δ | < 13 & falling | > 18 |
| 8 | Breadth | > 1.5% | < -1.5% |
| 9 | Portfolio Vega | Vega > 20 + VIX falling | — |

**Score Interpretation:**
- `>= 3.0` → Bullish
- `<= -3.0` → Bearish
- Otherwise → Neutral

---

## Global Bias Logic

The **Global Bias** header combines 4 signals:
1. Market Trend (Stocks breadth)
2. Intraday Signal (Options analysis)
3. Delta Signal (Portfolio Greeks)
4. Fast Moving Options direction

| Bull signals | Bear signals | Bias |
|---|---|---|
| ≥ 3 | any | Strong Bullish |
| any | ≥ 3 | Strong Bearish |
| > Bear | < Bull | Mild Bullish |
| < Bull | > Bear | Mild Bearish |

---

## Troubleshooting

**Guide not loading (500 error)?**
- Ensure `TRENDS_GUIDE.md` exists in the app directory (same folder as `apps.py`)
- Check Flask console for the actual Python error

**No trend data in chart?**
- Verify `/api/get-trends` returns data
- Check the `data/` folder for `.json` files

**Strategy shows "Loading…"?**
- Click **🔄 Refresh Strategy** on the Trends page
- Verify `/api/strategy` is accessible

**Charts blank after page loads?**
- Charts may need a moment to resize after the content becomes visible — try scrolling or resizing the window

---

## Running the App

```bash
cd Trading_dashboard_nse
python apps.py
```

Open: [http://localhost:5000](http://localhost:5000)
