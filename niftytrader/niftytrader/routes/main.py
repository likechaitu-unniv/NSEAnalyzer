"""
Main Routes
Home page and general routes
"""

from flask import Blueprint, render_template, jsonify

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@main_bp.route('/home')
def home():
    """Home page"""
    return render_template('pages/home.html')


@main_bp.route('/about')
def about():
    """About page"""
    return render_template('pages/about.html')


@main_bp.route('/api/health')
def health_check():
    """API health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'NiftyTrader Dashboard',
        'version': '1.0.0'
    })


@main_bp.route('/api/stats')
def get_stats():
    """Get application statistics"""
    from datetime import datetime
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'market': 'NSE',
        'index': 'NIFTY 50',
        'status': 'operational'
    })
