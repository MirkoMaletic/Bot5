
import csv
from datetime import datetime

TRADE_LOG = "trades_log.csv"

# Parametri za simulaciju
TP_PERCENT = 0.008   # +0.8%
SL_PERCENT = 0.004   # -0.4%
TRAIL_START = 0.006  # +0.6%
TRAIL_STEP = 0.002   # pomeranje trailing SL

# Aktivna pozicija (samo jedna u ovom modu)
active_trade = None

def start_trade(timestamp, direction, entry_price, scs):
    global active_trade
    active_trade = {
        "timestamp": timestamp,
        "direction": direction,
        "entry_price": entry_price,
        "high": entry_price,
        "low": entry_price,
        "scs": scs
    }

def update_price(candle_close):
    global active_trade
    if not active_trade:
        return None

    direction = active_trade["direction"]
    entry = active_trade["entry_price"]
    scs = active_trade["scs"]

    if direction == "LONG":
        active_trade["high"] = max(active_trade["high"], candle_close)
        active_trade["low"] = min(active_trade["low"], candle_close)

        if candle_close >= entry * (1 + TP_PERCENT):
            log_trade("TP", candle_close, scs, "fixed_tp")
            active_trade = None
        elif candle_close <= entry * (1 - SL_PERCENT):
            log_trade("SL", candle_close, scs, "fixed_sl")
            active_trade = None
        elif active_trade["high"] >= entry * (1 + TRAIL_START):
            trail_sl = active_trade["high"] - (entry * TRAIL_STEP)
            if candle_close <= trail_sl:
                log_trade("TRAIL_EXIT", candle_close, scs, "trailing")
                active_trade = None

    elif direction == "SHORT":
        active_trade["low"] = min(active_trade["low"], candle_close)
        active_trade["high"] = max(active_trade["high"], candle_close)

        if candle_close <= entry * (1 - TP_PERCENT):
            log_trade("TP", candle_close, scs, "fixed_tp")
            active_trade = None
        elif candle_close >= entry * (1 + SL_PERCENT):
            log_trade("SL", candle_close, scs, "fixed_sl")
            active_trade = None
        elif active_trade["low"] <= entry * (1 - TRAIL_START):
            trail_sl = active_trade["low"] + (entry * TRAIL_STEP)
            if candle_close >= trail_sl:
                log_trade("TRAIL_EXIT", candle_close, scs, "trailing")
                active_trade = None

def log_trade(result, exit_price, scs, exit_type):
    with open(TRADE_LOG, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
            active_trade["direction"],
            round(active_trade["entry_price"], 2),
            round(exit_price, 2),
            result,
            scs,
            exit_type
        ])
