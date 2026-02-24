
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
            ce_oi_change = ce.get('pchangeinOpenInterest', 0)
            pe_oi_change = pe.get('pchangeinOpenInterest', 0)
            ce_price_change = ce.get('change', 0)
            pe_price_change = pe.get('change', 0)
            ce_vol = ce.get('totalTradedVolume', 0)
            pe_vol = pe.get('totalTradedVolume', 0)
            
            # Classify CE buildup based on OI, price changes, and volume (threshold > 1000 for activity)
            ce_buildup_type = "Neutral"
            if ce_oi_change > 0 and ce_vol > 1000:
                if ce_price_change > 0:
                    ce_buildup_type = "Call Buying"
                elif ce_price_change < 0:
                    ce_buildup_type = "Call Writing"
            elif ce_oi_change < 0 and ce_vol > 1000:
                if ce_price_change > 0:
                    ce_buildup_type = "Call Long Cover"
                elif ce_price_change < 0:
                    ce_buildup_type = "Call Short Cover"
            
            # Classify PE buildup based on OI, price changes, and volume (threshold > 1000 for activity)
            pe_buildup_type = "Neutral"
            if pe_oi_change > 0 and pe_vol > 1000:
                if pe_price_change > 0:
                    pe_buildup_type = "Put Buying"
                elif pe_price_change < 0:
                    pe_buildup_type = "Put Writing"
            elif pe_oi_change < 0 and pe_vol > 1000:
                if pe_price_change > 0:
                    pe_buildup_type = "Put Long Cover"
                elif pe_price_change < 0:
                    pe_buildup_type = "Put Short Cover"
            

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
                "ce_pchangeinOpenInterest": f"{round(ce_oi_change)}%",
                "pe_ltp": pe_ltp,
                "pe_oi": pe.get("openInterest", 0),
                "pe_spot_distance": pe_spot_distance,
                "pe_spot_distance_pct": round(((spot - pe_ltp) / spot) * 100, 2),
                "pe_pchangeinOpenInterest": f"{round(pe_oi_change)}%",
                "ce_buildup_type": ce_buildup_type,
                "pe_buildup_type": pe_buildup_type,
                "ce_vol": ce_vol,
                "pe_vol": pe_vol
            })
    return options, spot
# ...existing code...