"""
Guide Routes
Help and documentation pages
"""

from flask import Blueprint, render_template, jsonify

guide_bp = Blueprint('guide', __name__, url_prefix='/guide')


@guide_bp.route('/')
def index():
    """Guide home page"""
    return render_template('pages/guide.html')


@guide_bp.route('/api/content')
def get_guide_content():
    """Get guide content"""
    content = {
        'sections': [
            {
                'id': 'dashboard',
                'title': 'Dashboard Overview',
                'content': 'The dashboard displays real-time Nifty 50 stock data with market analysis.'
            },
            {
                'id': 'trends',
                'title': 'Trend Analysis',
                'content': 'Analyze market trends using technical indicators and option data.'
            }
        ]
    }
    return jsonify(content)


@guide_bp.route('/api/faq')
def get_faq():
    """Get FAQ"""
    faqs = {
        'faqs': [
            {
                'question': 'What is Nifty 50?',
                'answer': 'Nifty 50 is a benchmark index of 50 large-cap Indian companies.'
            },
            {
                'question': 'How often is data updated?',
                'answer': 'Data updates in real-time during market hours (9:15 AM - 3:30 PM IST).'
            }
        ]
    }
    return jsonify(faqs)


@guide_bp.route('/api/glossary')
def get_glossary():
    """Get trading glossary"""
    glossary = {
        'terms': {
            'PCR': 'Put-Call Ratio - Sentiment indicator',
            'OI': 'Open Interest - Number of open contracts',
            'IV': 'Implied Volatility - Expected price volatility'
        }
    }
    return jsonify(glossary)
