"""
Trends Routes
Market trend analysis
"""

from flask import Blueprint, render_template, jsonify, request

trends_bp = Blueprint('trends', __name__, url_prefix='/trends')


@trends_bp.route('/')
def index():
    """Trends analysis page"""
    return render_template('pages/trends.html')


@trends_bp.route('/api/analysis')
def get_analysis():
    """Get trend analysis"""
    try:
        # This would typically use Analyzer.py from parent directory
        analysis_data = {
            'signal': 'Bullish',
            'pcr': 0.95,
            'support': 24500,
            'resistance': 25200,
            'timestamp': __import__('datetime').datetime.now().isoformat()
        }
        return jsonify(analysis_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@trends_bp.route('/api/oi')
def get_oi_data():
    """Get Open Interest data"""
    try:
        oi_data = [
            {'strike': 24000, 'call_oi': 1500000, 'put_oi': 1200000, 'diff': 300000},
            {'strike': 24500, 'call_oi': 2100000, 'put_oi': 2300000, 'diff': -200000},
            {'strike': 24800, 'call_oi': 3200000, 'put_oi': 2800000, 'diff': 400000},
            {'strike': 25000, 'call_oi': 2800000, 'put_oi': 3100000, 'diff': -300000},
            {'strike': 25500, 'call_oi': 1900000, 'put_oi': 1700000, 'diff': 200000},
        ]
        return jsonify({'oi_data': oi_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@trends_bp.route('/api/history')
def get_history():
    """Get trend history"""
    try:
        history = [
            {'date': '2026-02-22', 'signal': 'Bullish', 'pcr': 0.95, 'price': 24800},
            {'date': '2026-02-21', 'signal': 'Neutral', 'pcr': 0.88, 'price': 24650},
            {'date': '2026-02-20', 'signal': 'Bullish', 'pcr': 0.92, 'price': 24720},
            {'date': '2026-02-19', 'signal': 'Bearish', 'pcr': 1.05, 'price': 24500},
            {'date': '2026-02-18', 'signal': 'Bullish', 'pcr': 0.90, 'price': 24680},
        ]
        return jsonify({'history': history})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@trends_bp.route('/api/expiry', methods=['GET', 'POST'])
def handle_expiry():
    """Manage option expiry dates"""
    if request.method == 'POST':
        data = request.get_json()
        expiry = data.get('expiry')
        return jsonify({'status': 'success', 'expiry': expiry})
    
    return jsonify({
        'current_expiry': '24-Feb-2026',
        'available_expiries': ['17-Feb-2026', '24-Feb-2026', '03-Mar-2026']
    })
