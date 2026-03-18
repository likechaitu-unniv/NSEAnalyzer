
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


def fetch_india_vix():
    """Fetch India VIX using multiple fallbacks.
    Primary: Yahoo Finance quote API for ^INDIAVIX.
    Fallbacks: attempt to scrape NSE pages if Yahoo fails.
    Returns float value or None on failure.
    """
    # 1) Try Yahoo Finance API (use a friendly user-agent)
    yahoo_url = "https://query1.finance.yahoo.com/v7/finance/quote?symbols=%5EINDIAVIX"
    try:
        print(f"[DEBUG] fetch_india_vix: trying Yahoo API: {yahoo_url}")
        r = session.get(yahoo_url, headers=NSE_HEADERS, timeout=8)
        if r.status_code == 200:
            data = r.json()
            q = data.get('quoteResponse', {}).get('result', [])
            if q and isinstance(q, list):
                val = q[0].get('regularMarketPrice') or q[0].get('regularMarketPreviousClose')
                if val is not None:
                    print(f"[DEBUG] fetch_india_vix: Yahoo returned {val}")
                    try:
                        return float(val)
                    except Exception:
                        pass
    except Exception as e:
        print(f"[WARN] fetch_india_vix: Yahoo API failed: {e}")

    # 2) Try NSE India index API: prefetch homepage to establish cookies then call index API
    nse_index_api = "https://www.nseindia.com/api/quote-index?index=india-vix"
    try:
        print(f"[DEBUG] fetch_india_vix: prefetching NSE homepage to set cookies")
        session.get("https://www.nseindia.com", headers=NSE_HEADERS, timeout=6)
    except Exception as e:
        print(f"[WARN] fetch_india_vix: NSE homepage prefetch failed: {e}")

    try:
        print(f"[DEBUG] fetch_india_vix: trying NSE index API: {nse_index_api}")
        r = session.get(nse_index_api, headers=NSE_HEADERS, timeout=8)
        if r.status_code == 200:
            try:
                data = r.json()
            except Exception:
                data = None

            val = None
            if isinstance(data, dict):
                # Try multiple common keys
                val = (data.get('index', {}) or {}).get('last') or data.get('last') or data.get('price') or (data.get('data') and data.get('data').get('last'))
            if val is not None:
                try:
                    return float(val)
                except Exception:
                    pass
    except Exception as e:
        print(f"[WARN] fetch_india_vix: NSE API attempt failed: {e}")

    # 3) Give up gracefully
    # 3) Fallback: try scraping Yahoo Finance page HTML for the value
    try:
        yahoo_html = "https://finance.yahoo.com/quote/%5EINDIAVIX?p=%5EINDIAVIX"
        print(f"[DEBUG] fetch_india_vix: trying Yahoo HTML fallback: {yahoo_html}")
        r = session.get(yahoo_html, headers=NSE_HEADERS, timeout=8)
        if r.status_code == 200 and r.text:
            import re
            m = re.search(r'"regularMarketPrice"\s*:\s*\{\s*"raw"\s*:\s*([0-9]+\.?[0-9]*)', r.text)
            if m:
                try:
                    val = float(m.group(1))
                    print(f"[DEBUG] fetch_india_vix: parsed Yahoo HTML value {val}")
                    return val
                except Exception:
                    pass
    except Exception as e:
        print(f"[WARN] fetch_india_vix: Yahoo HTML fallback failed: {e}")

    print('[DEBUG] fetch_india_vix: all methods failed, returning None')
    return None


