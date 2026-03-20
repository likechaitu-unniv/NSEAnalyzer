"""
metrics/greeks.py  —  Black-Scholes Greeks (pure Python, no mibian)
Dependencies: math, scipy.stats (both in standard scipy install)
"""

import math
from datetime import datetime, date
from typing import List, Dict, Optional
from scipy.stats import norm

# ── Black-Scholes core ────────────────────────────────────────────────────────

def _d1_d2(S: float, K: float, T: float, r: float, sigma: float):
    """
    S     = underlying price
    K     = strike price
    T     = time to expiry in years
    r     = risk-free rate as decimal (e.g. 0.065)
    sigma = implied volatility as decimal (e.g. 0.15 for 15%)
    """
    if sigma <= 0 or T <= 0 or S <= 0 or K <= 0:
        return None, None
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    return d1, d2


def bs_greeks(S: float, K: float, T: float, r: float, sigma: float, flag: str) -> dict:
    """
    Compute Delta, Gamma, Theta, Vega for a European option.

    flag : 'c' for call, 'p' for put

    Returns dict with keys: delta, gamma, theta, vega
    All values rounded to 6 decimal places.
    Theta is expressed as daily decay (divided by 365).
    Vega  is expressed per 1% move in IV (divided by 100).
    """
    d1, d2 = _d1_d2(S, K, T, r, sigma)
    if d1 is None:
        return {g: None for g in ("delta", "gamma", "theta", "vega")}

    nd1  = norm.pdf(d1)          # standard normal PDF at d1
    Nd1  = norm.cdf(d1)          # CDF at d1
    Nd2  = norm.cdf(d2)
    Nnd1 = norm.cdf(-d1)
    Nnd2 = norm.cdf(-d2)

    sqrt_T = math.sqrt(T)
    e_rT   = math.exp(-r * T)

    # ── Delta ──────────────────────────────────────────────────────────────
    delta = Nd1 if flag == "c" else Nd1 - 1

    # ── Gamma (same for call and put) ───────────────────────────────────────
    gamma = nd1 / (S * sigma * sqrt_T)

    # ── Theta (annualised → daily) ──────────────────────────────────────────
    common_theta = -(S * nd1 * sigma) / (2 * sqrt_T)
    if flag == "c":
        theta = (common_theta - r * K * e_rT * Nd2)  / 365
    else:
        theta = (common_theta + r * K * e_rT * Nnd2) / 365

    # ── Vega (per 1% IV change) ─────────────────────────────────────────────
    vega = S * nd1 * sqrt_T / 100

    return {
        "delta": round(delta, 6),
        "gamma": round(gamma, 6),
        "theta": round(theta, 6),
        "vega":  round(vega,  6),
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def days_to_expiry(expiry_str: str) -> float:
    """Parse NSE expiry string like '25-Apr-2024' → years as float."""
    try:
        exp = datetime.strptime(expiry_str, "%d-%b-%Y").date()
        days = max((exp - date.today()).days, 1)
        return days / 365.0
    except Exception:
        return 30 / 365.0


def compute_greeks(records: List[Dict], vix: float) -> List[Dict]:
    """
    Enrich each strike record with BS Greeks for both CE and PE legs.
    Uses NSE-provided IV when available; falls back to VIX as proxy.
    IV and rate are converted from percentage to decimal internally.
    """
    R = 0.065        # RBI repo rate as decimal
    enriched = []

    for row in records:
        S      = row.get("underlying", 0)
        K      = row.get("strike", 0)
        T      = days_to_expiry(row.get("expiry", ""))

        for side, flag in (("ce", "c"), ("pe", "p")):
            iv_pct = row.get(f"{side}_iv") or vix or 15.0
            sigma  = iv_pct / 100.0          # percent → decimal

            greeks = bs_greeks(S, K, T, R, sigma, flag)
            row[f"{side}_delta"] = greeks["delta"]
            row[f"{side}_gamma"] = greeks["gamma"]
            row[f"{side}_theta"] = greeks["theta"]
            row[f"{side}_vega"]  = greeks["vega"]

        enriched.append(row)

    return enriched


# ─────────────────────────────────────────────────────────────────────────────

"""
metrics/pcr.py  —  Put-Call Ratio
"""


def compute_pcr(records: List[Dict]) -> dict:
    """
    PCR by OI and by volume, aggregated across all strikes.
    PCR > 1 = bearish sentiment (more put OI); < 1 = bullish.
    """
    total_ce_oi = total_pe_oi = 0
    total_ce_vol = total_pe_vol = 0

    for row in records:
        total_ce_oi  += row.get("ce_oi", 0)
        total_pe_oi  += row.get("pe_oi", 0)
        total_ce_vol += row.get("ce_volume", 0)
        total_pe_vol += row.get("pe_volume", 0)

    pcr_oi  = round(total_pe_oi  / total_ce_oi,  3) if total_ce_oi  else 0
    pcr_vol = round(total_pe_vol / total_ce_vol, 3) if total_ce_vol else 0

    return {
        "pcr_oi":       pcr_oi,
        "pcr_vol":      pcr_vol,
        "total_ce_oi":  total_ce_oi,
        "total_pe_oi":  total_pe_oi,
        "sentiment":    "bearish" if pcr_oi > 1.2 else "bullish" if pcr_oi < 0.8 else "neutral",
    }


# ─────────────────────────────────────────────────────────────────────────────

"""
metrics/max_pain.py  —  Max Pain strike
The strike where total dollar loss for all option buyers is maximised
(i.e. where the market "wants" to close at expiry).
"""


def compute_max_pain(records: List[Dict]) -> dict:
    """
    For each candidate strike S, compute total pain =
      Σ CE_OI × max(S - strike, 0)  +  Σ PE_OI × max(strike - S, 0)
    Max pain = strike S that minimises this total.
    """
    strikes = sorted(set(r["strike"] for r in records))
    if not strikes:
        return {"max_pain": 0, "pain_by_strike": {}}

    pain_map = {}
    for s in strikes:
        total = 0
        for row in records:
            k = row["strike"]
            total += row.get("ce_oi", 0) * max(s - k, 0)
            total += row.get("pe_oi", 0) * max(k - s, 0)
        pain_map[s] = total

    max_pain_strike = min(pain_map, key=pain_map.get)
    return {
        "max_pain":       max_pain_strike,
        "pain_by_strike": pain_map,
    }


# ─────────────────────────────────────────────────────────────────────────────

"""
metrics/iv_skew.py  —  IV Skew
Plots implied volatility across OTM strikes for the nearest expiry.
"""


def compute_iv_skew(records: List[Dict], underlying: float) -> dict:
    """
    Returns IV curve: list of {strike, ce_iv, pe_iv, moneyness}
    moneyness = (strike - underlying) / underlying * 100
    """
    if not underlying:
        return {"skew": []}

    # Use nearest expiry only
    expiries = sorted(set(r["expiry"] for r in records if r.get("expiry")))
    if not expiries:
        return {"skew": []}

    nearest = expiries[0]
    subset  = [r for r in records if r.get("expiry") == nearest]
    subset  = sorted(subset, key=lambda r: r["strike"])

    skew = []
    for row in subset:
        strike = row["strike"]
        skew.append({
            "strike":     strike,
            "moneyness":  round((strike - underlying) / underlying * 100, 2),
            "ce_iv":      row.get("ce_iv", 0),
            "pe_iv":      row.get("pe_iv", 0),
        })

    return {"expiry": nearest, "underlying": underlying, "skew": skew}


# ─────────────────────────────────────────────────────────────────────────────

"""
metrics/oi_delta.py  —  OI Buildup / Unwinding detection
"""


def classify_oi(price_chg: float, oi_chg: float) -> str:
    """
    Classic 4-quadrant OI interpretation:
      price↑ OI↑ = long buildup    (bullish)
      price↓ OI↑ = short buildup   (bearish)
      price↑ OI↓ = short covering  (bullish)
      price↓ OI↓ = long unwinding  (bearish)
    """
    if price_chg >= 0 and oi_chg >= 0:
        return "long_buildup"
    elif price_chg < 0 and oi_chg >= 0:
        return "short_buildup"
    elif price_chg >= 0 and oi_chg < 0:
        return "short_covering"
    else:
        return "long_unwinding"


def compute_oi_delta(records: List[Dict], underlying_chg_pct: float) -> List[Dict]:
    """
    For each strike, classify OI movement for both CE and PE.
    underlying_chg_pct: % change in underlying since last snapshot.
    """
    results = []
    for row in records:
        row_date = {
            "strike":       row["strike"],
            "expiry":       row.get("expiry", ""),
            "ce_oi_signal": classify_oi(underlying_chg_pct, row.get("ce_chg_oi", 0)),
            "pe_oi_signal": classify_oi(-underlying_chg_pct, row.get("pe_chg_oi", 0)),
            "ce_chg_oi":    row.get("ce_chg_oi", 0),
            "pe_chg_oi":    row.get("pe_chg_oi", 0),
        }        
        results.append(row_date)
    return results
