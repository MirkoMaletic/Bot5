
def analyze_candle(candle):
    '''
    candle: dict sa ključevima - open, high, low, close, volume, ema, vwap
    Vraća: (signal_tip, SCS_score)
    '''

    open_price = candle['open']
    high = candle['high']
    low = candle['low']
    close = candle['close']
    volume = candle['volume']
    ema = candle.get('ema', None)
    vwap = candle.get('vwap', None)

    body = abs(close - open_price)
    upper_wick = high - max(open_price, close)
    lower_wick = min(open_price, close) - low

    wick_score = 0
    if lower_wick > body * 1.5:
        wick_score = 10
    if upper_wick > body * 1.5:
        wick_score = 10

    rejection_score = 0
    if ema and close > ema and low <= ema:
        rejection_score += 10
    if vwap and close > vwap and low <= vwap:
        rejection_score += 5

    pattern_score = 0
    if close > open_price and lower_wick > body:
        pattern_score = 10  # bullish hammer
    elif close < open_price and upper_wick > body:
        pattern_score = 10  # bearish inverted hammer

    trend_score = 5 if ema and ema < close else 0

    volume_score = 5 if volume > candle.get('avg_volume', 0) * 1.5 else 0

    total_scs = wick_score + rejection_score + pattern_score + trend_score + volume_score

    if close > open_price and lower_wick > body * 1.2:
        return ("LONG", total_scs)
    elif close < open_price and upper_wick > body * 1.2:
        return ("SHORT", total_scs)
    else:
        return (None, total_scs)