def fetch_nifty_option_chain(exp_date, symbol = "NIFTY"):
    print(f"[DEBUG] fetch_nifty_option_chain() called: exp_date={exp_date}, symbol={symbol}")
    print("Getting Data for :", exp_date)

    home_url = "https://www.nseindia.com"
    url = home_url+"/api/option-chain-v3?type=Indices&symbol="+symbol+"&expiry="+exp_date
    print(f"[DEBUG] Making request to: {url}")
    r = session.get(url, headers=NSE_HEADERS, timeout=5)
    print("OC status:", r.status_code)
    print(f"[DEBUG] Response status code: {r.status_code}")
    try:
        data = r.json()
    except Exception as e:
        raise RuntimeError(f"NSE did not return JSON (likely HTML / blocked): {e}")

    if "records" not in data or "data" not in data["records"]:
        raise RuntimeError("NSE response missing 'records' or 'data' – possibly blocked or HTML returned")

    return data


def fetch_available_expiries(symbol="NIFTY"):
    """Fetch available expiry dates from NSE option-chain API for given symbol.
    Returns list of expiry strings as provided by NSE (e.g. '01-Mar-2026').
    """
    print(f"[DEBUG] fetch_available_expiries() called for symbol={symbol}")
    home_url = "https://www.nseindia.com"
    url = home_url + f"/api/option-chain-v3?type=Indices&symbol={symbol}&expiry=01-Mar-2020"
    try:
        # prefetch homepage to set cookies
        session.get(home_url, headers=NSE_HEADERS, timeout=6)
    except Exception as e:
        print(f"[WARN] prefetch homepage failed: {e}")
    try:
        r = session.get(url, headers=NSE_HEADERS, timeout=6)
        if r.status_code != 200:
            print(f"[WARN] expiry list request returned status {r.status_code}")
            return []
        data = r.json()
        expiries = data.get('records', {}).get('expiryDates', [])
        print(f"[DEBUG] fetched expiries: {expiries}")
        return expiries if isinstance(expiries, list) else []
    except Exception as e:
        print(f"[ERROR] fetch_available_expiries failed: {e}")
        return []


def derive_pcr(chain):
    print("[DEBUG] derive_pcr() called")
    print("Started pcr calculation")
    overall_pcr = round((chain["filtered"].get("PE")["totOI"]/chain["filtered"].get("CE")["totOI"]),2)
    overall_pcr_volume = round((chain["filtered"].get("PE")["totVol"]/chain["filtered"].get("CE")["totVol"]),2)
    print(f"[DEBUG] PCR Results: overall_pcr={overall_pcr}, overall_pcr_volume={overall_pcr_volume}")
    print("done pcr calculation")
    return overall_pcr, overall_pcr_volume



def write_to_local(data_to_write ):
    import json
    import datetime
    timestamp_str = datetime.datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
    filename = "data/N50_processed"+str(timestamp_str)+".json"
    try:
        with open(filename, 'w') as json_file:
            json.dump(data_to_write, json_file, indent=4) # The 'indent' parameter makes the file human-readable
        print(f"Successfully wrote data to {filename}")
    except IOError as e:
        print(f"Error writing to file: {e}")



def derive_nifty_option_chain(chain):
    records = chain["records"]
    rows = records["data"]
    spot_raw = records.get("underlyingValue")
    spot = float(str(spot_raw).replace(",", ""))
    df = pd.DataFrame(rows)
    target_expiry = records["expiryDates"][0]  # nearest expiry [web:103]
    df = df[df["expiryDates"] == target_expiry]

    step = 50
    atm_strike = round(spot / step) * step

    strikes = [atm_strike + i * step for i in range(-15, 15)]


    options = []
    for row in rows:
        if row["strikePrice"] in strikes:
           ce_ltp = row["CE"]["lastPrice"]
           pe_ltp = row["PE"]["lastPrice"]
           print("Cal CE dist",round(spot - ce_ltp - row["strikePrice"], 2))
           print("Cal PE dist",round(spot - pe_ltp - row["strikePrice"], 2))
           


           options.append({
                "strike": row["strikePrice"],
                "ce_ltp": ce_ltp,
                "ce_oi": row["CE"]["openInterest"],
                "ce_iv": row["CE"]["impliedVolatility"],
                "pe_iv": row["PE"]["impliedVolatility"],
                "ce_pchangeinOpenInterest" :f"{round(row['CE']['pchangeinOpenInterest'])}%",
                "ce_spot_distance": round(spot - ce_ltp - row["strikePrice"], 2),
                "ce_spot_distance_pct": round(((spot - ce_ltp) / spot) * 100, 2),
                "pe_ltp": pe_ltp,
                "pe_oi": row["PE"]["openInterest"],
                "pe_pchangeinOpenInterest" :f"{round(row['PE']['pchangeinOpenInterest'])}%",
                "pe_spot_distance": round(spot - pe_ltp - row["strikePrice"], 2),
                "pe_spot_distance_pct": round(((spot - pe_ltp) / spot) * 100, 2),
            })
    return options, spot 

