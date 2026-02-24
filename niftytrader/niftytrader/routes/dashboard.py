"""
Dashboard Routes
Stock dashboard and analysis
"""

from flask import Blueprint, render_template, jsonify
from niftytrader.models.analyzer import StockAnalyzer

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


@dashboard_bp.route('/')
def index():
    """Dashboard home page"""
    return render_template('pages/dashboard.html')


@dashboard_bp.route('/api/stocks')
def get_stocks():
    """Get all Nifty 50 stocks"""
    try:
        analyzer = StockAnalyzer()
        data = analyzer.fetch_data()
        stocks = data.get('data', [])
        stocks = analyzer.calculate_weightage(stocks)
        return jsonify({'stocks': stocks, 'count': len(stocks)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/api/trend')
def get_trend():
    """Get current market trend"""
    try:
        analyzer = StockAnalyzer()
        data = analyzer.fetch_data()
        stocks = data.get('data', [])
        stocks = analyzer.calculate_weightage(stocks)
        trend = analyzer.identify_trend(stocks)
        return jsonify(trend)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/api/movers')
def get_movers():
    """Get major market movers"""
    try:
        analyzer = StockAnalyzer()
        data = analyzer.fetch_data()
        stocks = data.get('data', [])
        stocks = analyzer.calculate_weightage(stocks)
        movers = analyzer.get_major_movers(stocks, limit=10)
        return jsonify({'movers': movers})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@dashboard_bp.route('/api/summary')
def get_summary():
    """Get dashboard summary"""
    try:
        analyzer = StockAnalyzer()
        data = analyzer.fetch_data()
        stocks = data.get('data', [])
        stocks = analyzer.calculate_weightage(stocks)
        
        trend = analyzer.identify_trend(stocks)
        movers = analyzer.get_major_movers(stocks, limit=5)
        
        return jsonify({
            'trend': trend,
            'movers': movers,
            'total_stocks': len(stocks),
            'top_gainer': movers[0] if movers else None,
            'top_loser': min(stocks, key=lambda x: x['pChange']) if stocks else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
