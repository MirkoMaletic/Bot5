
import json
import threading
import websocket
from scalping_engine import analyze_candle
import trade_simulator

SYMBOL = "ethusdt"
CONFIRM_DELAY = 60  # sekundi za čekanje potvrde (1m)

last_5m_signal = {"type": None, "scs": 0, "price": 0}
awaiting_confirmation = [False]

def start_dual_ws(bot, chat_id, min_scs_threshold, live_trading_flag, scalping_active_flag):
    def on_message_5m(ws, message):
        if not scalping_active_flag[0]:
            return

        data = json.loads(message)
        kline = data['k']
        if not kline['x']:
            return  # sveća još nije zatvorena

        candle = {
            'open': float(kline['o']),
            'high': float(kline['h']),
            'low': float(kline['l']),
            'close': float(kline['c']),
            'volume': float(kline['v']),
            'avg_volume': 1500,
            'ema': float(kline['c']),
            'vwap': float(kline['c'])
        }

        signal, scs = analyze_candle(candle)
        if signal and scs >= min_scs_threshold[0]:
            last_5m_signal.update({
                "type": signal,
                "scs": scs,
                "price": candle['close']
            })
            awaiting_confirmation[0] = True
            bot.send_message(chat_id=chat_id, text=f"⚡ 5M SIGNAL: {signal} (SCS {scs}) — čekamo 1m potvrdu...")

    def on_message_1m(ws, message):
        if not (scalping_active_flag[0] and awaiting_confirmation[0]):
            return

        data = json.loads(message)
        kline = data['k']
        if not kline['x']:
            return

        open_price = float(kline['o'])
        close_price = float(kline['c'])
        volume = float(kline['v'])

        if last_5m_signal["type"] == "LONG" and close_price > open_price:
            confirm = True
        elif last_5m_signal["type"] == "SHORT" and close_price < open_price:
            confirm = True
        else:
            confirm = False

        if confirm:
            msg = f"✅ Potvrđen ulaz ({last_5m_signal['type']}) na 1m\nCena: {close_price:.2f}\nSCS: {last_5m_signal['scs']}"
            bot.send_message(chat_id=chat_id, text=msg)

            if live_trading_flag[0]:
                print(f"ULAZ u {last_5m_signal['type']} — Cena: {close_price:.2f}, SCS: {last_5m_signal['scs']}")
            trade_simulator.start_trade(datetime.utcnow().strftime('%Y-%m-%d %H:%M'), last_5m_signal['type'], close_price, last_5m_signal['scs'])
            awaiting_confirmation[0] = False

    def start_ws_thread(url, callback):
        ws = websocket.WebSocketApp(url, on_message=callback)
        threading.Thread(target=ws.run_forever, daemon=True).start()

    url_5m = f"wss://stream.binance.com:9443/ws/{SYMBOL}@kline_5m"
    url_1m = f"wss://stream.binance.com:9443/ws/{SYMBOL}@kline_1m"

    start_ws_thread(url_5m, on_message_5m)
    start_ws_thread(url_1m, on_message_1m)