def calculate_oi_pcr(options):
    # 2. Compute totals
    total_call_oi = sum(row.get('ce_oi', 0) for row in options)
    total_put_oi  = sum(row.get('pe_oi', 0) for row in options)
    # 3. Compute PCR safely
    pcr = round(total_put_oi / total_call_oi, 2) if total_call_oi else None
    return total_call_oi, total_put_oi, pcr


def classify_buildup(data):
    results = []
    for row in data['records']['data']:
        strike = row['strikePrice']
        ce = row.get('CE', {})
        pe = row.get('PE', {})
        
        ce_oi_change = ce.get('pchangeinOpenInterest', 0)
        pe_oi_change = pe.get('pchangeinOpenInterest', 0)
        ce_vol = ce.get('totalTradedVolume', 0)
        pe_vol = pe.get('totalTradedVolume', 0)
        
        buildup_type = "Neutral"
        
        # Long Call Buildup: CE OI up, PE OI down/stable, high CE vol
        if ce_oi_change > 5 and pe_oi_change <= 0 and ce_vol > 1000:
            buildup_type = "Long Call Buildup"
        # Long Put Buildup: PE OI up, CE OI down/stable, high PE vol
        elif pe_oi_change > 5 and ce_oi_change <= 0 and pe_vol > 1000:
            buildup_type = "Long Put Buildup"
        # Short Call Buildup: CE OI down, high CE vol
        elif ce_oi_change < -5 and ce_vol > 1000:
            buildup_type = "Short Call Buildup"
        # Short Put Buildup: PE OI down, high PE vol
        elif pe_oi_change < -5 and pe_vol > 1000:
            buildup_type = "Short Put Buildup"
        # Overall Long: Both OI up
        elif ce_oi_change > 5 and pe_oi_change > 5:
            buildup_type = "Overall Long Buildup"
        # Overall Short: Both OI down
        elif ce_oi_change < -5 and pe_oi_change < -5:
            buildup_type = "Overall Short Buildup"
        
        results.append({
            "strike": strike,
            "buildup_type": buildup_type,
            "ce_oi_change": ce_oi_change,
            "pe_oi_change": pe_oi_change,
            "ce_vol": ce_vol,
            "pe_vol": pe_vol
        })
        pprint(results) 
    return results


