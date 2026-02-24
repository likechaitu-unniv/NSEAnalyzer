"""
Nifty Market Trend Analyzer
Based on Options Chain Data Analysis
"""

import json
from datetime import datetime
import time
from typing import Dict, List, Tuple
import math
import numpy as np
from scipy.stats import norm
from utils import calculate_oi_pcr, derive_and_classify_nifty_option_chain, derive_pcr, fetch_nifty_option_chain, write_to_local

print("[DEBUG] Analyzer.py module loaded")


class OptionGreeks:
    """Calculate option Greeks using Black-Scholes model"""
    
    @staticmethod
    def calculate_greeks(S, K, T, r, sigma, option_type='call'):
        """
        Calculate option Greeks
        S: Current stock price
        K: Strike price
        T: Time to expiration (in years)
        r: Risk-free rate
        sigma: Volatility
        option_type: 'call' or 'put'
        """
        #print(f"[DEBUG] calculate_greeks() called: S={S}, K={K}, T={T}, option_type={option_type}")
        if T <= 0 or sigma <= 0:
        #    print("[DEBUG] Invalid T or sigma, returning zero greeks")
            return {
                'delta': 0, 'gamma': 0, 'theta': 0, 
                'vega': 0, 'rho': 0, 'price': 0
            }
        
        # Calculate d1 and d2
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        # Calculate Greeks
        if option_type.lower() == 'call':
            delta = norm.cdf(d1)
            price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
            rho = K * T * np.exp(-r * T) * norm.cdf(d2) / 100
        else:  # put
            delta = -norm.cdf(-d1)
            price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
            rho = -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100
        
        gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
        theta = (-(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T)) - 
                 r * K * np.exp(-r * T) * norm.cdf(d2 if option_type.lower() == 'call' else -d2))
        theta = theta / 365  # Convert to daily theta
        vega = S * norm.pdf(d1) * np.sqrt(T) / 100  # Divided by 100 for 1% change
        
        return {
            'delta': round(delta, 4),
            'gamma': round(gamma, 6),
            'theta': round(theta, 2),
            'vega': round(vega, 2),
            'rho': round(rho, 2),
            'price': round(price, 2)
        }


