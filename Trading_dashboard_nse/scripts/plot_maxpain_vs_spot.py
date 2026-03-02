import json
import glob
import os
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def load_trends(data_dir):
    files = sorted(glob.glob(os.path.join(data_dir, 'trend_history_*.json')))
    rows = []
    for f in files:
        try:
            with open(f, 'r', encoding='utf-8') as fh:
                doc = json.load(fh)
        except Exception:
            continue
        trends = doc.get('trends') or []
        for t in trends:
            ts = t.get('timestamp') or t.get('recorded_at')
            try:
                ts_dt = datetime.fromisoformat(ts) if ts else None
            except Exception:
                ts_dt = None

            spot = t.get('nifty_value') or t.get('spot') or t.get('underlying_value')
            # try to get recorded max pain if available
            maxpain = None
            if isinstance(t.get('max_pain_analysis'), dict):
                maxpain = t['max_pain_analysis'].get('max_pain_strike')

            rows.append({'ts': ts_dt, 'spot': spot, 'maxpain': maxpain})
    return rows


def prepare_series(rows):
    rows = [r for r in rows if r['spot'] is not None]
    rows.sort(key=lambda x: (x['ts'] is None, x['ts']))

    xs = [r['ts'] or datetime.now() for r in rows]
    spots = [r['spot'] for r in rows]
    maxp = []
    for r in rows:
        if r['maxpain'] is not None:
            maxp.append(r['maxpain'])
        else:
            # fallback heuristic: nearest 100 to spot
            try:
                maxp.append(int(round(r['spot'] / 100.0) * 100))
            except Exception:
                maxp.append(r['spot'])

    return xs, spots, maxp


def plot(xs, spots, maxp, outpath):
    plt.figure(figsize=(12, 5))
    plt.plot(xs, spots, label='Spot (nifty_value)', color='tab:blue', linewidth=1)
    plt.plot(xs, maxp, label='Max Pain (strike)', color='tab:orange', linewidth=1)
    plt.scatter(xs, maxp, s=8, color='tab:orange')
    plt.xlabel('Time')
    plt.ylabel('Price')
    plt.title('Max Pain vs Spot Price')
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(outpath)
    print('Saved plot to', outpath)


def save_to_static(src_path):
    # ensure static images folder exists in project
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    static_dir = os.path.join(base, 'static', 'images')
    os.makedirs(static_dir, exist_ok=True)
    dst = os.path.join(static_dir, os.path.basename(src_path))
    try:
        from shutil import copy2
        copy2(src_path, dst)
        print('Copied plot to', dst)
    except Exception as e:
        print('Failed to copy plot to static:', e)


def main():
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    data_dir = os.path.abspath(data_dir)
    rows = load_trends(data_dir)
    if not rows:
        print('No trend rows found in', data_dir)
        return
    xs, spots, maxp = prepare_series(rows)
    outpath = os.path.join(data_dir, 'maxpain_vs_spot.png')
    plot(xs, spots, maxp, outpath)
    # also copy into static/images for dashboard consumption
    save_to_static(outpath)


if __name__ == '__main__':
    main()
