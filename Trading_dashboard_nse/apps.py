"""
Unified Flask Web Application for Nifty Trend Analysis
Combines both stock analyzer and option chain analyzer
"""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from Analyzer import NiftyTrendAnalyzer, fetch_nifty_option_chain
from trend_storage import TrendStorage
from utils import fetch_india_vix, fetch_available_expiries
from utils import fetch_nifty_option_chain
import threading
import time
import requests
from datetime import datetime

print("[DEBUG] apps.py module loaded")

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# Global expiry variable for options (will attempt to auto-select from NSE)
default_expiry = '23-Feb-2026'
expiry = default_expiry

# Attempt to read valid expiries from NSE and pick an appropriate one
try:
    expiries = fetch_available_expiries('NIFTY')
    from datetime import datetime, date
    parsed = []
    for s in expiries:
        try:
            d = datetime.strptime(s, "%d-%b-%Y").date()
            parsed.append((d, s))
        except Exception:
            # skip unparsable formats
            continue

    today = date.today()
    future = [ (d,s) for (d,s) in parsed if d >= today ]
    if future:
        # pick the nearest future expiry
        expiry = sorted(future, key=lambda x: x[0])[0][1]
        print(f"[DEBUG] Selected expiry from NSE (nearest future): {expiry}")
    elif parsed:
        # fallback: pick latest available
        expiry = sorted(parsed, key=lambda x: x[0])[-1][1]
        print(f"[DEBUG] Selected expiry from NSE (latest available): {expiry}")
    else:
        print(f"[WARN] No valid expiry parsed from NSE response, using default {default_expiry}")
except Exception as e:
    print(f"[WARN] Could not fetch expiries from NSE: {e}; using default {default_expiry}")

# Initialize trend storage with chosen expiry
trend_storage = TrendStorage(expiry=expiry)


