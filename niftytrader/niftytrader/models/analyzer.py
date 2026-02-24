"""
Stock Market Analyzer
Analyzes Nifty 50 stock data
"""

import requests
import pandas as pd
from typing import Dict, List


class StockAnalyzer:
    """Analyzer for Nifty 50 stock data"""
    
    def __init__(self):
        self.api_url = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
        }
    
    def fetch_data(self) -> Dict:
        """Fetch Nifty 50 data from NSE API"""
        try:
            response = requests.get(self.api_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching NSE data: {e}")
            return self.get_sample_data()
    
    @staticmethod
    def get_sample_data() -> Dict:
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
            ]
        }
    
    @staticmethod
    def calculate_weightage(stocks: List[Dict]) -> List[Dict]:
        """Calculate stock weightage in index"""
        total_value = sum(stock['lastPrice'] * stock.get('totalTradedVolume', 1) for stock in stocks)
        
        for stock in stocks:
            market_value = stock['lastPrice'] * stock.get('totalTradedVolume', 1)
            stock['weight'] = (market_value / total_value * 100) if total_value > 0 else 0
            stock['impact'] = (stock['weight'] * stock['pChange']) / 100
        
        return sorted(stocks, key=lambda x: x['weight'], reverse=True)
    
    @staticmethod
    def identify_trend(stocks: List[Dict]) -> Dict:
        """Identify market trend"""
        advancers = [s for s in stocks if s['pChange'] > 0]
        decliners = [s for s in stocks if s['pChange'] < 0]
        
        avg_change = sum(s['pChange'] for s in stocks) / len(stocks) if stocks else 0
        
        bull_power = sum(s.get('weight', 0) * s['pChange'] for s in advancers) if advancers else 0
        bear_power = sum(s.get('weight', 0) * abs(s['pChange']) for s in decliners) if decliners else 0
        net_power = bull_power - bear_power
        
        if net_power > 15 and len(advancers) > len(decliners):
            trend = 'Strong Bullish'
        elif net_power > 0 and len(advancers) > len(decliners):
            trend = 'Bullish'
        elif net_power < -15 and len(decliners) > len(advancers):
            trend = 'Strong Bearish'
        elif net_power < 0 and len(decliners) > len(advancers):
            trend = 'Bearish'
        else:
            trend = 'Neutral'
        
        return {
            'trend': trend,
            'avg_change': round(avg_change, 2),
            'advancers': len(advancers),
            'decliners': len(decliners),
            'bull_power': round(bull_power, 2),
            'bear_power': round(bear_power, 2)
        }
    
    @staticmethod
    def get_major_movers(stocks: List[Dict], limit: int = 5) -> List[Dict]:
        """Get top moving stocks"""
        movers = [s for s in stocks if abs(s['pChange']) > 1]
        return sorted(movers, key=lambda x: abs(x['impact']), reverse=True)[:limit]
