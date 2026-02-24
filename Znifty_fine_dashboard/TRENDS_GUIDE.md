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

## Files Involved

### 1. `trend_storage.py`
Core module for reading/writing trend data.

**Key Methods:**
- `write_trend(data)` - Write a single trend entry
- `read_all_trends()` - Get all stored trends
- `read_recent_trends(limit)` - Get N most recent trends
- `read_trends_by_sentiment(sentiment)` - Filter by sentiment
- `get_trend_statistics()` - Get summary statistics

### 2. `apps.py`
Flask application with integrated trend recording:

**API Endpoints:**
- `GET /api/get-trends` - Retrieve trend data and statistics
- `POST /api/write-trend` - Manually write trend data (optional)

The `transmit_option_analysis()` function automatically writes trends every 5 seconds.

### 3. `templates/dashboard.html`
Dashboard with new Trends tab showing:
- **Statistics Card**: Summary of recorded trends
- **Trends Table**: Recent 50 trend records with sortable columns
- **Trend Chart**: PCR (OI) and PCR (Volume) visualization over time

## Data Storage

Trends are stored in: `data/trend_history.json`

File structure:
```json
{
  "created_at": "2025-01-05T10:30:00",
  "last_updated": "2025-01-05T16:45:30",
  "trends": [
    {
      "timestamp": "2025-01-05T10:35:00",
      "nifty_value": 23456.50,
      "pcr_oi": 1.15,
      "pcr_volume": 1.08,
      "sentiment": "bullish",
      "iv_rank": 65,
      "call_oi": 234567,
      "put_oi": 245678,
      "recorded_at": "2025-01-05T10:35:00"
    }
  ]
}
```

## Usage

### Automatic Recording
Once the Flask app starts, trends are automatically recorded every 5 seconds.

### Viewing Trends
1. Open the dashboard
2. Click on the **📉 Trends** tab
3. View statistics and recent trend history
4. Analyze the trend chart for PCR movements

### Manual Recording (Optional)
```python
from trend_storage import TrendStorage

storage = TrendStorage()

# Write a single trend
storage.write_trend({
    'nifty_value': 23456.50,
    'pcr_oi': 1.15,
    'sentiment': 'bullish',
    'iv_rank': 65
})

# Read recent trends
trends = storage.read_recent_trends(50)

# Get statistics
stats = storage.get_trend_statistics()
```

## Data Management

### Keep File Size Manageable
```python
from trend_storage import TrendStorage

storage = TrendStorage()

# Keep only last 500 trends (delete older ones)
storage.clear_old_trends(keep_last_n=500)
```

### Export for Analysis
```python
storage.export_to_csv('trends_backup.csv')
```

## Dashboard Features

### 📊 Statistics Card
Shows total trends recorded and breakdown by sentiment:
- Bullish trends
- Bearish trends
- Neutral trends

### 📈 Recent Trends Table
- Displays last 50 recorded trends
- Columns: Time, Nifty Value, PCR (OI), PCR (Vol), Sentiment, IV Rank, Call OI, Put OI
- Scrollable for easy navigation

### 📉 Trend Chart
- Line chart showing PCR trends over time
- Two lines:
  - **PCR (OI)**: Put-Call Ratio by Open Interest (Blue)
  - **PCR (Volume)**: Put-Call Ratio by Volume (Green)
- Interactive tooltips showing exact values

## Sentiment Interpretation

| Sentiment | PCR (OI) | Meaning |
|-----------|----------|---------|
| **Bullish** | > 1.0 | More puts = market oversold, potential reversal up |
| **Neutral** | 0.7 - 1.0 | Balanced put-call ratio |
| **Bearish** | < 0.7 | More calls = market overbought, potential reversal down |

## Troubleshooting

**No trends showing in dashboard?**
- Check that `/api/get-trends` endpoint is working
- Ensure `data/` directory exists
- Look for error messages in Flask console

**Data not updating?**
- Verify `transmit_option_analysis()` thread is running
- Check if NSE API is accessible
- Look at Flask logs for errors

**Chart not displaying?**
- Ensure Chart.js library is loaded
- Check browser console for JavaScript errors
- Verify trend data contains numeric PCR values

## Future Enhancements

Potential features to add:
- Trend prediction using ML models
- Support for multiple expiry dates
- Alert system for sentiment changes
- Export to database instead of JSON
- Real-time trend streaming to multiple clients