# ...existing code...
def derive_and_classify_nifty_option_chain(chain):
    records = chain["records"]
    rows = records["data"]
    spot_raw = records.get("underlyingValue")
    spot = float(str(spot_raw).replace(",", ""))
    df = pd.DataFrame(rows)
    target_expiry = records["expiryDates"][0]  # nearest expiry
    df = df[df["expiryDates"] == target_expiry]

    step = 50
    atm_strike = round(spot / step) * step
    strikes = [atm_strike + i * step for i in range(-15, 15)]

    options = []
    for row in rows:
        if row["strikePrice"] in strikes:
            ce = row.get('CE', {})
            pe = row.get('PE', {})
            
            ce_ltp = ce.get("lastPrice", 0)
            pe_ltp = pe.get("lastPrice", 0)

            # Prefer absolute OI change when available; fall back to percent change
            ce_oi_change_abs = ce.get('changeinOpenInterest') if ce.get('changeinOpenInterest') is not None else 0
            pe_oi_change_abs = pe.get('changeinOpenInterest') if pe.get('changeinOpenInterest') is not None else 0
            try:
                ce_oi_pct = float(ce.get('pchangeinOpenInterest', 0))
            except Exception:
                ce_oi_pct = 0
            try:
                pe_oi_pct = float(pe.get('pchangeinOpenInterest', 0))
            except Exception:
                pe_oi_pct = 0

            # Price directional change (may be absent in some datasets)
            ce_price_change = ce.get('change', 0) or ce.get('pChange', 0) or 0
            pe_price_change = pe.get('change', 0) or pe.get('pChange', 0) or 0

            ce_vol = ce.get('totalTradedVolume', 0)
            pe_vol = pe.get('totalTradedVolume', 0)

            # Heuristics: significant movement if absolute OI change or percent change or large volume
            def significant_move(abs_change, pct_change, vol, abs_thresh=100, pct_thresh=5, vol_thresh=1000):
                return (abs(abs_change) >= abs_thresh) or (abs(pct_change) >= pct_thresh) or (vol >= vol_thresh and abs(abs_change) > 0)

            # Classify CE buildup using absolute OI change (preferred) and price direction when available
            ce_buildup_type = "Neutral"
            if significant_move(ce_oi_change_abs, ce_oi_pct, ce_vol):
                if ce_oi_change_abs > 0:
                    if ce_price_change > 0:
                        ce_buildup_type = "Call Buying"
                    elif ce_price_change < 0:
                        ce_buildup_type = "Call Writing"
                    else:
                        ce_buildup_type = "Call Buildup"
                elif ce_oi_change_abs < 0:
                    if ce_price_change > 0:
                        ce_buildup_type = "Call Short Cover"
                    elif ce_price_change < 0:
                        ce_buildup_type = "Call Long Cover"
                    else:
                        ce_buildup_type = "Call Unwinding"

            # Classify PE buildup similarly
            pe_buildup_type = "Neutral"
            if significant_move(pe_oi_change_abs, pe_oi_pct, pe_vol):
                if pe_oi_change_abs > 0:
                    if pe_price_change > 0:
                        pe_buildup_type = "Put Buying"
                    elif pe_price_change < 0:
                        pe_buildup_type = "Put Writing"
                    else:
                        pe_buildup_type = "Put Buildup"
                elif pe_oi_change_abs < 0:
                    if pe_price_change > 0:
                        pe_buildup_type = "Put Short Cover"
                    elif pe_price_change < 0:
                        pe_buildup_type = "Put Long Cover"
                    else:
                        pe_buildup_type = "Put Unwinding"
            

            ce_spot_distance = ce_ltp
            pe_spot_distance = pe_ltp
            if row["strikePrice"] < spot:
                ce_spot_distance = round(-spot + ce_ltp + row["strikePrice"], 2)
            elif row["strikePrice"] > spot:
                pe_spot_distance = round((pe_ltp +spot - row["strikePrice"]), 2)
                

            options.append({
                "strike": row["strikePrice"],
                "ce_ltp": ce_ltp,
                "ce_oi": ce.get("openInterest", 0),
                "ce_iv": ce.get("impliedVolatility", 0),
                "ce_spot_distance": ce_spot_distance,
                "ce_spot_distance_pct": round(((spot - ce_ltp) / spot) * 100, 2),
                "pe_iv": pe.get("impliedVolatility", 0),
                "ce_pchangeinOpenInterest": f"{round(ce_oi_pct)}%",
                "pe_ltp": pe_ltp,
                "pe_oi": pe.get("openInterest", 0),
                "pe_spot_distance": pe_spot_distance,
                "pe_spot_distance_pct": round(((spot - pe_ltp) / spot) * 100, 2),
                "pe_pchangeinOpenInterest": f"{round(pe_oi_pct)}%",
                "ce_buildup_type": ce_buildup_type,
                "pe_buildup_type": pe_buildup_type,
                "ce_vol": ce_vol,
                "pe_vol": pe_vol
            })
    return options, spot
# ...existing code...