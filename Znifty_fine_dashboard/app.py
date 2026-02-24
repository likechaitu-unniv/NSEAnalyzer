from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import requests
from datetime import datetime
import math
import json

print("[DEBUG] app.py module loaded")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")
print("[DEBUG] Flask app and SocketIO initialized")

class NiftyAnalyzer:
    """Business logic for analyzing Nifty 50 stock data"""
    
    def __init__(self):
        print("[DEBUG] Initializing NiftyAnalyzer")
        self.api_url = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        print("[DEBUG] NiftyAnalyzer ready")
    
    def fetch_nifty_data(self):
        """Fetch data from NSE API"""
        try:
            response = requests.get(self.api_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching data: {e}")
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
        """Identify market trend based on stock changes"""
        advancers = [s for s in stocks if s['pChange'] > 0]
        decliners = [s for s in stocks if s['pChange'] < 0]
        
        avg_change = sum(s['pChange'] for s in stocks) / len(stocks) if stocks else 0
        
        trend = 'Neutral'
        if avg_change > 0.5 and len(advancers) > len(decliners) * 1.5:
            trend = 'Strong Bullish'
        elif avg_change > 0 and len(advancers) > len(decliners):
            trend = 'Bullish'
        elif avg_change < -0.5 and len(decliners) > len(advancers) * 1.5:
            trend = 'Strong Bearish'
        elif avg_change < 0 and len(decliners) > len(advancers):
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
        # Stocks with significant change (>1%) and high weight
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
        
        # Volume analysis
        total_volume = sum(s.get('totalTradedVolume', 0) for s in stocks)
        high_volume_stocks = sorted(stocks, key=lambda x: x.get('totalTradedVolume', 0), reverse=True)[:5]
        
        # Price momentum
        avg_positive_change = sum(s['pChange'] for s in stocks if s['pChange'] > 0) / max(len([s for s in stocks if s['pChange'] > 0]), 1)
        avg_negative_change = sum(s['pChange'] for s in stocks if s['pChange'] < 0) / max(len([s for s in stocks if s['pChange'] < 0]), 1)
        
        # Market breadth
        breadth_ratio = len([s for s in stocks if s['pChange'] > 0]) / total_stocks * 100 if total_stocks > 0 else 0
        
        # Volatility indicator
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
            'market_sentiment': 'Positive' if breadth_ratio > 55 else 'Negative' if breadth_ratio < 45 else 'Mixed'
        }
    
    def suggest_trading_strategy(self, trend_info, power_info, insights, stocks):
        """Suggest trading strategies based on market conditions"""
        
        # Extract key metrics
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
        
        # Determine volatility level
        if volatility > 2.0:
            volatility_level = 'High'
            risk_level = 'High'
        elif volatility > 1.0:
            volatility_level = 'Moderate'
        else:
            volatility_level = 'Low'
        
        # Strategy 1: Trend-based strategy
        if trend in ['Strong Bullish', 'Bullish'] and breadth_ratio > 60:
            market_phase = 'Strong Uptrend'
            strategies.append({
                'method': 'Momentum Trading',
                'description': 'Buy on dips in strong stocks. Look for breakouts above resistance.',
                'stocks': 'Focus on strong gainers with high volume',
                'risk': 'Medium',
                'timeframe': 'Intraday to Short-term'
            })
            strategies.append({
                'method': 'Call Options (Bullish)',
                'description': 'Buy ATM or slightly OTM call options on Nifty or strong stocks.',
                'stocks': 'Index options or high-weighted stocks',
                'risk': 'Medium-High',
                'timeframe': 'Intraday to Weekly'
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
            strategies.append({
                'method': 'Inverse ETF / Bear Spread',
                'description': 'Use inverse positions or bear put spreads for limited risk.',
                'stocks': 'Nifty index options or inverse ETFs',
                'risk': 'Medium',
                'timeframe': 'Short-term'
            })
            risk_level = 'High'
            
        # Strategy 2: Volatility-based strategy
        if volatility > 2.0:
            strategies.append({
                'method': 'Straddle/Strangle Options',
                'description': 'High volatility suggests big moves. Use non-directional strategies.',
                'stocks': 'Nifty index options or high beta stocks',
                'risk': 'High',
                'timeframe': 'Intraday to Short-term'
            })
            strategies.append({
                'method': 'Scalping',
                'description': 'Quick in-and-out trades capturing small price movements.',
                'stocks': 'High volume liquid stocks',
                'risk': 'Medium',
                'timeframe': 'Intraday (minutes)'
            })
        elif volatility < 0.8:
            strategies.append({
                'method': 'Range Trading',
                'description': 'Low volatility market. Trade between support and resistance.',
                'stocks': 'Stocks in clear trading ranges',
                'risk': 'Low-Medium',
                'timeframe': 'Short to Medium-term'
            })
            strategies.append({
                'method': 'Iron Condor / Theta Strategies',
                'description': 'Sell premium in low volatility environment.',
                'stocks': 'Index options with tight ranges',
                'risk': 'Medium',
                'timeframe': 'Weekly to Monthly'
            })
        
        # Strategy 3: Market breadth-based
        if 45 <= breadth_ratio <= 55 and abs(avg_change) < 0.5:
            market_phase = 'Consolidation'
            strategies.append({
                'method': 'Wait and Watch',
                'description': 'Market is indecisive. Wait for clear breakout or breakdown.',
                'stocks': 'Keep watchlist ready, avoid aggressive positions',
                'risk': 'Low',
                'timeframe': 'Patience required'
            })
            strategies.append({
                'method': 'Sectoral Rotation',
                'description': 'Some sectors may be strong. Focus on relative strength.',
                'stocks': 'Identify sector leaders',
                'risk': 'Medium',
                'timeframe': 'Medium-term'
            })
        
        # Strategy 4: Power differential strategy
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
        
        # Risk warnings
        warnings = []
        if volatility > 2.5:
            warnings.append('⚠️ Extreme volatility detected. Use strict stop losses.')
        if breadth_ratio < 30 or breadth_ratio > 70:
            warnings.append('⚠️ Extreme market breadth. Potential reversal ahead.')
        if abs(net_power) > 30:
            warnings.append('⚠️ One-sided market. Watch for exhaustion signals.')
        
        # General recommendations
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
            'strategies': strategies[:4],  # Limit to top 4 strategies
            'warnings': warnings,
            'recommendations': recommendations
        }
    
    def analyze(self):
        """Main analysis function"""
        raw_data = self.fetch_nifty_data()
        
        if not raw_data or 'data' not in raw_data:
            return {'error': 'Failed to fetch data'}
        
        # Filter valid stocks and exclude NIFTY 50 index itself
        stocks = [s for s in raw_data['data'] 
                 if s.get('symbol') and s.get('lastPrice') 
                 and s.get('symbol') not in ['NIFTY 50', 'NIFTY50', 'Nifty 50']]
        
        # Calculate weightage
        stocks_with_weight = self.calculate_weightage(stocks)
        
        # Market trend analysis
        trend_info = self.identify_market_trend(stocks_with_weight)
        
        # Bull and bear power
        power_info = self.calculate_bull_bear_power(stocks_with_weight)
        
        # Major movers
        major_movers = self.identify_major_movers(stocks_with_weight)
        
        # Market insights
        insights = self.calculate_market_insights(stocks_with_weight)
        
        # Top gainers and losers
        gainers = sorted([s for s in stocks_with_weight if s['pChange'] > 0], 
                        key=lambda x: x['pChange'], reverse=True)[:5]
        losers = sorted([s for s in stocks_with_weight if s['pChange'] < 0], 
                       key=lambda x: x['pChange'])[:5]
        
        # Trading strategy suggestions
        trading_suggestions = self.suggest_trading_strategy(trend_info, power_info, insights, stocks_with_weight)
        
        return {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'trend': trend_info,
            'power': power_info,
            'insights': insights,
            'trading_suggestions': trading_suggestions,
            'top_stocks': stocks_with_weight,  # Return all stocks instead of just top 10
            'major_movers': major_movers,
            'gainers': gainers,
            'losers': losers
        }


class GreeksAnalyzer:
    """Analyze options Greeks and chain data"""
    
    @staticmethod
    def black_scholes_call(S, K, T, r, sigma):
        """Calculate call option price using Black-Scholes"""
        if T <= 0 or sigma <= 0:
            return 0
        d1 = (math.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*math.sqrt(T))
        d2 = d1 - sigma*math.sqrt(T)
        N_d1 = 0.5 * (1 + math.erf(d1/math.sqrt(2)))
        N_d2 = 0.5 * (1 + math.erf(d2/math.sqrt(2)))
        return S*N_d1 - K*math.exp(-r*T)*N_d2
    
    @staticmethod
    def calculate_greeks(S, K, T, r, sigma, option_type='call'):
        """Calculate all Greeks for an option"""
        if T <= 0 or sigma <= 0:
            return {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0}
        
        d1 = (math.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*math.sqrt(T))
        d2 = d1 - sigma*math.sqrt(T)
        
        N_d1 = 0.5 * (1 + math.erf(d1/math.sqrt(2)))
        n_d1 = (1/math.sqrt(2*math.pi)) * math.exp(-0.5*d1**2)
        
        if option_type == 'call':
            delta = N_d1
            theta = (-S * n_d1 * sigma / (2*math.sqrt(T)) - r*K*math.exp(-r*T)*0.5*(1+math.erf(d2/math.sqrt(2)))) / 365
        else:
            delta = N_d1 - 1
            theta = (-S * n_d1 * sigma / (2*math.sqrt(T)) + r*K*math.exp(-r*T)*0.5*(1+math.erf(d2/math.sqrt(2)))) / 365
        
        gamma = n_d1 / (S * sigma * math.sqrt(T))
        vega = S * n_d1 * math.sqrt(T) / 100
        
        return {
            'delta': delta,
            'gamma': gamma,
            'theta': theta,
            'vega': vega
        }
    
    def generate_sample_options_chain(self, spot_price=25000, current_iv=18.5):
        """Generate sample options chain data"""
        strikes = []
        for i in range(-10, 11):
            strike = (spot_price // 100) * 100 + (i * 100)
            moneyness = strike / spot_price
            
            # Adjust IV based on moneyness (volatility smile)
            adjusted_iv = current_iv * (1 + 0.5 * abs(moneyness - 1))
            T = 15 / 365  # 15 days to expiry
            r = 0.06  # Risk-free rate
            
            ce_greeks = self.calculate_greeks(spot_price, strike, T, r, adjusted_iv/100, 'call')
            pe_greeks = self.calculate_greeks(spot_price, strike, T, r, adjusted_iv/100, 'put')
            
            # Generate realistic OI values
            ce_oi = int(1000000 * (1 + 5 * math.exp(-abs(moneyness-1)**2)))
            pe_oi = int(1000000 * (1 + 5 * math.exp(-abs(moneyness-1)**2)))
            
            strikes.append({
                'strike': strike,
                'ce_oi': ce_oi,
                'ce_iv': round(adjusted_iv, 2),
                'ce_ltp': round(self.black_scholes_call(spot_price, strike, T, r, adjusted_iv/100), 2),
                'ce_chg': round((5 - i * 0.3), 2),
                'ce': {
                    'delta': round(ce_greeks['delta'], 4),
                    'gamma': round(ce_greeks['gamma'], 6),
                    'theta': round(ce_greeks['theta'], 4),
                    'vega': round(ce_greeks['vega'], 4),
                    'iv': round(adjusted_iv, 2),
                    'oi': ce_oi
                },
                'pe_chg': round((-5 + i * 0.3), 2),
                'pe_ltp': round(self.black_scholes_call(spot_price, strike, T, r, adjusted_iv/100) - spot_price + strike, 2),
                'pe_iv': round(adjusted_iv, 2),
                'pe_oi': pe_oi,
                'pe': {
                    'delta': round(pe_greeks['delta'], 4),
                    'gamma': round(pe_greeks['gamma'], 6),
                    'theta': round(pe_greeks['theta'], 4),
                    'vega': round(pe_greeks['vega'], 4),
                    'iv': round(adjusted_iv, 2),
                    'oi': pe_oi
                }
            })
        
        return strikes
    
    def analyze_options(self):
        """Generate complete options analysis"""
        spot_price = 25000
        current_iv = 18.5
        expiry_date = "31-Jan-2025"
        time_to_expiry_days = 15
        time_to_expiry_years = time_to_expiry_days / 365
        
        chain = self.generate_sample_options_chain(spot_price, current_iv)
        
        # Calculate PCR
        total_ce_oi = sum(s['ce_oi'] for s in chain)
        total_pe_oi = sum(s['pe_oi'] for s in chain)
        pcr = total_pe_oi / total_ce_oi if total_ce_oi > 0 else 1
        
        # Calculate max pain
        max_pain_strike = int(round(spot_price / 100) * 100)
        
        return {
            'rows': chain,
            'greeks': chain,
            'spot_price': spot_price,
            'pcr_oi': round(pcr, 2),
            'max_pain_strike': max_pain_strike,
            'atm_iv': current_iv,
            'expiry_date': expiry_date,
            'time_to_expiry_years': time_to_expiry_years,
            'time_to_expiry_days': time_to_expiry_days,
            'current_price': spot_price,
            'underlying_value': spot_price,
            'final_signal': 'BULLISH',
            'action': 'BUY',
            'confidence': 75,
            'pcr_analysis': {
                'pcr_oi': round(pcr, 2),
                'signal': 'BULLISH' if pcr > 1.2 else 'BEARISH' if pcr < 0.8 else 'NEUTRAL',
                'interpretation': 'High put interest indicates downside protection'
            },
            'max_pain_analysis': {
                'max_pain_strike': max_pain_strike,
                'signal': 'NEUTRAL',
                'distance': 0
            },
            'oi_buildup_analysis': {
                'call_writing': total_ce_oi,
                'put_writing': total_pe_oi,
                'signal': 'BEARISH' if total_pe_oi > total_ce_oi else 'BULLISH',
                'ce_buildup_type': 'STRONG' if total_ce_oi > pcr * 1000000 else 'WEAK',
                'pe_buildup_type': 'STRONG' if total_pe_oi > pcr * 1000000 else 'WEAK'
            },
            'pressure_analysis': {
                'net_pressure': total_pe_oi - total_ce_oi,
                'signal': 'BULLISH'
            },
            'iv_analysis': {
                'atm_iv': current_iv,
                'iv_skew': -1.5,
                'avg_ce_iv': current_iv - 0.5,
                'avg_pe_iv': current_iv + 0.5,
                'signal': 'NEUTRAL'
            },
            'support_resistance': {
                'immediate_resistance': int(spot_price * 1.01),
                'immediate_support': int(spot_price * 0.99),
                'all_resistance': [int(spot_price * 1.02), int(spot_price * 1.04)],
                'all_support': [int(spot_price * 0.98), int(spot_price * 0.96)]
            },
            'overall_pcr': round(pcr, 3),
            'overall_pcr_volume': round(pcr, 3),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }


# Initialize analyzer
analyzer = NiftyAnalyzer()
greeks_analyzer = GreeksAnalyzer()

@app.route('/')
def index():
    """Render the main page"""
    return render_template('dashboard.html')

@app.route('/api/analyze')
def api_analyze():
    """API endpoint for analysis"""
    result = analyzer.analyze()
    return jsonify(result)

@app.route('/api/analyze-stocks')
def api_analyze_stocks():
    """API endpoint for stocks analysis"""
    result = analyzer.analyze()
    return jsonify(result)

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    print('Client connected')
    emit('connect', {'data': 'Connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    print('Client disconnected')

@socketio.on('request_analysis')
def handle_request_analysis():
    """Handle request for analysis data"""
    print('Received request_analysis event')
    stocks_data = analyzer.analyze()
    print(f'Got stocks data with keys: {stocks_data.keys()}')
    
    options_data = greeks_analyzer.analyze_options()
    print(f'Got options data with keys: {options_data.keys()}')
    print(f'Options data has greeks: {len(options_data.get("greeks", []))} items')
    
    # Check first greek item
    if options_data.get('greeks'):
        first_greek = options_data['greeks'][0]
        print(f'First greek item keys: {first_greek.keys()}')
        print(f'First greek CE: {first_greek.get("ce")}')
        print(f'First greek PE: {first_greek.get("pe")}')
    
    # Merge stocks and options data
    combined_data = {
        **stocks_data,
        'greeks_analysis': options_data,
        'final_signal': options_data['final_signal'],
        'action': options_data['action'],
        'confidence': options_data['confidence'],
        'pcr_analysis': options_data['pcr_analysis'],
        'max_pain_analysis': options_data['max_pain_analysis'],
        'oi_buildup_analysis': options_data['oi_buildup_analysis'],
        'pressure_analysis': options_data['pressure_analysis'],
        'iv_analysis': options_data['iv_analysis'],
        'support_resistance': options_data['support_resistance'],
        'overall_pcr': options_data['overall_pcr'],
        'overall_pcr_volume': options_data['overall_pcr_volume'],
        'timestamp': options_data['timestamp'],
        'rows': options_data['rows'],
    }
    
    print(f'Emitting analysis_data with greeks_analysis containing {len(combined_data["greeks_analysis"]["greeks"])} items')
    emit('analysis_data', combined_data)

@socketio.on('change_expiry')
def handle_change_expiry(data):
    """Handle expiry date change"""
    expiry = data.get('expiry')
    print(f'Expiry changed to: {expiry}')
    emit('current_expiry', {'expiry': expiry}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='127.0.0.1', port=5001)