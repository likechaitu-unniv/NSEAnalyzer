"""
Options Strategy Computation Engine
Ported from the JS buildStrategiesTab() frontend function.

Takes analysis_result from NiftyTrendAnalyzer.generate_composite_signal() plus
market context (mkt_trend, breadth, pcr_trend) and returns a fully-computed
strategy recommendation dict ready for JSON serialisation.
"""


def compute_strategy(analysis_result, mkt_trend='', breadth=50.0, pcr_trend='stable'):
    """
    Compute options strategy recommendation from live analysis data.

    Args:
        analysis_result : dict  – result of NiftyTrendAnalyzer.generate_composite_signal()
        mkt_trend       : str   – e.g. 'Strong Bullish', 'Bearish', 'Neutral'
        breadth         : float – % of advancing stocks (0-100)
        pcr_trend       : str   – 'rising', 'falling', or 'stable'

    Returns:
        dict with keys: context, reasons, primary, categories,
                        alternatives, checks, go_count, go_ratio,
                        go_status, go_verdict, strike_matrix
    """
    ar = analysis_result or {}

    # ── 1. DATA GATHERING ────────────────────────────────────────────
    spot = float(ar.get('underlying_value') or 0)

    max_pain_data = ar.get('max_pain_analysis') or {}
    max_pain = float(max_pain_data.get('max_pain_strike') or 0)
    mp_dist = spot - max_pain if max_pain > 0 else 0
    mp_dist_pct = (mp_dist / max_pain) * 100 if max_pain > 0 else 0

    pcr_data = ar.get('pcr_analysis') or {}
    pcr_oi = float(pcr_data.get('pcr_oi') or 1.0)
    pcr_vol = float(pcr_data.get('pcr_volume') or 1.0)

    iv_data = ar.get('iv_analysis') or {}
    atm_iv = float(iv_data.get('atm_iv') or 0)
    ce_iv = float(iv_data.get('avg_ce_iv') or atm_iv)
    pe_iv = float(iv_data.get('avg_pe_iv') or atm_iv)
    iv_skew = float(iv_data.get('iv_skew') or ((pe_iv - ce_iv) / ce_iv * 100 if ce_iv > 0 else 0))

    vix = float(ar.get('vix') or 0)

    oi_bld = ar.get('oi_buildup_analysis') or {}
    call_writing = abs(float(oi_bld.get('call_writing') or 0))
    put_writing = abs(float(oi_bld.get('put_writing') or 0))
    bld_sig = str(oi_bld.get('signal') or '').upper()

    pressure = ar.get('pressure_analysis') or {}

    sr = ar.get('support_resistance') or {}
    resistance = float(sr.get('immediate_resistance') or 0)
    support = float(sr.get('immediate_support') or 0)

    final_sig = str(ar.get('final_signal') or '').upper()
    confidence = float(ar.get('confidence') or 0)

    greeks = ar.get('portfolio_greeks') or {}
    delta_signal = str(greeks.get('delta_signal') or '').upper()

    fmo = ar.get('fast_moving_options') or {}
    fmo_dir = str(fmo.get('overall_direction') or '').upper()

    mkt = str(mkt_trend or '').upper()
    breadth = float(breadth or 50)

    # Strike step detection
    strike_step = 50
    chain_rows = ar.get('rows') or []
    if len(chain_rows) > 1:
        s0 = float((chain_rows[0] or {}).get('strike') or
                   (chain_rows[0] or {}).get('strikePrice') or 0)
        s1 = float((chain_rows[1] or {}).get('strike') or
                   (chain_rows[1] or {}).get('strikePrice') or 0)
        if s1 - s0 > 1:
            strike_step = int(s1 - s0)

    atm_strike = int(round(spot / strike_step)) * strike_step if spot > 0 else 0

    high_vol = vix > 18 or atm_iv > 20
    low_vol = 0 < vix < 13 and 0 < atm_iv < 15
    near_mp = max_pain > 0 and abs(mp_dist_pct) < 0.5

    ss = strike_step  # shorthand

    # ── 2. SIGNAL SCORING ────────────────────────────────────────────
    bull_score = 0
    bear_score = 0
    reasons = []

    def add_reason(txt, direction, pts):
        nonlocal bull_score, bear_score
        if direction == 'bull':
            bull_score += pts
        else:
            bear_score += pts
        reasons.append({'txt': txt, 'dir': direction})

    if 'BULL' in final_sig:
        add_reason('Signal: ' + final_sig, 'bull', 2)
    if 'BEAR' in final_sig:
        add_reason('Signal: ' + final_sig, 'bear', 2)

    if 'STRONG' in mkt and 'BULL' in mkt:
        add_reason('Mkt: Strong Bullish Trend', 'bull', 3)
    elif 'BULL' in mkt:
        add_reason('Mkt Trend: Bullish', 'bull', 2)
    if 'STRONG' in mkt and 'BEAR' in mkt:
        add_reason('Mkt: Strong Bearish Trend', 'bear', 3)
    elif 'BEAR' in mkt:
        add_reason('Mkt Trend: Bearish', 'bear', 2)

    if pcr_oi > 1.3:
        add_reason(f'PCR {pcr_oi:.2f} > 1.3 (Bullish)', 'bull', 2)
    elif pcr_oi > 1.0:
        add_reason(f'PCR {pcr_oi:.2f} (Mild Bullish)', 'bull', 1)
    elif pcr_oi < 0.7:
        add_reason(f'PCR {pcr_oi:.2f} < 0.7 (Bearish)', 'bear', 2)
    elif pcr_oi < 1.0:
        add_reason(f'PCR {pcr_oi:.2f} (Mild Bearish)', 'bear', 1)

    if mp_dist_pct > 0.5:
        add_reason(f'Spot {mp_dist_pct:.1f}% above MaxPain', 'bull', 1)
    elif mp_dist_pct < -0.5:
        add_reason(f'Spot {abs(mp_dist_pct):.1f}% below MaxPain', 'bear', 1)

    if 'BULL' in delta_signal:
        add_reason('Portfolio Delta: Bullish', 'bull', 1)
    if 'BEAR' in delta_signal:
        add_reason('Portfolio Delta: Bearish', 'bear', 1)

    if 'BULL' in fmo_dir:
        add_reason('Options Flow: Bullish', 'bull', 1)
    if 'BEAR' in fmo_dir:
        add_reason('Options Flow: Bearish', 'bear', 1)

    if breadth > 60:
        add_reason(f'Breadth {breadth:.0f}% (Bullish)', 'bull', 1)
    elif breadth < 40:
        add_reason(f'Breadth {breadth:.0f}% (Bearish)', 'bear', 1)

    if put_writing > call_writing * 1.4:
        add_reason('Heavy Put Writing (PE > CE 1.4×)', 'bull', 1)
    elif call_writing > put_writing * 1.4:
        add_reason('Heavy Call Writing (CE > PE 1.4×)', 'bear', 1)

    if pcr_trend == 'rising' and pcr_oi > 1.0:
        add_reason('PCR Rising — Put protection increasing', 'bull', 1)
    if pcr_trend == 'falling' and pcr_oi < 1.0:
        add_reason('PCR Falling — Puts being shed', 'bear', 1)

    net_score = bull_score - bear_score

    # ── 3. PRIMARY STRATEGY ──────────────────────────────────────────
    def _fmt_vix():
        return f'{vix:.1f}' if vix > 0 else 'elevated'

    def _fmt_iv():
        return f'{atm_iv:.1f}%' if atm_iv > 0 else 'elevated'

    def _mp_side():
        return f'{mp_dist_pct:.1f}% {"above" if mp_dist_pct > 0 else "below"}'

    if high_vol and abs(net_score) <= 2:
        primary = {
            'name': 'Long Straddle', 'icon': '📐', 'type': 'neutral',
            'setup': f'Buy {atm_strike} CE  +  Buy {atm_strike} PE',
            'ce': {'strike': atm_strike, 'action': 'BUY', 'pos': 'ATM',
                   'note': 'Buys calls — profits if Nifty moves up strongly'},
            'pe': {'strike': atm_strike, 'action': 'BUY', 'pos': 'ATM',
                   'note': 'Buys puts — profits if Nifty moves down strongly'},
            'rationale': f'High volatility (VIX={_fmt_vix()}, IV={_fmt_iv()}) with mixed signals. '
                         f'Straddle profits from a big move either way.',
            'risk': 'Medium', 'maxLoss': 'Total premium paid (both legs)',
            'target': '≥ 1.5× premium paid on either leg',
            'entry': 'Buy at or after 9:30 AM; avoid near expiry',
            'avoid': 'Avoid if IV drops sharply after entry (vega crush)',
        }
    elif net_score >= 4:
        sell_st = atm_strike + 2 * ss
        primary = {
            'name': 'Bull Call Spread', 'icon': '🐂', 'type': 'bull',
            'setup': f'Buy {atm_strike} CE  +  Sell {sell_st} CE',
            'ce': {'strike': atm_strike, 'action': 'BUY', 'pos': 'ATM',
                   'note': 'Long CE — directional call at ATM'},
            'pe': {'strike': sell_st, 'action': 'SELL', 'pos': '+2 OTM',
                   'note': f'Short CE hedge — caps cost and upside at {sell_st}'},
            'rationale': (f'Strong bullish confluence (score {bull_score} vs {bear_score}): '
                          f'{", ".join(filter(None, [final_sig, mkt]))}. '
                          f'PCR={pcr_oi:.2f}, Spot {_mp_side()} MaxPain.'),
            'risk': 'Low-Medium', 'maxLoss': 'Net debit (spread premium only)',
            'target': f'{sell_st} strike (full spread width)',
            'entry': 'Enter on slight market dip or current levels',
            'avoid': 'Avoid if PCR drops below 0.9 or signal flips bearish',
        }
    elif net_score == 3:
        ce_st = atm_strike + ss
        primary = {
            'name': 'Long CE — OTM', 'icon': '📈', 'type': 'bull',
            'setup': f'Buy {ce_st} CE',
            'ce': {'strike': ce_st, 'action': 'BUY', 'pos': '+1 OTM',
                   'note': 'OTM call — leveraged upside with defined risk'},
            'pe': None,
            'rationale': f'Bullish tilt (score {bull_score} vs {bear_score}). PCR={pcr_oi:.2f}. OTM CE for leveraged upside participation.',
            'risk': 'Medium', 'maxLoss': 'Premium paid',
            'target': f'{ce_st + ss} (next OTM)',
            'entry': 'Buy on dip near ATM or VWAP support',
            'avoid': 'Avoid buying if ATM IV > 18% — switch to spread instead',
        }
    elif net_score >= 2:
        sell_ce = atm_strike + ss
        primary = {
            'name': 'Bull Call Spread (1-step)', 'icon': '🟢', 'type': 'bull',
            'setup': f'Buy {atm_strike} CE  +  Sell {sell_ce} CE',
            'ce': {'strike': atm_strike, 'action': 'BUY', 'pos': 'ATM',
                   'note': 'ATM call — directional'},
            'pe': {'strike': sell_ce, 'action': 'SELL', 'pos': '+1 OTM',
                   'note': 'Short CE reduces net debit'},
            'rationale': f'Mild bullish bias (score {bull_score} vs {bear_score}). Defined-risk spread with modest exposure.',
            'risk': 'Low', 'maxLoss': 'Net debit only',
            'target': f'{sell_ce} (1 step above ATM)',
            'entry': 'Current or minor pullback',
            'avoid': 'Avoid if broader market turns bearish',
        }
    elif net_score <= -4:
        sell_pe = atm_strike - 2 * ss
        primary = {
            'name': 'Bear Put Spread', 'icon': '🐻', 'type': 'bear',
            'setup': f'Buy {atm_strike} PE  +  Sell {sell_pe} PE',
            'ce': {'strike': atm_strike, 'action': 'BUY', 'pos': 'ATM',
                   'note': 'Long PE — ATM directional put'},
            'pe': {'strike': sell_pe, 'action': 'SELL', 'pos': '-2 OTM',
                   'note': f'Short put reduces cost, caps downside profit at {sell_pe}'},
            'rationale': (f'Strong bearish confluence (score {bear_score} bear vs {bull_score} bull): '
                          f'PCR={pcr_oi:.2f}. Spot {abs(mp_dist_pct):.1f}% below MaxPain.'),
            'risk': 'Low-Medium', 'maxLoss': 'Net debit (spread only)',
            'target': f'{sell_pe} (2 steps below ATM)',
            'entry': 'Enter on bounce to resistance / VWAP rejection',
            'avoid': 'Avoid if PCR rises above 1.1 or market stabilises',
        }
    elif net_score == -3:
        pe_st = atm_strike - ss
        primary = {
            'name': 'Long PE — OTM', 'icon': '📉', 'type': 'bear',
            'setup': f'Buy {pe_st} PE',
            'ce': None,
            'pe': {'strike': pe_st, 'action': 'BUY', 'pos': '-1 OTM',
                   'note': 'OTM put — leveraged downside exposure'},
            'rationale': f'Bearish tilt (score {bear_score} bear vs {bull_score} bull). PCR={pcr_oi:.2f} below neutral.',
            'risk': 'Medium', 'maxLoss': 'Premium paid',
            'target': str(pe_st - ss),
            'entry': 'Short at resistance or VWAP rejection candle',
            'avoid': 'Avoid near expiry or if VIX starts declining',
        }
    elif net_score == -2:
        sell_pe = atm_strike - ss
        primary = {
            'name': 'Bear Put Spread (1-step)', 'icon': '🔴', 'type': 'bear',
            'setup': f'Buy {atm_strike} PE  +  Sell {sell_pe} PE',
            'ce': {'strike': atm_strike, 'action': 'BUY', 'pos': 'ATM',
                   'note': 'ATM put — directional'},
            'pe': {'strike': sell_pe, 'action': 'SELL', 'pos': '-1 OTM',
                   'note': 'Short put reduces cost'},
            'rationale': f'Mild bearish tilt (score {bear_score} bear vs {bull_score} bull). Conservative spread with defined risk.',
            'risk': 'Low', 'maxLoss': 'Net debit only',
            'target': str(sell_pe),
            'entry': 'Enter on bounce to resistance',
            'avoid': 'Avoid if signal turns neutral',
        }
    elif near_mp and low_vol:
        ce_sell = atm_strike + 2 * ss
        pe_sell = atm_strike - 2 * ss
        ce_buy = atm_strike + 3 * ss
        pe_buy = atm_strike - 3 * ss
        primary = {
            'name': 'Iron Condor', 'icon': '🦅', 'type': 'neutral',
            'setup': f'Sell {ce_sell} CE / Sell {pe_sell} PE  +  Buy {ce_buy} CE / Buy {pe_buy} PE (wings)',
            'ce': {'strike': ce_sell, 'action': 'SELL', 'pos': '+2 OTM',
                   'note': f'Short CE at {ce_sell} — Collect premium with upside cap'},
            'pe': {'strike': pe_sell, 'action': 'SELL', 'pos': '-2 OTM',
                   'note': f'Short PE at {pe_sell} — Collect premium with downside floor'},
            'rationale': (f'Spot is {abs(mp_dist_pct):.1f}% from MaxPain {max_pain:.0f}. '
                          f'Low IV and bounded market ideal for iron condor premium collection.'),
            'risk': 'Low-Medium', 'maxLoss': 'Width of wings minus net credit',
            'target': 'Close at 50% of net credit collected',
            'entry': 'Enter at current levels; IV should be reasonable',
            'avoid': 'Avoid on high-VIX days or macro events',
        }
    else:
        ce_sell = atm_strike + ss
        pe_sell = atm_strike - ss
        primary = {
            'name': 'Short Strangle', 'icon': '⚖️', 'type': 'neutral',
            'setup': f'Sell {ce_sell} CE  +  Sell {pe_sell} PE',
            'ce': {'strike': ce_sell, 'action': 'SELL', 'pos': '+1 OTM',
                   'note': 'Short CE — collect time value; hedge if moves above'},
            'pe': {'strike': pe_sell, 'action': 'SELL', 'pos': '-1 OTM',
                   'note': 'Short PE — collect time value; hedge if moves below'},
            'rationale': (f'Mixed / neutral signals (score {bull_score} bull vs {bear_score} bear). '
                          f'Theta-positive strategy to collect premium in a rangebound market.'),
            'risk': 'Medium-High (undefined)',
            'maxLoss': 'Theoretically unlimited — manage actively or add wings',
            'target': '50% of net premium collected',
            'entry': 'Sell when IV is relatively elevated',
            'avoid': 'Avoid on expiry day, high-VIX sessions, or strong trending days',
        }

    ptype = primary.get('type', 'neutral')

    # ── 4. CATEGORY STRATEGIES ───────────────────────────────────────
    # Max Pain
    if max_pain <= 0:
        mp_strat = 'No MaxPain Data'
        mp_desc = 'MaxPain data not available.'
        mp_action = 'Use PCR and OI signals instead.'
    elif mp_dist_pct > 1.0:
        mp_strat = 'Sell Calls above MaxPain'
        mp_desc = (f'Spot is {mp_dist_pct:.1f}% above MaxPain {max_pain:.0f}. '
                   f'Writers lose less if Nifty drifts back to {max_pain:.0f} by expiry.')
        mp_action = f'Sell CE at {atm_strike + ss} or {atm_strike + 2 * ss}. SL above recent high.'
    elif mp_dist_pct < -1.0:
        mp_strat = 'Sell Puts below MaxPain'
        mp_desc = (f'Spot is {abs(mp_dist_pct):.1f}% below MaxPain {max_pain:.0f}. '
                   f'Gravity pulls toward MaxPain on expiry.')
        mp_action = f'Buy {atm_strike} CE targeting MaxPain ({max_pain:.0f}). SL below swing low.'
    else:
        mp_strat = 'Near MaxPain — Short Straddle/Strangle'
        mp_desc = (f'Spot is only {abs(mp_dist_pct):.1f}% from MaxPain {max_pain:.0f}. '
                   f'Market is gravitating toward expiry settlement.')
        mp_action = f'Sell ATM straddle at {atm_strike} or strangle around MaxPain. Collect theta.'

    # OI Buildup
    call_dom_ratio = call_writing / put_writing if put_writing > 0 else 1.0
    put_dom_ratio = put_writing / call_writing if call_writing > 0 else 1.0
    if call_writing > put_writing * 1.4:
        res_lbl = resistance if resistance > 0 else atm_strike + ss
        oi_strat = 'CE Writing Dominance — Resistance'
        oi_desc = (f'Call writing is {call_dom_ratio:.1f}× heavier than put writing. '
                   f'{res_lbl:.0f} acts as strong resistance.')
        oi_action = (f'Short call or bearish strangle near '
                     f'{resistance if resistance > 0 else atm_strike + 2 * ss:.0f}. '
                     f'Avoid fresh longs above resistance.')
    elif put_writing > call_writing * 1.4:
        sup_lbl = support if support > 0 else atm_strike - ss
        oi_strat = 'PE Writing Dominance — Support'
        oi_desc = (f'Put writing is {put_dom_ratio:.1f}× heavier than call writing. '
                   f'{sup_lbl:.0f} acts as strong support.')
        oi_action = (f'Buy call or bullish spread above PE support. Target: '
                     f'{resistance if resistance > 0 else atm_strike + 2 * ss:.0f}.')
    else:
        lo = support if support > 0 else atm_strike - 2 * ss
        hi = resistance if resistance > 0 else atm_strike + 2 * ss
        oi_strat = 'Balanced OI Buildup'
        oi_desc = f'CE and PE writing are roughly balanced. Market range is between {lo:.0f} and {hi:.0f}.'
        oi_action = f'Trade the range. Sell strangle with {lo:.0f} – {hi:.0f} as boundaries.'

    # PCR Strategy
    if pcr_oi > 1.4:
        pcr_strat = f'PCR Extremely Bullish ({pcr_oi:.2f})'
        pcr_desc = 'PCR > 1.4: heavy put protection signals institutional hedging — market often reverses up from here.'
        pcr_action = f'Long CE at ATM ({atm_strike}) or bull call spread. Fade extreme PCR bearish moves as reversals.'
    elif pcr_oi > 1.2:
        pcr_strat = f'PCR Bullish ({pcr_oi:.2f})'
        rising_note = ('PCR is rising, adding to bullish conviction.'
                       if pcr_trend == 'rising' else 'PCR is stable/falling — watch for reversal.')
        pcr_desc = f'PCR 1.2–1.4: puts outweigh calls — mild bullish tilt. {rising_note}'
        pcr_action = 'Bull call spread or OTM CE. Watch for PCR to sustain above 1.2.'
    elif pcr_oi < 0.7:
        pcr_strat = f'PCR Bearish ({pcr_oi:.2f})'
        pcr_desc = 'PCR < 0.7: calls heavily dominate. Put-call divergence suggests downside risk.'
        pcr_action = 'Bear put spread or OTM PE. Expiry strangle if PCR neutral and VIX < 18.'
    elif pcr_oi < 0.9:
        pcr_strat = f'PCR Mild Bearish ({pcr_oi:.2f})'
        fall_note = ('PCR is falling — deteriorating sentiment.'
                     if pcr_trend == 'falling' else 'Watch if PCR falls further below 0.8.')
        pcr_desc = f'PCR 0.7–0.9: mild bearish lean. {fall_note}'
        pcr_action = 'Reduce longs. Small OTM PE or bear spread for protection.'
    else:
        pcr_strat = f'PCR Neutral ({pcr_oi:.2f})'
        if pcr_trend == 'rising':
            trend_note = 'PCR rising — slight bullish lean.'
        elif pcr_trend == 'falling':
            trend_note = 'PCR falling — slight bearish lean.'
        else:
            trend_note = 'PCR stable.'
        pcr_desc = f'PCR 0.9–1.2: balanced market. {trend_note}'
        pcr_action = 'Iron condor or short strangle near MaxPain. Watch breakout in either direction.'

    # ── 5. ALTERNATIVE STRATEGIES ────────────────────────────────────
    alts = []
    if ptype == 'bull':
        alts.append({
            'name': 'Covered Call',
            'setup': f'Sell {atm_strike + ss} CE against existing long position',
            'why': 'If you hold underlying/futures — earn premium while limiting upside. Works well when rally seems limited.',
        })
        alts.append({
            'name': 'Long CE + Bear Put Spread Hedge',
            'setup': f'Buy {atm_strike} CE  +  Buy {atm_strike} PE / Sell {atm_strike - ss} PE',
            'why': 'Bullish with downside hedge in case signal reverses. More expensive but protected.',
        })
    elif ptype == 'bear':
        alts.append({
            'name': 'Protective Put',
            'setup': f'Buy {atm_strike - ss} PE as portfolio hedge',
            'why': 'If holding stock positions — hedge downside without exiting positions. Pays off if market drops.',
        })
        alts.append({
            'name': 'Bear Call Spread',
            'setup': f'Sell {atm_strike} CE  +  Buy {atm_strike + ss} CE',
            'why': 'Collect premium on rallies while limiting risk. Profits if market stays below sold strike.',
        })
    else:
        alts.append({
            'name': 'Long Straddle (if pre-event)',
            'setup': f'Buy {atm_strike} CE + PE both',
            'why': 'If a big event (RBI, earnings, macro print) is ahead — straddle profits from the volatility spike regardless of direction.',
        })
        alts.append({
            'name': 'Calendar Spread',
            'setup': f'Sell near-expiry {atm_strike} CE + Buy next-week {atm_strike} CE',
            'why': 'Earn time decay differential between near and far expiry when spot stays near current levels.',
        })

    # ── 6. GO/NO-GO CHECKLIST ────────────────────────────────────────
    checks = [
        {'label': 'Signal confidence ≥ 50%',
         'pass': confidence >= 50,
         'note': f'{confidence:.0f}% confidence'},
        {'label': 'Market breadth aligned',
         'pass': (ptype == 'bull' and breadth >= 45) or
                 (ptype == 'bear' and breadth <= 55) or ptype == 'neutral',
         'note': f'Breadth: {breadth:.0f}%'},
        {'label': 'PCR supports direction',
         'pass': (ptype == 'bull' and pcr_oi >= 0.9) or
                 (ptype == 'bear' and pcr_oi <= 1.1) or ptype == 'neutral',
         'note': f'PCR {pcr_oi:.2f}'},
        {'label': 'VIX appropriate for strategy',
         'pass': (ptype == 'neutral' and not high_vol) or
                 ('Straddle' in primary.get('name', '') and high_vol) or
                 (ptype != 'neutral'),
         'note': f'VIX: {vix:.1f}' if vix > 0 else 'VIX: N/A'},
        {'label': 'Spot vs MaxPain direction matches',
         'pass': max_pain <= 0 or
                 (ptype == 'bull' and mp_dist_pct >= -0.3) or
                 (ptype == 'bear' and mp_dist_pct <= 0.3) or ptype == 'neutral',
         'note': f'MP dist: {mp_dist_pct:.1f}%' if max_pain > 0 else 'MP dist: N/A'},
        {'label': 'IV skew acceptable',
         'pass': abs(iv_skew) < 15,
         'note': f'IV skew: {iv_skew:.1f}%'},
        {'label': 'OI buildup direction aligns',
         'pass': (ptype == 'bull' and 'BEAR' not in bld_sig) or
                 (ptype == 'bear' and 'BULL' not in bld_sig) or ptype == 'neutral',
         'note': bld_sig or 'N/A'},
        {'label': 'Net score ≥ 2 (meaningful edge)',
         'pass': abs(net_score) >= 2,
         'note': f'Net score: {net_score}'},
    ]
    go_count = sum(1 for c in checks if c['pass'])
    go_ratio = go_count / len(checks)
    if go_ratio >= 0.75:
        go_status = 'go'
        go_verdict = f'GO — {go_count}/{len(checks)} checks pass'
    elif go_ratio >= 0.5:
        go_status = 'caution'
        go_verdict = f'CAUTION — {go_count}/{len(checks)} checks pass (reduce size)'
    else:
        go_status = 'nogo'
        go_verdict = f'NO-GO — only {go_count}/{len(checks)} checks pass'

    # ── 7. STRIKE MATRIX ─────────────────────────────────────────────
    ce_leg = primary.get('ce')
    pe_leg = primary.get('pe')
    strike_matrix = []
    for i in range(-3, 4):
        s = atm_strike + i * strike_step
        ce_oi_v = 0.0
        pe_oi_v = 0.0
        ce_iv_v = 0.0
        pe_iv_v = 0.0
        for row in chain_rows:
            rs = float((row or {}).get('strike') or
                       (row or {}).get('strikePrice') or 0)
            if rs == s:
                ce_data = row.get('CE') or {}
                pe_data = row.get('PE') or {}
                ce_oi_v = float(ce_data.get('openInterest') or row.get('ce_oi') or 0)
                pe_oi_v = float(pe_data.get('openInterest') or row.get('pe_oi') or 0)
                ce_iv_v = float(ce_data.get('impliedVolatility') or row.get('ce_iv') or 0)
                pe_iv_v = float(pe_data.get('impliedVolatility') or row.get('pe_iv') or 0)
                break
        sig_parts = []
        if i == 0:
            sig_parts.append('🎯 ATM')
        if resistance > 0 and s == resistance:
            sig_parts.append('🔴 Resistance')
        if support > 0 and s == support:
            sig_parts.append('🟢 Support')
        if max_pain > 0 and s == max_pain:
            sig_parts.append('🧭 MaxPain')
        if ce_leg and ce_leg.get('strike') == s:
            sig_parts.append('⚔️ CE leg')
        if pe_leg and pe_leg.get('strike') == s:
            sig_parts.append('⚔️ PE leg')
        strike_matrix.append({
            'strike': s,
            'offset': i,
            'ce_oi': ce_oi_v,
            'pe_oi': pe_oi_v,
            'ce_iv': ce_iv_v,
            'pe_iv': pe_iv_v,
            'label': ' + '.join(sig_parts),
        })

    # ── RETURN ────────────────────────────────────────────────────────
    return {
        'context': {
            'spot': spot,
            'max_pain': max_pain,
            'mp_dist_pct': round(mp_dist_pct, 2),
            'pcr_oi': round(pcr_oi, 3),
            'pcr_trend': pcr_trend,
            'atm_iv': round(atm_iv, 2),
            'high_vol': high_vol,
            'low_vol': low_vol,
            'final_sig': final_sig,
            'mkt_trend': mkt,
            'breadth': round(breadth, 1),
            'atm_strike': atm_strike,
            'strike_step': strike_step,
            'net_score': net_score,
            'bull_score': bull_score,
            'bear_score': bear_score,
        },
        'reasons': reasons,
        'primary': primary,
        'categories': {
            'max_pain': {'strat': mp_strat, 'desc': mp_desc, 'action': mp_action},
            'oi':       {'strat': oi_strat, 'desc': oi_desc, 'action': oi_action},
            'pcr':      {'strat': pcr_strat, 'desc': pcr_desc, 'action': pcr_action},
        },
        'alternatives': alts,
        'checks': checks,
        'go_count': go_count,
        'go_ratio': round(go_ratio, 3),
        'go_status': go_status,
        'go_verdict': go_verdict,
        'strike_matrix': strike_matrix,
    }