class NiftyStockAnalyzer:
    """Business logic for analyzing Nifty 50 stock data"""
    
    def __init__(self):
        print("[DEBUG] Initializing NiftyStockAnalyzer")
        self.api_url = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        print("[DEBUG] NiftyStockAnalyzer initialized")
    
    def fetch_nifty_data(self):
        """Fetch data from NSE API"""
        print("[DEBUG] fetch_nifty_data() called")
        try:
            print("[DEBUG] Making request to NSE API...")
            response = requests.get(self.api_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            print(f"[DEBUG] NSE API response status: {response.status_code}")
            return response.json()
        except Exception as e:
            print(f"[ERROR] Error fetching data: {e}")
            print("[DEBUG] Falling back to sample data")
            return self.get_sample_data()
    
    def get_sample_data(self):
        """Return sample data for demonstration"""
        return {
            "data": [
                {"symbol": "RELIANCE", "lastPrice": 2450.50, "change": 45.30, "pChange": 1.88, "totalTradedVolume": 5500000},
                {"symbol": "TCS", "lastPrice": 3650.20, "change": -25.40, "pChange": -0.69, "totalTradedVolume": 2100000},
                {"symbol": "HDFCBANK", "lastPrice": 1625.80, "change": 32.15, "pChange": 2.02, "totalTradedVolume": 8900000},
                {"symbol": "INFY", "lastPrice": 1480.40, "change": -18.60, "pChange": -1.24, "totalTradedVolume": 4200000},
                {"symbol": "ICICIBANK", "lastPrice": 1089.25, "change": 28.75, "pChange": 2.71, "totalTradedVolume": 6700000},
                {"symbol": "HINDUNILVR", "lastPrice": 2385.60, "change": -12.30, "pChange": -0.51, "totalTradedVolume": 1800000},
                {"symbol": "BHARTIARTL", "lastPrice": 1256.45, "change": 22.10, "pChange": 1.79, "totalTradedVolume": 5300000},
                {"symbol": "ITC", "lastPrice": 425.80, "change": 8.90, "pChange": 2.14, "totalTradedVolume": 7200000},
                {"symbol": "KOTAKBANK", "lastPrice": 1745.30, "change": -15.20, "pChange": -0.86, "totalTradedVolume": 3100000},
                {"symbol": "LT", "lastPrice": 3456.70, "change": 65.40, "pChange": 1.93, "totalTradedVolume": 2400000},
                {"symbol": "SBIN", "lastPrice": 625.30, "change": 12.50, "pChange": 2.04, "totalTradedVolume": 9100000},
                {"symbol": "AXISBANK", "lastPrice": 1089.60, "change": -8.40, "pChange": -0.77, "totalTradedVolume": 4500000},
                {"symbol": "WIPRO", "lastPrice": 445.80, "change": 5.60, "pChange": 1.27, "totalTradedVolume": 3200000},
                {"symbol": "MARUTI", "lastPrice": 10250.40, "change": -85.30, "pChange": -0.83, "totalTradedVolume": 850000},
                {"symbol": "TITAN", "lastPrice": 3125.90, "change": 78.90, "pChange": 2.59, "totalTradedVolume": 1950000},
            ]
        }
    
    def calculate_weightage(self, stocks):
        """Calculate weightage of each stock based on market cap"""
        total_value = sum(stock['lastPrice'] * stock.get('totalTradedVolume', 1) for stock in stocks)
        
        for stock in stocks:
            market_value = stock['lastPrice'] * stock.get('totalTradedVolume', 1)
            stock['weight'] = (market_value / total_value * 100) if total_value > 0 else 0
            stock['impact'] = (stock['weight'] * stock['pChange']) / 100
        
        return sorted(stocks, key=lambda x: x['weight'], reverse=True)
    
    def identify_market_trend(self, stocks):
        """Identify market trend based on weighted power of stock changes"""
        advancers = [s for s in stocks if s['pChange'] > 0]
        decliners = [s for s in stocks if s['pChange'] < 0]
        
        avg_change = sum(s['pChange'] for s in stocks) / len(stocks) if stocks else 0
        
        # Calculate weighted power (consider both count and magnitude)
        bull_power = sum(s.get('weight', 0) * s['pChange'] for s in advancers) if advancers else 0
        bear_power = sum(s.get('weight', 0) * abs(s['pChange']) for s in decliners) if decliners else 0
        net_power = bull_power - bear_power
        
        # Trend should be based on net power, not just count
        trend = 'Neutral'
        if net_power > 15 and len(advancers) > len(decliners):
            trend = 'Strong Bullish'
        elif net_power > 0 and len(advancers) > len(decliners):
            trend = 'Bullish'
        elif net_power < -15 and len(decliners) > len(advancers):
            trend = 'Strong Bearish'
        elif net_power < 0 and len(decliners) > len(advancers):
            trend = 'Bearish'
        
        return {
            'trend': trend,
            'avg_change': round(avg_change, 2),
            'advancers': len(advancers),
            'decliners': len(decliners),
            'unchanged': len(stocks) - len(advancers) - len(decliners)
        }
    
    def identify_major_movers(self, stocks):
        """Identify stocks that are major market movers"""
        major_movers = [s for s in stocks if abs(s['pChange']) > 1]
        return sorted(major_movers, key=lambda x: abs(x['impact']), reverse=True)[:5]
    
    def calculate_bull_bear_power(self, stocks):
        """Calculate bull and bear power weightage"""
        bull_power = sum(s['weight'] * s['pChange'] for s in stocks if s['pChange'] > 0)
        bear_power = sum(s['weight'] * abs(s['pChange']) for s in stocks if s['pChange'] < 0)
        
        return {
            'bull_power': round(bull_power, 2),
            'bear_power': round(bear_power, 2),
            'net_power': round(bull_power - bear_power, 2)
        }
    
    def calculate_market_insights(self, stocks):
        """Calculate additional market insights"""
        total_stocks = len(stocks)
        strong_gainers = len([s for s in stocks if s['pChange'] > 2])
        strong_losers = len([s for s in stocks if s['pChange'] < -2])
        
        total_volume = sum(s.get('totalTradedVolume', 0) for s in stocks)
        high_volume_stocks = sorted(stocks, key=lambda x: x.get('totalTradedVolume', 0), reverse=True)[:5]
        
        avg_positive_change = sum(s['pChange'] for s in stocks if s['pChange'] > 0) / max(len([s for s in stocks if s['pChange'] > 0]), 1)
        avg_negative_change = sum(s['pChange'] for s in stocks if s['pChange'] < 0) / max(len([s for s in stocks if s['pChange'] < 0]), 1)
        
        breadth_ratio = len([s for s in stocks if s['pChange'] > 0]) / total_stocks * 100 if total_stocks > 0 else 0
        
        price_changes = [abs(s['pChange']) for s in stocks]
        avg_volatility = sum(price_changes) / len(price_changes) if price_changes else 0
        
        return {
            'total_stocks': total_stocks,
            'strong_gainers': strong_gainers,
            'strong_losers': strong_losers,
            'total_volume': total_volume,
            'high_volume_stocks': high_volume_stocks,
            'avg_positive_change': round(avg_positive_change, 2),
            'avg_negative_change': round(avg_negative_change, 2),
            'breadth_ratio': round(breadth_ratio, 2),
            'avg_volatility': round(avg_volatility, 2),
            'market_sentiment': self._determine_sentiment(breadth_ratio, avg_positive_change, avg_negative_change)
        }
    
    def _determine_sentiment(self, breadth_ratio, avg_positive_change, avg_negative_change):
        """Determine sentiment based on breadth ratio and magnitude of changes"""
        # Compare strength of positive vs negative moves
        move_strength_ratio = avg_positive_change / abs(avg_negative_change) if avg_negative_change != 0 else 0
        
        # If more decliners OR decliners are stronger, sentiment is negative
        if breadth_ratio < 45:
            return 'Negative' if move_strength_ratio < 1.2 else 'Mixed'
        elif breadth_ratio > 55:
            # Even if more advancers, if decliners are much stronger, it's mixed or negative
            if move_strength_ratio < 0.8:
                return 'Mixed'
            return 'Positive'
        else:
            return 'Mixed'
    
    def suggest_trading_strategy(self, trend_info, power_info, insights, stocks):
        """Suggest trading strategies based on market conditions"""
        trend = trend_info['trend']
        avg_change = trend_info['avg_change']
        breadth_ratio = insights['breadth_ratio']
        volatility = insights['avg_volatility']
        bull_power = power_info['bull_power']
        bear_power = power_info['bear_power']
        net_power = power_info['net_power']
        
        strategies = []
        risk_level = 'Medium'
        market_phase = 'Consolidation'
        
        if volatility > 2.0:
            volatility_level = 'High'
            risk_level = 'High'
        elif volatility > 1.0:
            volatility_level = 'Moderate'
        else:
            volatility_level = 'Low'
        
        # Trend-based strategy
        if trend in ['Strong Bullish', 'Bullish'] and breadth_ratio > 60:
            market_phase = 'Strong Uptrend'
            strategies.append({
                'method': 'Momentum Trading',
                'description': 'Buy on dips in strong stocks. Look for breakouts above resistance.',
                'stocks': 'Focus on strong gainers with high volume',
                'risk': 'Medium',
                'timeframe': 'Intraday to Short-term'
            })
            risk_level = 'Medium-High'
            
        elif trend in ['Strong Bearish', 'Bearish'] and breadth_ratio < 40:
            market_phase = 'Strong Downtrend'
            strategies.append({
                'method': 'Short Selling / Put Options',
                'description': 'Consider shorting weak stocks or buying put options.',
                'stocks': 'Focus on major losers with high weight',
                'risk': 'High',
                'timeframe': 'Intraday to Short-term'
            })
            risk_level = 'High'
        
        # Volatility-based strategy
        if volatility > 2.0:
            strategies.append({
                'method': 'Straddle/Strangle Options',
                'description': 'High volatility suggests big moves. Use non-directional strategies.',
                'stocks': 'Nifty index options or high beta stocks',
                'risk': 'High',
                'timeframe': 'Intraday to Short-term'
            })
        elif volatility < 0.8:
            strategies.append({
                'method': 'Range Trading',
                'description': 'Low volatility market. Trade between support and resistance.',
                'stocks': 'Stocks in clear trading ranges',
                'risk': 'Low-Medium',
                'timeframe': 'Short to Medium-term'
            })
        
        # Market breadth-based
        if 45 <= breadth_ratio <= 55 and abs(avg_change) < 0.5:
            market_phase = 'Consolidation'
            strategies.append({
                'method': 'Wait and Watch',
                'description': 'Market is indecisive. Wait for clear breakout or breakdown.',
                'stocks': 'Keep watchlist ready, avoid aggressive positions',
                'risk': 'Low',
                'timeframe': 'Patience required'
            })
        
        # Power differential strategy
        if abs(net_power) > 20:
            if net_power > 0:
                strategies.append({
                    'method': 'Buy the Leaders',
                    'description': 'Strong bull power indicates institutional buying. Follow the leaders.',
                    'stocks': 'High weighted stocks with positive impact',
                    'risk': 'Medium',
                    'timeframe': 'Short to Medium-term'
                })
            else:
                strategies.append({
                    'method': 'Defensive Positioning',
                    'description': 'Strong bear power suggests distribution. Reduce exposure or hedge.',
                    'stocks': 'Defensive sectors or hedging instruments',
                    'risk': 'Low',
                    'timeframe': 'Immediate'
                })
        
        warnings = []
        if volatility > 2.5:
            warnings.append('⚠️ Extreme volatility detected. Use strict stop losses.')
        if breadth_ratio < 30 or breadth_ratio > 70:
            warnings.append('⚠️ Extreme market breadth. Potential reversal ahead.')
        if abs(net_power) > 30:
            warnings.append('⚠️ One-sided market. Watch for exhaustion signals.')
        
        recommendations = []
        if volatility > 1.5:
            recommendations.append('Use smaller position sizes due to high volatility')
            recommendations.append('Keep stop losses tighter than usual')
        
        if trend in ['Strong Bullish', 'Strong Bearish']:
            recommendations.append('Trend is strong - avoid counter-trend trades')
            recommendations.append('Trail your stop losses to protect profits')
        
        if breadth_ratio > 65:
            recommendations.append('Market is overbought - watch for profit booking')
        elif breadth_ratio < 35:
            recommendations.append('Market is oversold - potential bounce ahead')
        
        return {
            'market_phase': market_phase,
            'volatility_level': volatility_level,
            'risk_level': risk_level,
            'strategies': strategies[:4],
            'warnings': warnings,
            'recommendations': recommendations
        }
    
    def analyze(self):
        """Main analysis function"""
        raw_data = self.fetch_nifty_data()
        
        if not raw_data or 'data' not in raw_data:
            return {'error': 'Failed to fetch data'}
        
        stocks = [s for s in raw_data['data'] 
                 if s.get('symbol') and s.get('lastPrice') 
                 and s.get('symbol') not in ['NIFTY 50', 'NIFTY50', 'Nifty 50']]
        
        stocks_with_weight = self.calculate_weightage(stocks)
        trend_info = self.identify_market_trend(stocks_with_weight)
        power_info = self.calculate_bull_bear_power(stocks_with_weight)
        major_movers = self.identify_major_movers(stocks_with_weight)
        insights = self.calculate_market_insights(stocks_with_weight)
        
        # Get ALL gainers and losers, sorted by percentage change
        gainers = sorted([s for s in stocks_with_weight if s['pChange'] > 0], 
                        key=lambda x: x['pChange'], reverse=True)
        losers = sorted([s for s in stocks_with_weight if s['pChange'] < 0], 
                       key=lambda x: x['pChange'])
        
        trading_suggestions = self.suggest_trading_strategy(trend_info, power_info, insights, stocks_with_weight)
        
        return {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'trend': trend_info,
            'power': power_info,
            'insights': insights,
            'trading_suggestions': trading_suggestions,
            'top_stocks': stocks_with_weight,
            'major_movers': major_movers,
            'gainers': gainers,
            'losers': losers
        }


# Initialize analyzers
stock_analyzer = NiftyStockAnalyzer()

# In-memory cache for the latest successful analysis result
_latest_analysis_result = None
_latest_analysis_lock = threading.Lock()

# In-memory cache for the latest stock analysis result
_latest_stocks_result = None
_latest_stocks_lock = threading.Lock()


def _run_option_analysis():
    """Fetch + analyze options. Returns the result dict or raises."""
    global expiry, _latest_stocks_result
    data = fetch_nifty_option_chain(expiry)
    analyzer = NiftyTrendAnalyzer(data)
    result = analyzer.generate_composite_signal()

    stock_result = stock_analyzer.analyze()
    with _latest_stocks_lock:
        _latest_stocks_result = stock_result
    stock_trend = stock_result.get('trend', {})

    trend_data = {
        'timestamp': datetime.now().isoformat(),
        'nifty_value': result.get('underlying_value'),
        'pcr_oi': result.get('overall_pcr'),
        'pcr_volume': result.get('overall_pcr_volume'),
        'sentiment': result.get('final_signal', 'NEUTRAL').lower(),
        'iv_rank': result.get('iv_analysis', {}).get('iv_rank') if isinstance(result.get('iv_analysis'), dict) else None,
        'call_oi': result.get('total_call_oi'),
        'put_oi': result.get('total_put_oi'),
        'market_trend': stock_trend.get('trend', 'NEUTRAL'),
        'advancers': stock_trend.get('advancers', 0),
        'decliners': stock_trend.get('decliners', 0),
        'avg_change': stock_trend.get('avg_change', 0),
        'primary_signal': result.get('final_signal', 'NEUTRAL'),
        'confidence': result.get('confidence', 0),
        'action': result.get('action', '-'),
        'oi_buildup_signal': result.get('oi_buildup_analysis', {}).get('signal', 'NEUTRAL'),
        'call_writing': result.get('oi_buildup_analysis', {}).get('call_writing', 0),
        'put_writing': result.get('oi_buildup_analysis', {}).get('put_writing', 0)
    }
    trend_storage.write_trend(trend_data)

    pcr_timeframe_changes = trend_storage.get_pcr_changes_multiple_timeframes()
    result['pcr_timeframe_changes'] = pcr_timeframe_changes
    return result


def transmit_option_analysis():
    """Threaded function to continuously analyze options and emit data"""
    global _latest_analysis_result
    while True:
        try:
            result = _run_option_analysis()
            with _latest_analysis_lock:
                _latest_analysis_result = result
            socketio.emit('analysis_data', result)
            print("Emitted option analysis data and wrote trend with market data")
        except Exception as e:
            print(f"Error in option analysis: {e}")
            socketio.emit('error', {'message': str(e)})
        time.sleep(15)


# Routes
@app.route('/')
def index():
    """Serve the main HTML page"""
    from flask import make_response
    resp = make_response(render_template('dashboard.html'))
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp


@app.route('/api/analyze-stocks')
def api_analyze_stocks():
    """API endpoint for stock analysis"""
    result = stock_analyzer.analyze()
    return jsonify(result)


@app.route('/api/analyze-options')
def api_analyze_options():
    """API endpoint for options analysis — returns cached result if available."""
    global _latest_analysis_result
    # 1. Return cached result instantly (avoids duplicate NSE call racing with background thread)
    with _latest_analysis_lock:
        cached = _latest_analysis_result
    if cached is not None:
        return jsonify(cached)
    # 2. No cache yet — do a fresh fetch (only happens on first call before thread fires)
    try:
        result = _run_option_analysis()
        with _latest_analysis_lock:
            _latest_analysis_result = result
        return jsonify(result)
    except Exception as e:
        print(f"api_analyze_options error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/pcr-by-expiry')
def api_pcr_by_expiry():
        """Return PCR summary for all available expiries for NIFTY.
        Each item: { expiry: str, overall_pcr: float, pcr_plusminus_5: float }
        """
        try:
            expiries = fetch_available_expiries('NIFTY')
            out = []
            for exp in expiries:
                try:
                    chain = fetch_nifty_option_chain(exp)
                    records = chain.get('records', {})
                    rows = records.get('data', [])
                    spot_raw = records.get('underlyingValue') or records.get('underlying_value') or 0
                    try:
                        spot = float(str(spot_raw).replace(',', ''))
                    except Exception:
                        spot = 0

                    # collect unique strikes
                    strikes = sorted(list({ r.get('strikePrice') for r in rows if r.get('strikePrice') is not None }))
                    # overall PCR
                    total_call_oi = 0
                    total_put_oi = 0
                    for r in rows:
                        ce = r.get('CE', {})
                        pe = r.get('PE', {})
                        total_call_oi += ce.get('openInterest', 0)
                        total_put_oi += pe.get('openInterest', 0)
                    overall_pcr = round((total_put_oi / total_call_oi), 3) if total_call_oi else None

                    # find nearest strike to spot and compute +/-5 strikes window
                    pcr_window = None
                    if strikes and spot:
                        nearest = min(strikes, key=lambda s: abs(s - spot))
                        idx = strikes.index(nearest)
                        low = max(0, idx - 5)
                        high = min(len(strikes) - 1, idx + 5)
                        selected = set(strikes[low:high+1])
                        sel_call = 0
                        sel_put = 0
                        for r in rows:
                            if r.get('strikePrice') in selected:
                                sel_call += r.get('CE', {}).get('openInterest', 0)
                                sel_put += r.get('PE', {}).get('openInterest', 0)
                        pcr_window = round((sel_put / sel_call), 3) if sel_call else None

                    out.append({ 'expiry': exp, 'overall_pcr': overall_pcr, 'pcr_plusminus_5': pcr_window })
                except Exception as e:
                    print(f"Error fetching/processing expiry {exp}: {e}")
                    out.append({ 'expiry': exp, 'overall_pcr': None, 'pcr_plusminus_5': None })

            return jsonify(out)
        except Exception as e:
            return jsonify({'error': str(e)}), 500


@app.route('/api/strategy')
def api_strategy():
    """Compute and return strategy recommendation from cached analysis data."""
    from strategy import compute_strategy

    with _latest_analysis_lock:
        analysis = _latest_analysis_result
    if analysis is None:
        return jsonify({'error': 'No analysis data available yet — please wait for background thread.'}), 503

    with _latest_stocks_lock:
        stocks = _latest_stocks_result
    mkt_trend = ''
    breadth = 50.0
    if stocks:
        mkt_trend = (stocks.get('trend') or {}).get('trend') or ''
        breadth = float((stocks.get('insights') or {}).get('breadth_ratio') or 50)

    # Derive PCR trend from last 2 stored trend entries
    pcr_trend = 'stable'
    try:
        recent = trend_storage.read_recent_trends(2)
        if len(recent) >= 2:
            p0 = float(recent[0].get('pcr_oi') or 0)
            p1 = float(recent[1].get('pcr_oi') or 0)
            if p0 > p1:
                pcr_trend = 'rising'
            elif p0 < p1:
                pcr_trend = 'falling'
    except Exception:
        pass

    try:
        result = compute_strategy(analysis, mkt_trend=mkt_trend, breadth=breadth, pcr_trend=pcr_trend)
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/get-trends')
def api_get_trends():
    """API endpoint to get trend data"""
    try:
        # Get expiry from query parameter, use global if not provided
        request_expiry = request.args.get('expiry', expiry)
        print(f"[DEBUG] Getting trends for expiry: {request_expiry}")
        
        # Create temporary storage instance for requested expiry if different
        if request_expiry != expiry:
            print(f"[DEBUG] Creating temporary storage for: {request_expiry}")
            temp_storage = TrendStorage(expiry=request_expiry)
            recent_trends = temp_storage.read_recent_trends(250)
            statistics = temp_storage.get_trend_statistics()
        else:
            print(f"[DEBUG] Using global trend storage")
            recent_trends = trend_storage.read_recent_trends(250)
            statistics = trend_storage.get_trend_statistics()
        
        print(f"[DEBUG] Retrieved {len(recent_trends)} trends")
        print(f"[DEBUG] Statistics keys: {statistics.keys()}")
        
        response = {
            'recent_trends': recent_trends,
            'statistics': statistics,
            'expiry': request_expiry
        }
        print(f"[DEBUG] Base response prepared, attempting to fetch India VIX")
        # Try to include India VIX in statistics (best-effort)
        try:
            vix_val = fetch_india_vix()
            if vix_val is not None:
                # attach to statistics for client use
                response['statistics']['vix'] = vix_val
                print( f"[DEBUG] Included India VIX in response: {vix_val}")
        except Exception as e:
            print(f"[WARN] Could not fetch India VIX: {e}")
        print(f"[DEBUG] Response ready, returning success")
        return jsonify(response)
    except Exception as e:
        import traceback
        print(f"[ERROR] Error getting trends: {e}")
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'error_type': type(e).__name__,
            'recent_trends': [],
            'statistics': {
                'total_trends': 0,
                'pcr_analysis': {'pcr_trend': f'Error: {str(e)}'}
            }
        }), 500


