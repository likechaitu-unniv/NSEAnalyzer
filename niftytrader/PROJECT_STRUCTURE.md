# NiftyTrader Project Structure Overview

## 📁 Complete Directory Tree

```
NSEAnalyzer/
└── niftytrader/
    ├── niftytrader/                           # Main Application Package
    │   ├── __init__.py                       # Flask App Factory
    │   ├── models/                           # Data Models & Business Logic
    │   │   ├── __init__.py
    │   │   └── analyzer.py                  # Stock Analysis
    │   ├── routes/                           # Flask Blueprints (Multi-Page Routes)
    │   │   ├── __init__.py
    │   │   ├── main.py                      # Home, About, Health Check
    │   │   ├── dashboard.py                 # Stock Dashboard Pages
    │   │   ├── trends.py                    # Trend Analysis Pages
    │   │   └── guide.py                     # Help & Guide Pages
    │   ├── static/                           # Static Assets
    │   │   ├── css/                         # Stylesheets
    │   │   │   ├── style.css               # Main styles
    │   │   │   ├── home.css                # Home page styles
    │   │   │   ├── dashboard.css           # Dashboard styles
    │   │   │   ├── trends.css              # Trends page styles
    │   │   │   └── guide.css               # Guide page styles
    │   │   └── js/                         # JavaScript Files
    │   │       ├── main.js                 # Core app utilities
    │   │       ├── home.js                 # Home page logic
    │   │       ├── dashboard.js            # Dashboard interactions
    │   │       ├── trends.js               # Trends logic
    │   │       └── guide.js                # Guide navigation
    │   ├── templates/                        # HTML Templates
    │   │   ├── base.html                   # Master (Base) Template
    │   │   ├── pages/                      # Page Templates
    │   │   │   ├── home.html               # Home page
    │   │   │   ├── about.html              # About page
    │   │   │   ├── dashboard.html          # Dashboard page
    │   │   │   ├── trends.html             # Trends analysis page
    │   │   │   └── guide.html              # Guide/Help page
    │   │   └── errors/                     # Error Pages
    │   │       ├── 404.html                # Not Found
    │   │       └── 500.html                # Server Error
    │   ├── utils/                            # Utility Functions
    │   │   └── __init__.py
    │   └── data/                             # Data Storage Directory
    │       └── .gitkeep
    ├── run.py                                # Application Entry Point
    ├── config.py                             # Configuration Management
    ├── requirements.txt                      # Python Dependencies
    ├── .env.example                          # Environment Template
    ├── .gitignore                            # Git Ignore Rules
    └── README.md                             # Project Documentation
```

## 📄 Key Files Description

### Core Files
- **run.py** - Application entry point, starts Flask server
- **config.py** - Configuration for dev/prod environments
- **requirements.txt** - Python package dependencies

### Application Package (niftytrader/)

#### Flask App Factory (__init__.py)
- Creates Flask application
- Initializes extensions (SocketIO)
- Registers blueprints
- Sets up error handlers

#### Models (models/)
- **analyzer.py** - Business logic for stock analysis
  - `StockAnalyzer` class for data processing
  - Methods for trend analysis, weightage calculation

#### Routes (routes/)
Multi-page Flask blueprints:

1. **main.py** - General routes
   - GET `/` - Home page
   - GET `/about` - About page
   - GET `/api/health` - Health check
   - GET `/api/stats` - Statistics

2. **dashboard.py** - Stock dashboard
   - GET `/dashboard` - Dashboard page
   - GET `/dashboard/api/stocks` - All stocks
   - GET `/dashboard/api/trend` - Market trend
   - GET `/dashboard/api/movers` - Top movers
   - GET `/dashboard/api/summary` - Summary

3. **trends.py** - Trend analysis
   - GET `/trends` - Trends page
   - GET `/trends/api/analysis` - Analysis data
   - GET `/trends/api/history` - Historical data
   - GET `/trends/api/expiry` - Expiry info

4. **guide.py** - Help & documentation
   - GET `/guide` - Guide main page
   - GET `/guide/api/content` - Guide content
   - GET `/guide/api/faq` - FAQ section
   - GET `/guide/api/glossary` - Trading terms

#### Static Files (static/)

**CSS (css/)**
- `style.css` - Global styles (1100+ lines)
  - Navigation, buttons, cards, tables
  - Responsive design, utilities
- `home.css` - Home page specific styles
- `dashboard.css` - Dashboard styles
- `trends.css` - Trends page styles
- `guide.css` - Guide page styles