class NiftyTrendAnalyzer:
    """Analyzes Nifty options chain data to predict market trend"""
    
    def __init__(self, data):
        """Initialize with JSON data file"""
        self.data = data
        
        self.timestamp = self.data['records']['timestamp']
        self.underlying_value = self.data['records']['underlyingValue']
        self.options_data = self.data['records']['data']
        
    def calculate_pcr(self) -> Dict:
        """
        Put-Call Ratio (PCR) Analysis
        PCR > 1.0: Bullish (more puts, market oversold)
        PCR < 0.7: Bearish (more calls, market overbought)
        0.7 - 1.0: Neutral
        """
        total_put_oi = 0
        total_call_oi = 0
        total_put_volume = 0
        total_call_volume = 0
        
        for entry in self.options_data:
            if entry['CE']['openInterest'] > 0:
                total_call_oi += entry['CE']['openInterest']
                total_call_volume += entry['CE']['totalTradedVolume']
            
            if entry['PE']['openInterest'] > 0:
                total_put_oi += entry['PE']['openInterest']
                total_put_volume += entry['PE']['totalTradedVolume']
        
        pcr_oi = total_put_oi / total_call_oi if total_call_oi > 0 else 0
        pcr_volume = total_put_volume / total_call_volume if total_call_volume > 0 else 0
        
        # Interpretation
        if pcr_oi > 1.2:
            signal = "STRONG BULLISH"
            confidence = min(95, 70 + (pcr_oi - 1.2) * 50)
        elif pcr_oi > 1.0:
            signal = "BULLISH"
            confidence = 60 + (pcr_oi - 1.0) * 50
        elif pcr_oi > 0.7:
            signal = "NEUTRAL"
            confidence = 50
        elif pcr_oi > 0.5:
            signal = "BEARISH"
            confidence = 60 + (0.7 - pcr_oi) * 100
        else:
            signal = "STRONG BEARISH"
            confidence = min(95, 70 + (0.5 - pcr_oi) * 100)
        
        return {
            'pcr_oi': round(pcr_oi, 3),
            'pcr_volume': round(pcr_volume, 3),
            'signal': signal,
            'confidence': round(confidence, 1),
            'interpretation': f"PCR-OI: {round(pcr_oi, 3)} indicates {signal.lower()} sentiment"
        }
    
    def calculate_max_pain(self) -> Dict:
        """
        Max Pain Theory: Strike where option writers lose least money
        Market tends to gravitate towards this level at expiry
        """
        strike_pain = {}
        
        for entry in self.options_data:
            strike = entry['CE']['strikePrice']
            if strike == 0:
                continue
                
            ce_oi = entry['CE']['openInterest']
            pe_oi = entry['PE']['openInterest']
            
            # Calculate pain for all strikes
            total_pain = 0
            for test_entry in self.options_data:
                test_strike = test_entry['CE']['strikePrice']
                if test_strike == 0:
                    continue
                
                test_ce_oi = test_entry['CE']['openInterest']
                test_pe_oi = test_entry['PE']['openInterest']
                
                # Call writers pain (if price > strike)
                if strike > test_strike:
                    total_pain += test_ce_oi * (strike - test_strike)
                
                # Put writers pain (if price < strike)
                if strike < test_strike:
                    total_pain += test_pe_oi * (test_strike - strike)
            
            strike_pain[strike] = total_pain
        
        # Find max pain strike (minimum pain for writers)
        max_pain_strike = min(strike_pain, key=strike_pain.get) if strike_pain else 0
        
        # Determine signal based on current price vs max pain
        distance = self.underlying_value - max_pain_strike
        distance_pct = (distance / max_pain_strike * 100) if max_pain_strike > 0 else 0
        
        if distance_pct > 2:
            signal = "BEARISH"
            interpretation = f"Price {round(distance, 0)} points above Max Pain - likely to correct down"
        elif distance_pct < -2:
            signal = "BULLISH"
            interpretation = f"Price {abs(round(distance, 0))} points below Max Pain - likely to move up"
        else:
            signal = "NEUTRAL"
            interpretation = "Price near Max Pain - balanced"
        
        return {
            'max_pain_strike': max_pain_strike,
            'current_price': self.underlying_value,
            'distance': round(distance, 2),
            'distance_pct': round(distance_pct, 2),
            'signal': signal,
            'interpretation': interpretation
        }
    
    def analyze_oi_buildup(self) -> Dict:
        """
        Open Interest Change Analysis
        Shows where aggressive positioning is happening
        """
        ce_buildup = []
        pe_buildup = []
        
        for entry in self.options_data:
            strike = entry['CE']['strikePrice']
            if strike == 0:
                continue
            
            ce_chg_oi = entry['CE']['changeinOpenInterest']
            pe_chg_oi = entry['PE']['changeinOpenInterest']
            
            if abs(ce_chg_oi) > 1000:  # Significant change
                ce_buildup.append({
                    'strike': strike,
                    'change': ce_chg_oi,
                    'pct_change': entry['CE']['pchangeinOpenInterest']
                })
            
            if abs(pe_chg_oi) > 1000:
                pe_buildup.append({
                    'strike': strike,
                    'change': pe_chg_oi,
                    'pct_change': entry['PE']['pchangeinOpenInterest']
                })
        
        # Sort by absolute change
        ce_buildup.sort(key=lambda x: abs(x['change']), reverse=True)
        pe_buildup.sort(key=lambda x: abs(x['change']), reverse=True)
        
        # Get top resistance and support levels
        call_resistance = [x for x in ce_buildup[:5] if x['change'] > 0 and x['strike'] > self.underlying_value]
        put_support = [x for x in pe_buildup[:5] if x['change'] > 0 and x['strike'] < self.underlying_value]
        
        # Analyze buildup pattern
        ce_total = sum([x['change'] for x in ce_buildup[:10] if x['change'] > 0])
        pe_total = sum([x['change'] for x in pe_buildup[:10] if x['change'] > 0])
        
        if pe_total > ce_total * 1.5:
            signal = "BULLISH"
            interpretation = "Heavy PUT writing indicates bullish sentiment"
        elif ce_total > pe_total * 1.5:
            signal = "BEARISH"
            interpretation = "Heavy CALL writing indicates bearish sentiment"
        else:
            signal = "NEUTRAL"
            interpretation = "Balanced buildup in both CE and PE"
        
        return {
            'signal': signal,
            'interpretation': interpretation,
            'call_writing': ce_total,
            'put_writing': pe_total,
            'key_resistance': call_resistance[:3],
            'key_support': put_support[:3]
        }
    
    def analyze_implied_volatility(self) -> Dict:
        """
        Implied Volatility Analysis
        High IV: Market expects big moves (uncertainty)
        Low IV: Market expects stability
        """
        atm_strike = min([abs(entry['CE']['strikePrice'] - self.underlying_value) 
                         for entry in self.options_data if entry['CE']['strikePrice'] > 0])
        
        ce_iv_list = []
        pe_iv_list = []
        atm_iv = 0
        
        for entry in self.options_data:
            strike = entry['CE']['strikePrice']
            if strike == 0:
                continue
            
            ce_iv = entry['CE']['impliedVolatility']
            pe_iv = entry['PE']['impliedVolatility']
            
            if ce_iv > 0:
                ce_iv_list.append(ce_iv)
            if pe_iv > 0:
                pe_iv_list.append(pe_iv)
            
            # Find ATM IV
            if abs(strike - self.underlying_value) == atm_strike:
                atm_iv = (ce_iv + pe_iv) / 2 if (ce_iv > 0 and pe_iv > 0) else max(ce_iv, pe_iv)
        
        avg_ce_iv = sum(ce_iv_list) / len(ce_iv_list) if ce_iv_list else 0
        avg_pe_iv = sum(pe_iv_list) / len(pe_iv_list) if pe_iv_list else 0
        
        iv_skew = avg_pe_iv - avg_ce_iv
        
        # Interpretation
        if atm_iv > 20:
            signal = "HIGH VOLATILITY"
            interpretation = "Market expects significant movement"
        elif atm_iv > 15:
            signal = "MODERATE VOLATILITY"
            interpretation = "Normal market conditions"
        else:
            signal = "LOW VOLATILITY"
            interpretation = "Market expects stability"
        
        if iv_skew > 5:
            skew_signal = "Fear in market (PE IV > CE IV)"
        elif iv_skew < -5:
            skew_signal = "Complacency in market (CE IV > PE IV)"
        else:
            skew_signal = "Balanced volatility"
        
        return {
            'atm_iv': round(atm_iv, 2),
            'avg_ce_iv': round(avg_ce_iv, 2),
            'avg_pe_iv': round(avg_pe_iv, 2),
            'iv_skew': round(iv_skew, 2),
            'signal': signal,
            'skew_signal': skew_signal,
            'interpretation': interpretation
        }
    
    def calculate_buy_sell_pressure(self) -> Dict:
        """
        Order Book Analysis - Buy vs Sell Pressure
        """
        total_ce_buy_qty = 0
        total_ce_sell_qty = 0
        total_pe_buy_qty = 0
        total_pe_sell_qty = 0
        
        for entry in self.options_data:
            if entry['CE']['strikePrice'] > 0:
                total_ce_buy_qty += entry['CE']['totalBuyQuantity']
                total_ce_sell_qty += entry['CE']['totalSellQuantity']
            
            if entry['PE']['strikePrice'] > 0:
                total_pe_buy_qty += entry['PE']['totalBuyQuantity']
                total_pe_sell_qty += entry['PE']['totalSellQuantity']
        
        # Calculate ratios
        ce_pressure = total_ce_buy_qty / total_ce_sell_qty if total_ce_sell_qty > 0 else 0
        pe_pressure = total_pe_buy_qty / total_pe_sell_qty if total_pe_sell_qty > 0 else 0
        
        # Overall pressure (PE buying = bullish, CE buying = bearish)
        net_pressure = pe_pressure - ce_pressure
        
        if net_pressure > 0.5:
            signal = "BULLISH"
            interpretation = "Strong PUT buying suggests bullish stance"
            confidence = min(90, 60 + net_pressure * 30)
        elif net_pressure < -0.5:
            signal = "BEARISH"
            interpretation = "Strong CALL buying suggests bearish hedging"
            confidence = min(90, 60 + abs(net_pressure) * 30)
        else:
            signal = "NEUTRAL"
            interpretation = "Balanced buy-sell pressure"
            confidence = 50
        
        return {
            'ce_buy_sell_ratio': round(ce_pressure, 3),
            'pe_buy_sell_ratio': round(pe_pressure, 3),
            'net_pressure': round(net_pressure, 3),
            'signal': signal,
            'confidence': round(confidence, 1),
            'interpretation': interpretation
        }
    
    def find_support_resistance(self) -> Dict:
        """
        Identify key support and resistance levels based on OI concentration
        """
        strike_data = []
        
        for entry in self.options_data:
            strike = entry['CE']['strikePrice']
            if strike == 0:
                continue
            
            ce_oi = entry['CE']['openInterest']
            pe_oi = entry['PE']['openInterest']
            total_oi = ce_oi + pe_oi
            
            strike_data.append({
                'strike': strike,
                'ce_oi': ce_oi,
                'pe_oi': pe_oi,
                'total_oi': total_oi
            })
        
        # Sort by total OI
        strike_data.sort(key=lambda x: x['total_oi'], reverse=True)
        
        # Find resistances (above current price with high CE OI)
        resistances = sorted([x for x in strike_data if x['strike'] > self.underlying_value], 
                            key=lambda x: x['ce_oi'], reverse=True)[:3]
        
        # Find supports (below current price with high PE OI)
        supports = sorted([x for x in strike_data if x['strike'] < self.underlying_value], 
                         key=lambda x: x['pe_oi'], reverse=True)[:3]
        
        return {
            'immediate_resistance': resistances[0]['strike'] if resistances else None,
            'immediate_support': supports[0]['strike'] if supports else None,
            'all_resistance': [r['strike'] for r in resistances],
            'all_support': [s['strike'] for s in supports],
            'resistance_strength': [r['ce_oi'] for r in resistances],
            'support_strength': [s['pe_oi'] for s in supports]
        }
    
    def calculate_option_greeks(self) -> Dict:
        """
        Calculate Greeks for all CE and PE options
        Returns Delta, Gamma, Theta, Vega for each strike
        """
        # Assume expiry date from data or calculate
        expiry_dates = self.data['records'].get('expiryDates', [])
        if not expiry_dates:
            return {}
        
        nearest_expiry = expiry_dates[0]
        T = self._calculate_time_to_expiry(nearest_expiry)
        r = 0.07  # Risk-free rate
        
        greeks_data = []
        
        for entry in self.options_data:
            strike = entry['CE']['strikePrice']
            if strike == 0:
                continue
            
            # CE Greeks
            ce_iv = entry['CE'].get('impliedVolatility', 20) / 100
            ce_greeks = OptionGreeks.calculate_greeks(
                self.underlying_value, strike, T, r, ce_iv, 'call'
            )
            
            # PE Greeks
            pe_iv = entry['PE'].get('impliedVolatility', 20) / 100
            pe_greeks = OptionGreeks.calculate_greeks(
                self.underlying_value, strike, T, r, pe_iv, 'put'
            )
            
            greeks_data.append({
                'strike': strike,
                'ce': {
                    'delta': ce_greeks['delta'],
                    'gamma': ce_greeks['gamma'],
                    'theta': ce_greeks['theta'],
                    'vega': ce_greeks['vega'],
                    'iv': round(ce_iv * 100, 2),
                    'oi': entry['CE']['openInterest']
                },
                'pe': {
                    'delta': pe_greeks['delta'],
                    'gamma': pe_greeks['gamma'],
                    'theta': pe_greeks['theta'],
                    'vega': pe_greeks['vega'],
                    'iv': round(pe_iv * 100, 2),
                    'oi': entry['PE']['openInterest']
                }
            })
        
        return {
            'expiry_date': nearest_expiry,
            'time_to_expiry_years': round(T, 3),
            'greeks': greeks_data
        }
    
    def _calculate_time_to_expiry(self, expiry_date_str):
        """Calculate time to expiry in years"""
        try:
            expiry_date = datetime.strptime(expiry_date_str, '%d-%b-%Y')
            current_date = datetime.now()
            days_to_expiry = (expiry_date - current_date).days
            return max(days_to_expiry / 365.0, 0.001)
        except:
            return 0.04  # Default
    
    def generate_composite_signal(self) -> Dict:
        """
        Generate final composite signal based on all indicators
        """
        # Get all individual signals
        pcr = self.calculate_pcr()
        max_pain = self.calculate_max_pain()
        oi_buildup = self.analyze_oi_buildup()
        iv_analysis = self.analyze_implied_volatility()
        pressure = self.calculate_buy_sell_pressure()
        levels = self.find_support_resistance()
        greeks = self.calculate_option_greeks()
        options, spot  = derive_and_classify_nifty_option_chain(self.data)
        overall_pcr, overall_pcr_volume = derive_pcr(self.data)
        total_call_oi, total_put_oi, npcr = calculate_oi_pcr(options)
        #time_now = time.strftime("%H:%M:%S")
        # Scoring system
        scores = {
            'STRONG BULLISH': 2,
            'BULLISH': 1,
            'NEUTRAL': 0,
            'BEARISH': -1,
            'STRONG BEARISH': -2
        }
        
        # Calculate weighted score
        total_score = 0
        weights = {
            'pcr': 0.25,
            'max_pain': 0.15,
            'oi_buildup': 0.20,
            'pressure': 0.25,
            'iv': 0.15
        }
        
        total_score += scores.get(pcr['signal'], 0) * weights['pcr']
        total_score += scores.get(max_pain['signal'], 0) * weights['max_pain']
        total_score += scores.get(oi_buildup['signal'], 0) * weights['oi_buildup']
        total_score += scores.get(pressure['signal'], 0) * weights['pressure']
        
        # Final signal
        if total_score > 0.8:
            final_signal = "STRONG BULLISH"
            action = "BUY"
            color = "#00C853"
        elif total_score > 0.3:
            final_signal = "BULLISH"
            action = "BUY ON DIPS"
            color = "#64DD17"
        elif total_score > -0.3:
            final_signal = "NEUTRAL"
            action = "HOLD / WAIT"
            color = "#FFC107"
        elif total_score > -0.8:
            final_signal = "BEARISH"
            action = "SELL ON RISE"
            color = "#FF6F00"
        else:
            final_signal = "STRONG BEARISH"
            action = "SELL"
            color = "#D32F2F"
        
        # Calculate confidence based on agreement
        signals_list = [pcr['signal'], max_pain['signal'], oi_buildup['signal'], pressure['signal']]
        bullish_count = sum([1 for s in signals_list if 'BULLISH' in s])
        bearish_count = sum([1 for s in signals_list if 'BEARISH' in s])
        max_count = max(bullish_count, bearish_count)
        confidence = (max_count / len(signals_list)) * 100

        return_data = {
            'timestamp': self.timestamp,
            'underlying_value': self.underlying_value,
            'final_signal': final_signal,
            'action': action,
            'confidence': round(confidence, 1),
            'score': round(total_score, 2),
            'color': color,
            'pcr_analysis': pcr,
            'max_pain_analysis': max_pain,
            'oi_buildup_analysis': oi_buildup,
            'iv_analysis': iv_analysis,
            'pressure_analysis': pressure,
            'support_resistance': levels,
            'individual_signals': {
                'PCR': pcr['signal'],
                'Max Pain': max_pain['signal'],
                'OI Buildup': oi_buildup['signal'],
                'Buy/Sell Pressure': pressure['signal']
            },
            'spot': spot,
            'total_call_oi': total_call_oi,
            'total_put_oi': total_put_oi,
            'pcr': npcr,
            'overall_pcr': overall_pcr,
            'overall_pcr_volume': overall_pcr_volume
        }

        return_data2 = {
            'timestamp': self.timestamp,
            'underlying_value': self.underlying_value,
            'final_signal': final_signal,
            'action': action,
            'confidence': round(confidence, 1),
            'score': round(total_score, 2),
            'color': color,
            'pcr_analysis': pcr,
            'spot': spot,
            'total_call_oi': total_call_oi,
            'total_put_oi': total_put_oi,
            'pcr': npcr,
            'overall_pcr': overall_pcr,
            'overall_pcr_volume': overall_pcr_volume
        }

        #write_to_local(return_data2)

        return {
            'timestamp': self.timestamp,
            'underlying_value': self.underlying_value,
            'final_signal': final_signal,
            'action': action,
            'confidence': round(confidence, 1),
            'score': round(total_score, 2),
            'color': color,
            'pcr_analysis': pcr,
            'max_pain_analysis': max_pain,
            'oi_buildup_analysis': oi_buildup,
            'iv_analysis': iv_analysis,
            'pressure_analysis': pressure,
            'support_resistance': levels,
            'greeks_analysis': greeks,
            'individual_signals': {
                'PCR': pcr['signal'],
                'Max Pain': max_pain['signal'],
                'OI Buildup': oi_buildup['signal'],
                'Buy/Sell Pressure': pressure['signal']
            },
            'spot': spot,
            'rows': options,
            'total_call_oi': total_call_oi,
            'total_put_oi': total_put_oi,
            'pcr': npcr,
            'overall_pcr': overall_pcr,
            'overall_pcr_volume': overall_pcr_volume
        }


import requests
from pprint import pprint
import pandas as pd
# Use a session so NSE cookies persist
session = requests.Session()

NSE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/option-chain",
    "Connection": "keep-alive"
}


def main():
    """Main execution function"""
    data = fetch_nifty_option_chain("30-Dec-2025")
    analyzer = NiftyTrendAnalyzer(data)
    result = analyzer.generate_composite_signal()
    
    # Save result
    with open('C:/Users/likec/OneDrive/Desktop/MyAutomation/FirstSteps-N/data/analysis_result.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    main()