# NiftyTrader - Advanced Nifty Market Analysis Dashboard

Advanced multi-page Flask application for real-time Nifty 50 market analysis, trend analysis, and trading insights.

## 📋 Project Structure

```
niftytrader/
├── niftytrader/                    # Main application package
│   ├── __init__.py                # App factory
│   ├── models/                    # Data models and analyzers
│   │   ├── analyzer.py           # Stock analysis logic
│   │   └── __init__.py
│   ├── routes/                    # Flask blueprints
│   │   ├── main.py               # Home and general routes
│   │   ├── dashboard.py          # Dashboard routes
│   │   ├── trends.py             # Trends analysis routes
│   │   ├── guide.py              # Help/guide routes
│   │   └── __init__.py
│   ├── static/                    # Static files
│   │   ├── css/                  # Stylesheets
│   │   │   ├── style.css         # Main styles
│   │   │   ├── home.css
│   │   │   ├── dashboard.css
│   │   │   ├── trends.css
│   │   │   └── guide.css
│   │   └── js/                   # JavaScript files
│   │       ├── main.js           # Main app script
│   │       ├── home.js
│   │       ├── dashboard.js
│   │       ├── trends.js
│   │       └── guide.js
│   ├── templates/                 # HTML templates
│   │   ├── base.html             # Master template
│   │   ├── pages/                # Page templates
│   │   │   ├── home.html
│   │   │   ├── about.html
│   │   │   ├── dashboard.html
│   │   │   ├── trends.html
│   │   │   └── guide.html
│   │   └── errors/               # Error pages
│   │       ├── 404.html
│   │       └── 500.html
│   ├── utils/                     # Utility modules
│   └── data/                      # Data storage
├── run.py                         # Application entry point
├── config.py                      # Configuration
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment template
└── README.md                      # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip or conda

### Installation

1. **Clone or download the project**
   ```bash
   cd niftytrader
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env as needed
   ```

4. **Run the application**
   ```bash
   python run.py
   ```

5. **Access the application**
   Open your browser and goto: `http://localhost:5000`

## 📱 Features

### 🏠 Home Page
- Welcome and feature overview
- Quick market statistics
- Links to main sections

### 📊 Dashboard
- Real-time Nifty 50 stock data
- Market overview and trends
- Top moving stocks
- Searchable stock list
- Live price updates

### 📈 Trends Analysis
- Market trend analysis
- Put-Call Ratio (PCR) analysis
- Support and Resistance levels
- Open Interest (OI) data
- Historical trend tracking

### 📚 Guide & Help
- Getting started guide
- Dashboard tutorial
- Trend analysis explanation
- Trading glossary
- FAQ section

## 🔧 Configuration

Edit `config.py` to customize:
- Database settings
- API configurations
- Security settings
- Feature flags

Environment variables in `.env`:
```env
FLASK_ENV=development|production
FLASK_DEBUG=True|False
SECRET_KEY=your-secret-key
DEFAULT_EXPIRY=17-Feb-2026
```

## 🛠️ Development

### Project Architecture

**Backend (Flask)**
- Application factory pattern
- Blueprint-based routing
- Modular structure
- REST API endpoints

**Frontend (HTML/CSS/JS)**
- Responsive design
- Progressive enhancement
- Vanilla JavaScript
- Semantic HTML5

**Data**
- NSE API integration
- Real-time data processing
- Pandas for analysis

### API Endpoints

#### Main Routes
- `GET /` - Home page
- `GET /about` - About page
- `GET /api/health` - Health check

#### Dashboard
- `GET /dashboard` - Dashboard page
- `GET /dashboard/api/stocks` - Get stocks
- `GET /dashboard/api/trend` - Get market trend
- `GET /dashboard/api/movers` - Get top movers
- `GET /dashboard/api/summary` - Get summary

#### Trends
- `GET /trends` - Trends page
- `GET /trends/api/analysis` - Get analysis
- `GET /trends/api/history` - Get history
- `GET /trends/api/expiry` - Get expiry info

#### Guide
- `GET /guide` - Guide page
- `GET /guide/api/content` - Get guide content
- `GET /guide/api/faq` - Get FAQ
- `GET /guide/api/glossary` - Get glossary

## 📦 Dependencies

**Core**
- Flask 2.3.3
- Flask-SocketIO 5.3.4

**Data Processing**
- pandas 2.0.3
- numpy 1.24.3
- scipy 1.11.2

**HTTP Client**
- requests 2.31.0

**Optional (Production)**
- gunicorn 21.2.0
- gevent 23.9.1

## 🔐 Security

**Implemented**
- CORS protection
- Session management
- Error handling
- Input validation

**Recommendations**
- Use HTTPS in production
- Set strong SECRET_KEY
- Validate all user input
- Keep dependencies updated

## 📝 License

This project is for educational purposes.

## ⚠️ Disclaimer

NiftyTrader is provided for educational and informational purposes only. The data and analysis provided are not investment advice. Past performance is not indicative of future results. Always conduct your own research and consult with a licensed financial advisor before making investment decisions.

## 🤝 Contributing

Improvements welcome! Areas for enhancement:
- Advanced charting
- WebSocket real-time updates
- User accounts
- Watchlists
- Alert system
- Historical data analysis

## 📚 Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Flask-SocketIO](https://flask-socketio.readthedocs.io/)
- [NSE India](https://www.nseindia.com/)
- [Pandas Documentation](https://pandas.pydata.org/)

## 🐛 Troubleshooting

**Port already in use**
```bash
python run.py  # Change port in .env or run.py
```

**Import errors**
```bash
pip install -r requirements.txt  # Reinstall dependencies
```

**Data not loading**
- Check internet connection
- Verify NSE API is accessible
- Check browser console for errors

## 📞 Support

For issues and questions, refer to the Guide section in the application or check the FAQ.

---

**Happy Trading!** 📈