**JavaScript (js/)**
- `main.js` - Core utilities
  - Number formatting, color helpers, time display
- `home.js` - Home page features
- `dashboard.js` - Dashboard functionality
  - Data loading, table updates, search/sort
- `trends.js` - Trends page features
- `guide.js` - Guide navigation

#### Templates (templates/)

**Base Template**
- `base.html` - Master template
  - Navigation bar
  - Main content area
  - Footer
  - Script/CSS includes

**Page Templates** (pages/)
- `home.html` - Home page (hero, features, stats)
- `about.html` - About page (info, features, disclaimer)
- `dashboard.html` - Stock dashboard (market overview, movers, stock list)
- `trends.html` - Trends analysis (analysis summary, tabs, history)
- `guide.html` - Help guide (sidebar nav, sections, glossary, FAQ)

**Error Templates** (errors/)
- `404.html` - Not Found page
- `500.html` - Server Error page

## 🔄 Multi-Page Application Flow

```
Browser Request
    ↓
Nginx/Apache (optional)
    ↓
Flask App (run.py)
    ↓
Route Dispatcher
    ├── Main Blueprint
    │   ├── / → home page
    │   ├── /about → about page
    │   └── /api/* → API endpoints
    │
    ├── Dashboard Blueprint (/dashboard)
    │   ├── / → dashboard page
    │   └── /api/* → stock data API
    │
    ├── Trends Blueprint (/trends)
    │   ├── / → trends page
    │   └── /api/* → analysis API
    │
    └── Guide Blueprint (/guide)
        ├── / → guide page
        └── /api/* → content API
    ↓
Template Renderer (Jinja2)
    ↓
HTML Response
    ↓
Browser Rendering
    ↓
JavaScript Execution (dynamic features)
```

## 🚀 Running the Application

### Development
```bash
cd niftytrader
pip install -r requirements.txt
python run.py
```
Access: `http://localhost:5000`

### Production
```bash
gunicorn --workers 4 --threads 2 run:app
```

## 📊 Technology Stack

**Backend**
- Flask 2.3.3 - Web framework
- Flask-SocketIO 5.3.4 - Real-time communication
- Python 3.8+ - Programming language

**Frontend**
- HTML5 - Markup
- CSS3 - Styling
- Vanilla JavaScript - Interactions

**Data**
- Pandas - Data analysis
- NumPy - Numerical computing
- SciPy - Scientific computing
- Requests - HTTP client

**Deployment** (Optional)
- Gunicorn - WSGI server
- Gevent - Async framework

## 🎯 Application Pages

### 1. Home Page (/)
- Hero section with CTA
- Feature overview
- Quick market stats
- Links to main sections

### 2. Dashboard (/dashboard)
- **Market Overview**: Trend, change, advancers/decliners, bull/bear power
- **Major Movers**: Top 5 impactful stocks
- **Stock List**: All Nifty 50 with search/sort

### 3. Trends (/trends)
- **Analysis Summary**: Signal, PCR, support, resistance
- **Tabs**: Open Interest, PCR Analysis, Chart
- **History**: Historical trend data

### 4. Guide (/guide)
- **Sidebar Navigation**: Quick access to sections
- **Content Sections**: Getting started, dashboard, trends
- **Glossary**: Trading terms
- **FAQ**: Common questions

### 5. About (/about)
- Project information
- Feature list
- Technology stack
- Disclaimer

## ✅ Checklist

- ✅ Project structure created
- ✅ Flask app factory implemented
- ✅ Four main blueprints (pages)
- ✅ 5 page templates + error pages
- ✅ 5 CSS stylesheets
- ✅ 5 JavaScript files
- ✅ Stock analyzer model
- ✅ API endpoints
- ✅ Configuration management
- ✅ Environment setup
- ✅ Complete documentation

## 🔗 Navigation Map

```
Home (/)
├── Dashboard (/dashboard)
├── Trends (/trends)
├── Guide (/guide)
│   ├── Getting Started
│   ├── Dashboard Guide
│   ├── Trends Guide
│   ├── Glossary
│   └── FAQ
└── About (/about)
```

## 📝 Notes

- All routes return both HTML pages and JSON API
- Responsive design (mobile-friendly)
- Search and filtering on dashboard
- Tab-based navigation in trends
- Sidebar navigation in guide
- Real-time data updates possible with SocketIO
- Error handling for 404 and 500 errors

---

**Ready to start!** Run `python run.py` to launch the application.
