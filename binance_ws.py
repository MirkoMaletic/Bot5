
import json
import threading
import websocket
from scalping_engine import analyze_candle
from telegram import Bot

SYMBOL = "ethusdt"
INTERVAL = "1m"  # ili "5m"
WS_URL = f"wss://stream.binance.com:9443/ws/{SYMBOL}@kline_{INTERVAL}"

def start_ws(bot, chat_id, min_scs_threshold, live_trading_flag, scalping_active_flag):
    def on_message(ws, message):
        if not scalping_active_flag[0]:
            return

        data = json.loads(message)
        kline = data['k']
        if not kline['x']:  # skip ako sveća nije zatvorena
            return

        candle = {
            'open': float(kline['o']),
            'high': float(kline['h']),
            'low': float(kline['l']),
            'close': float(kline['c']),
            'volume': float(kline['v']),
            'avg_volume': 1500,  # placeholder
            'ema': float(kline['c']),  # za sada isto kao close
            'vwap': float(kline['c'])  # za sada isto kao close
        }

        signal, scs = analyze_candle(candle)
        if signal and scs >= min_scs_threshold[0]:
            msg = f"⚡ SCALPING SIGNAL ({signal})\n✅ SCS: {scs}\n💵 Cena: {candle['close']:.2f}"
            bot.send_message(chat_id=chat_id, text=msg)

            if live_trading_flag[0]:
                print(f"ULAZ u {signal} poziciju na ceni {candle['close']:.2f} sa SCS={scs}")

    def on_error(ws, error):
        print("WebSocket greška:", error)

    def on_close(ws, close_status_code, close_msg):
        print("WebSocket zatvoren")

    def on_open(ws):
        print("✅ WebSocket konekcija otvorena")

    ws = websocket.WebSocketApp(WS_URL, on_open=on_open, on_message=on_message,
                                 on_error=on_error, on_close=on_close)
    threading.Thread(target=ws.run_forever, daemon=True).start()
