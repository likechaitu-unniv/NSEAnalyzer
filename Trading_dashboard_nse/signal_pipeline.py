"""
Signal pipeline skeleton for Trading_dashboard_nse

Fetches option-chain, computes Greeks via NiftyTrendAnalyzer, aggregates
portfolio Greeks and emits simple trade signals. Intended as a minimal
runner to integrate with the existing codebase.
"""
import time
import json
import os
from typing import Optional

from Analyzer import NiftyTrendAnalyzer
from utils import fetch_nifty_option_chain, fetch_available_expiries


class SignalPipeline:
    def __init__(self, symbol: str = 'NIFTY'):
        self.symbol = symbol

    def _choose_expiry(self, expiry: Optional[str]) -> Optional[str]:
        if expiry:
            return expiry
        exps = fetch_available_expiries(self.symbol)
        return exps[0] if exps else None

    def fetch_and_analyze(self, expiry: Optional[str] = None) -> dict:
        """Fetch option-chain for `expiry` and return composite analysis dict."""
        e = self._choose_expiry(expiry)
        if not e:
            raise RuntimeError('No expiries available')

        data = fetch_nifty_option_chain(e, symbol=self.symbol)
        analyzer = NiftyTrendAnalyzer(data)
        result = analyzer.generate_composite_signal()
        return result

    def aggregate_portfolio_greeks(self, analysis_result: dict) -> dict:
        """Return a compact aggregation of portfolio Greeks useful for signals."""
        pg = analysis_result.get('portfolio_greeks') or {}
        # Expected keys: portfolio_delta, portfolio_gamma, portfolio_theta, portfolio_vega
        agg = {
            'portfolio_delta': pg.get('portfolio_delta'),
            'delta_signal': pg.get('delta_signal'),
            'portfolio_gamma': pg.get('portfolio_gamma'),
            'gamma_risk': pg.get('gamma_risk'),
            'portfolio_theta': pg.get('portfolio_theta'),
            'portfolio_vega': pg.get('portfolio_vega'),
        }
        return agg

    def make_signal_summary(self, analysis_result: dict) -> dict:
        """Produce a compact human/machine readable summary of the current state."""
        summary = {
            'timestamp': analysis_result.get('timestamp'),
            'spot': analysis_result.get('underlying_value'),
            'final_signal': analysis_result.get('final_signal'),
            'confidence': analysis_result.get('confidence'),
            'score': analysis_result.get('score'),
            'portfolio_greeks': self.aggregate_portfolio_greeks(analysis_result),
        }
        return summary

    def run(self, expiry: Optional[str] = None, interval: int = 60, iterations: Optional[int] = None, out_path: str = 'data/signal_latest.json'):
        """Run the pipeline periodically.

        - `expiry`: optional expiry string; if None choose nearest expiry
        - `interval`: seconds between runs
        - `iterations`: number of iterations to run (None = infinite)
        - `out_path`: file path to write latest summary
        """
        os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
        count = 0
        try:
            while iterations is None or count < iterations:
                try:
                    res = self.fetch_and_analyze(expiry)
                    summary = self.make_signal_summary(res)
                    # Print concise summary
                    print(f"[{summary.get('timestamp')}] Spot={summary.get('spot')}, Signal={summary.get('final_signal')}, Conf={summary.get('confidence')}%")
                    # Save to file
                    with open(out_path, 'w') as f:
                        json.dump({'analysis': res, 'summary': summary}, f, indent=2)
                except Exception as e:
                    print(f"[ERROR] fetch/analyze iteration failed: {e}")
                count += 1
                if iterations is not None and count >= iterations:
                    break
                time.sleep(interval)
        except KeyboardInterrupt:
            print('Interrupted by user')


def cli_runner():
    import argparse
    parser = argparse.ArgumentParser(description='Signal pipeline runner for Trading_dashboard_nse')
    parser.add_argument('--expiry', help='Expiry string (e.g. 30-Dec-2025)', default=None)
    parser.add_argument('--interval', help='Seconds between runs', type=int, default=60)
    parser.add_argument('--iterations', help='Number of iterations (default: infinite)', type=int, default=1)
    parser.add_argument('--out', help='Output JSON file', default='data/signal_latest.json')
    args = parser.parse_args()

    sp = SignalPipeline()
    sp.run(expiry=args.expiry, interval=args.interval, iterations=args.iterations, out_path=args.out)


if __name__ == '__main__':
    cli_runner()