@app.route('/api/write-trend', methods=['POST'])
def api_write_trend():
    """API endpoint to write a new trend"""
    try:
        data = request.json
        success = trend_storage.write_trend(data)
        return jsonify({
            'success': success,
            'message': 'Trend recorded successfully' if success else 'Failed to record trend'
        })
    except Exception as e:
        print(f"[ERROR] Error writing trend: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/get-guide')
def api_get_guide():
    """API endpoint to serve the TRENDS_GUIDE.md file"""
    try:
        with open('TRENDS_GUIDE.md', 'r', encoding='utf-8') as f:
            guide_content = f.read()
        return jsonify({
            'success': True,
            'content': guide_content
        })
    except Exception as e:
        print(f"[ERROR] Error reading guide: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    emit('status', {'msg': 'Connected to Nifty Trend Analyzer'})
    emit('current_expiry', {'expiry': expiry})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')


@socketio.on('change_expiry')
def handle_change_expiry(data):
    """Handle expiry change"""
    global expiry, trend_storage
    expiry = data['expiry']
    # Reinitialize trend_storage with new expiry
    trend_storage = TrendStorage(expiry=expiry)
    print(f"Expiry changed to {expiry}, trend storage reinitialized")
    emit('expiry_changed', {'expiry': expiry}, broadcast=True)


if __name__ == '__main__':
    # Start the options analysis thread
    threading.Thread(target=transmit_option_analysis, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
