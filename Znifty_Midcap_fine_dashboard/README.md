# Nifty Midcap Dashboard - Professional Analytics

## Overview
This is a comprehensive real-time Nifty Midcap 50 trading analytics dashboard built with HTML5, JavaScript, and WebSocket communication. It provides professional traders with multi-faceted market analysis including index options Greeks, PCR analysis, and trend history visualization.

---

## Dashboard Structure

### 1. **STOCKS TAB** 📈
Displays comprehensive stock market analysis across Nifty Midcap 50 constituents.

#### Key Metrics Displayed:
- **Market Trend**: Overall bullish/bearish sentiment with advancers/decliners count
- **Bull Power**: Weighted bullish power, Bear Power, and Net Power calculations
- **Market Insights**: Market sentiment, breadth ratio, volatility metrics
- **Volatility & Volume**: Total trading volume, gainers, and losers count

#### Data Sections:
- **Gaining Stocks Table**: Lists all stocks with positive movement
  - Sortable by: Symbol, Rate (Price), Change Amount, Weight Points
  - Color-coded in green (#4CAF50)
  
- **Losing Stocks Table**: Lists all stocks with negative movement
  - Sortable by: Symbol, Rate (Price), Change Amount, Weight Points
  - Color-coded in red (#FF6B6B)

#### Functions:
- `loadStocksData()`: Fetches stock analysis from `/api/analyze-stocks`
- `displayStocksData(data)`: Populates all stock metrics and tables
- `sortStocksGainersTable(column)`: Sorts gainers by selected column
- `sortStocksLosersTable(column)`: Sorts losers by selected column

---

### 2. **OPTIONS ANALYSIS TAB** 📊
Provides in-depth options Greeks and market sentiment analysis.

#### Primary Signal Section:
- **Final Signal**: BULLISH/BEARISH/NEUTRAL with confidence percentage
- **Signal Badge**: Visual indicator with color coding
- **Action**: Recommended trading action based on analysis

#### PCR (Put-Call Ratio) Analysis:
- **Overall PCR**: Ratio of total put and call open interest
- **PCR Signal**: Interpretation of ratio (neutral range: 0.7-1.4)
- **PCR Volume**: Alternative PCR using volume data

#### Max Pain Analysis:
- **Max Pain Strike**: Strike level where maximum pain (financial loss) occurs
- **Current Spot Price**: Underlying Nifty value
- **Distance**: Points away from max pain level

#### OI Buildup Analysis:
- **Call OI**: Total call option open interest
- **Put OI**: Total put option open interest
- **CE Buildup Type**: STRONG/WEAK classification for calls
- **PE Buildup Type**: STRONG/WEAK classification for puts
- **Buildup Signal**: Based on OI patterns (BULLISH/BEARISH/NEUTRAL)

#### Market Pressure Analysis:
- **Net Pressure**: PE OI minus CE OI (positive = bearish, negative = bullish)
- **Pressure Signal**: Market directionality indicator

#### IV (Implied Volatility) Analysis:
- **ATM IV**: At-The-Money volatility
- **IV Skew**: Difference between call and put IV
- **CE IV / PE IV**: Individual implied volatility by option type

#### Support & Resistance:
- **Immediate Resistance**: Key overhead level
- **Immediate Support**: Key support level

#### Options Chain Table:
- Displays all option strikes with detailed information
- **Columns** (toggleable):
  - Strike Price
  - CE/PE Last Traded Price (LTP)
  - Spot Distance (absolute and percentage)
  - Open Interest for CE/PE
  - Implied Volatility for CE/PE
  - Price Changes for CE/PE
  - Buildup Types

#### Functions:
- `displayOptionsData(data)`: Populates all options metrics
- `createOptionsColumnToggles()`: Creates column visibility controls
- `toggleOptionsColumn(key)`: Toggle column visibility
- `renderOptionsTable()`: Renders filterable options chain

---

### 3. **TREND ANALYSIS SUB-SECTION** 🔄
Integrated within the OPTIONS tab, provides combined market analysis.

#### Market Analysis Card (80% Weight):
- **Market Trend**: Combined bullish/bearish from stocks
- **Advancers/Decliners**: Count of gaining/losing stocks
- **Average Change**: Mean price change percentage
- **Primary Signal**: From options analysis with confidence
- **Action**: Trading recommendation

#### CE vs PE Buildup Card (5% Weight):
- **Buildup Signal**: BULLISH/BEARISH based on OI pattern
- **Call Writing**: Heavy call option writing volume
- **Put Writing**: Heavy put option writing volume
- **Derived Decision**: 
  - PUT DOMINANCE: Heavy PE writing (bullish correction setup)
  - CALL DOMINANCE: Heavy CE writing (bearish trend)
  - BALANCED: Mixed signals
- **Decision Rationale**: Interpretation explanation

#### PCR Analysis Card:
- **Current PCR (OI)**: Current put-call ratio
- **PCR High/Low**: Range during tracking period
- **PCR Direction**: Moving UP/DOWN with change percentage
- **PCR Trend**: Current trend interpretation

#### Statistics Card:
- **Total Trends**: Total analysis records
- **Bullish Count**: Number of bullish signals
- **Bearish Count**: Number of bearish signals
- **Neutral Count**: Number of neutral signals

#### Trend Charts:
All charts display time-series data with 6 interactive visualizations:

1. **PCR Trend Chart**: PCR (OI) and PCR (Volume) over time
2. **Advancers & Decliners Trend**: Movement of advancers vs decliners
3. **Call vs Put Writing Trend**: CE buildup vs PE buildup
4. **Nifty Value Trend**: Spot price movement over time
5. **Call OI vs Put OI Trend**: Open interest comparison
6. **Signal Confidence Trend**: Confidence percentage evolution

#### Recent Trend History Table:
- Shows last 50 records, sorted latest first
- **Columns**:
  - Time: Timestamp of analysis
  - Nifty Value: Spot price
  - PCR (OI): Put-call open interest ratio
  - PCR (Vol): Put-call volume ratio
  - Sentiment: Bullish/Bearish/Neutral
  - IV Rank: Implied volatility ranking
  - Call OI: Call open interest
  - Put OI: Put open interest

#### Functions:
- `loadTrendsData()`: Fetches trends from `/api/get-trends` and stocks from `/api/analyze-stocks`
- `displayTrendsData(data, stocksData)`: Populates all trend sections
- `plotTrendChart(trends)`: Renders PCR trend chart
- `plotAdvancersDeclinersChart(trends)`: Renders A/D trend chart
- `plotCallPutWritingChart(trends)`: Renders CE/PE trend chart
- `plotNiftyValueChart(trends)`: Renders price trend chart
- `plotCallPutOIChart(trends)`: Renders OI trend chart
- `plotConfidenceChart(trends)`: Renders confidence trend chart

---

### 4. **GREEKS TAB** ξ
Displays detailed Greeks analysis for all option strike prices.

#### Overview Section:
- **Expiry Date**: Current option contract expiry
- **Days to Expiry**: Time remaining (in days)

#### ATM (At-The-Money) Greeks Sections:

**For Call Options (CE):**
- **Delta (Δ)**: Rate of change of option price with spot price
- **Gamma (Γ)**: Rate of change of delta
- **Theta (Θ)**: Time decay (daily loss in option value)
- **Vega**: Sensitivity to volatility changes
- **IV**: Implied Volatility percentage

**For Put Options (PE):**
- Same Greeks calculations as calls but with opposite delta sign

#### Open Interest Metrics:
- **CE OI**: Call option open interest (in millions)
- **PE OI**: Put option open interest (in millions)
- **OI Ratio**: PE OI / CE OI (>1 = more puts open)

#### Greeks Chain Table:
Comprehensive strike-by-strike breakdown with toggleable columns:
- **Strike**: Option strike price
- **CE Δ, Γ, Θ**: Call Greeks
- **PE Δ, Γ, Θ**: Put Greeks
- **CE OI, PE OI**: Open interest by strike

#### Functions:
- `displayGreeksData(data)`: Populates Greeks metrics and table
- `createGreeksColumnToggles()`: Creates column visibility controls
- `toggleGreeksColumn(key)`: Toggle column visibility
- `renderGreeksTable(data)`: Renders filterable Greeks table

---

## Technical Architecture

### Data Flow:
1. **WebSocket Connection** (Socket.IO):
   - Real-time data streaming from Python backend
   - `socket.on('analysis_data')`: Receives complete analysis package

2. **REST API Endpoints**:
   - `/api/analyze-stocks`: Nifty 50 stock analysis
   - `/api/get-trends`: Historical trend data with 50 recent records

3. **Global Data Storage**:
   - `currentData`: Holds complete analysis payload
   - `stocksData`: Stores stocks analysis
   - `greeksData`: Stores Greeks analysis

### UI/UX Features:
1. **Tab Navigation**: Easy switching between Stocks, Options, Greeks, Trends
2. **Responsive Grid Layout**: Adapts to screen sizes (mobile, tablet, desktop)
3. **Color Coding**:
   - Green (#4CAF50): Bullish, gains, positive signals
   - Red (#FF6B6B): Bearish, losses, negative signals
   - Orange (#FFA500): Neutral, warnings, caution
   - Cyan (#00bfff): Accent, key metrics
   
4. **Sorting**: Tables support column-based sorting (ascending/descending)
5. **Column Toggles**: Hide/show table columns for custom views
6. **Chart.js Integration**: Real-time trend visualization
7. **Dark Theme**: Professional dark interface with high contrast

### Interactive Elements:
- **Theme Toggle**: Invert colors for alternative theme
- **Expiry Date Selector**: Change analysis period via date input
- **Sort Functions**: Click column headers to sort
- **Column Visibility**: Toggle switches for each table column
- **Auto-Refresh**: Trends tab auto-refreshes every 15 seconds

---

## Signal Interpretations

### Final Signal Categories:
- **BULLISH**: Favors upside movement, BUY setup
- **BEARISH**: Favors downside movement, SELL setup
- **NEUTRAL**: Mixed signals, WAIT for clarity

### Confidence Levels:
- 0-30%: Low confidence, risky trades
- 30-70%: Moderate confidence, regular trading
- 70-100%: High confidence, strong setup

### PCR Interpretation:
- **0.7-1.4**: Neutral zone (balanced sentiment)
- **<0.7**: Bullish zone (more calls, upside risk)
- **>1.4**: Bearish zone (more puts, downside risk)

### OI Buildup Signals:
- **Heavy CE Writing**: Sellers expect range-bound to bearish move
- **Heavy PE Writing**: Sellers expect upside move (bullish correction)
- **Balanced**: No strong directional bias

### Max Pain Level:
- Indicates where maximum option sellers' profit occurs
- Price tends to move toward this level
- Distance from spot shows potential movement

---

## Data Update Frequency

- **Stocks Tab**: On-demand loading via "Stocks" button click
- **Options Analysis**: Real-time via WebSocket (analysis_data event)
- **Trends Tab**: Auto-refresh every 15 seconds (configurable)
- **Greeks Data**: Updated with each analysis_data event

---

## Color Scheme
| Element | Color | Usage |
|---------|-------|-------|
| Background | #1a1f3a | Main page background |
| Card Background | #252d4a | Content cards |
| Accent | #00bfff | Highlights, key values |
| Bullish | #4CAF50 | Green for gains/bullish |
| Bearish | #FF6B6B | Red for losses/bearish |
| Neutral | #FFA500 | Orange for caution/neutral |
| Text Primary | #ffffff | Main text |
| Text Secondary | #b0b8d4 | Secondary labels |
| Border | #3a4563 | Card borders |

---

## Key Features Summary

✅ **Real-time Analysis**: WebSocket-based live data updates
✅ **Multi-level Insights**: Stocks, Options, Greeks, Trends
✅ **Comprehensive Greeks**: All Greeks for all strikes
✅ **PCR Analysis**: Both OI and Volume-based ratios
✅ **Max Pain**: Strike-level analysis
✅ **OI Buildup**: CE vs PE heavy positions
✅ **Market Sentiment**: Advancers/Decliners, Breadth ratio
✅ **Historical Trends**: 50-record history with charts
✅ **Interactive Tables**: Sortable, filterable columns
✅ **Responsive Design**: Works on all screen sizes
✅ **Dark Theme**: Eye-friendly professional interface
✅ **Customizable View**: Toggle table columns as needed

---

## Usage Instructions

1. **Initial Load**: Page loads Stocks data automatically
2. **Switch Tabs**: Click tab buttons to navigate
3. **Stocks Tab**: 
   - View market trend and power metrics
   - Sort gaining/losing stocks by clicking column headers
4. **Options Tab**:
   - View signals, PCR, Max Pain analyses
   - Toggle columns to customize view
   - Scroll for trend history table
5. **Greeks Tab**:
   - Check Greeks for all strikes
   - Toggle columns for focused view
6. **Trends Tab**:
   - Monitor trend history (auto-updates)
   - Review charts for pattern analysis
   - Check recent trends table

---

## Performance Optimization

- **Efficient Rendering**: Conditional display of loading states
- **Chart Destruction**: Previous charts destroyed before creating new ones
- **Data Sorting**: Client-side sorting without re-fetching
- **Column Filtering**: Toggle without re-rendering entire table
- **Debounced Updates**: 15-second refresh interval prevents API overload

---

## Browser Compatibility

- Chrome/Chromium: Full support
- Firefox: Full support
- Safari: Full support
- Edge: Full support
- Mobile browsers: Responsive, optimized layout

---

**Last Updated**: January 7, 2026
**Version**: Professional Analytics v1.0
