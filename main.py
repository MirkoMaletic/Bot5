import analyze_trades
import dual_ws
import scalping_engine

import sys

try:
except ImportError:


import os
import json
import time
import threading
import pandas as pd
from datetime import datetime
from flask import Flask, request
from binance.client import Client
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler
from dotenv import load_dotenv
import requests

load_dotenv()
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET = os.getenv("BINANCE_SECRET")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

bot = Bot(token=TELEGRAM_TOKEN)
client = Client(BINANCE_API_KEY, BINANCE_SECRET)
app = Flask(__name__)
dispatcher = Dispatcher(bot, None, use_context=True)

STATE_FILE = "state.json"
LOG_FILE = "trades_log.csv"
DAILY_REPORT_HOUR = 22

state = {
    "live": True,
    "paused": False,
    "scalp_active": False,
    "positions": []
}

if os.path.exists(STATE_FILE):
    with open(STATE_FILE, 'r') as f:
        state.update(json.load(f))

def save_state():
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=4)

def send(msg):
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
        print("Telegram error:", e)

@app.route("/")
def home():
    return "Bot je aktivan!", 200

@app.route("/oraclebot", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "OK", 200

def start_live(update, context):
    state["live"] = True
    save_state()
    update.message.reply_text("✅ Live režim uključen.")

def pause(update, context):
    state["paused"] = True
    save_state()
    update.message.reply_text("⏸ Bot pauziran.")

def resume(update, context):
    state["paused"] = False
    save_state()
    update.message.reply_text("▶ Bot nastavlja rad.")

def status(update, context):
    update.message.reply_text(f"Live: {state['live']} | Paused: {state['paused']} | Scalping: {state['scalp_active']} | Pozicija: {len(state['positions'])}")

def scalp_on(update, context):
    state["scalp_active"] = True
    save_state()
    update.message.reply_text("⚡ Scalping uključen.")

def scalp_off(update, context):
    state["scalp_active"] = False
    save_state()
    update.message.reply_text("🔕 Scalping isključen.")

def daily_report():
    while True:
        now = datetime.utcnow()
        if now.hour == DAILY_REPORT_HOUR and now.minute < 2:
                if os.path.exists(LOG_FILE):
                    df = pd.read_csv(LOG_FILE)
                    df["timestamp"] = pd.to_datetime(df["timestamp"])
                    df_today = df[df["timestamp"].dt.date == now.date()]
                    profit = df_today["pnl"].sum() if "pnl" in df_today.columns else 0
                    wins = (df_today["pnl"] > 0).sum() if "pnl" in df_today.columns else 0
                    losses = (df_today["pnl"] < 0).sum() if "pnl" in df_today.columns else 0
                    send(f"🧾 Dnevni izveštaj\n📈 Ulaza: {len(df_today)}\n✅ Dobitaka: {wins} ❌ Gubitaka: {losses}\n💰 PnL: {profit:.2f} USDT")
                else:
                    send("🧾 Nema podataka za današnji dan.")
                print("Report error:", e)
    time.sleep(120)
    time.sleep(30)

def keep_alive():
    while True:
            requests.get(WEBHOOK_URL)
            print("Ping error:", e)
    time.sleep(600)

dispatcher.add_handler(CommandHandler("start_live", start_live))
dispatcher.add_handler(CommandHandler("pause", pause))
dispatcher.add_handler(CommandHandler("resume", resume))
dispatcher.add_handler(CommandHandler("status", status))
dispatcher.add_handler(CommandHandler("scalp_on", scalp_on))
dispatcher.add_handler(CommandHandler("scalp_off", scalp_off))

threading.Thread(target=daily_report, daemon=True).start()
threading.Thread(target=keep_alive, daemon=True).start()

if __name__ == "__main__":
    bot.delete_webhook()
    bot.set_webhook(WEBHOOK_URL)
    app.run(host="0.0.0.0", port=443)

# === Scalping komandne funkcije ===

def start_scalping(update, context):
    global scalping_active
    scalping_active = True
    update.message.reply_text("🚀 Scalping bot (1m/5m) je pokrenut.")
    dual_ws.start_dual_ws(bot, TELEGRAM_CHAT_ID, [min_scs_threshold], [LIVE_TRADING], [scalping_active])

def pause_scalping(update, context):
    global scalping_active
    scalping_active = False
    update.message.reply_text("⏸ Scalping bot je pauziran.")

def status_scalping(update, context):
    status = "Aktivan ✅" if scalping_active else "Neaktivan ❌"
    update.message.reply_text(f"📊 Status scalping modula (1m/5m): {status}")

def stop_scalping(update, context):
    global scalping_active
    scalping_active = False
    update.message.reply_text("🛑 Scalping bot je isključen.")


# === Registracija scalping komandi ===

dispatcher.add_handler(CommandHandler('start_scalping', start_scalping))
dispatcher.add_handler(CommandHandler('pause_scalping', pause_scalping))
dispatcher.add_handler(CommandHandler('status_scalping', status_scalping))
dispatcher.add_handler(CommandHandler('stop_scalping', stop_scalping))

# === Komanda za podešavanje SCS praga ===

min_scs_threshold = 60  # Defaultni prag za wick-entry

def set_scs_min(update, context):
    global min_scs_threshold
    try:
        value = int(context.args[0])
        if 0 <= value <= 100:
            min_scs_threshold = value
            update.message.reply_text(f"✅ Minimalni SCS prag za scalping postavljen na {value}")
        else:
            update.message.reply_text("⚠ Unesite broj između 0 i 100.")
    except (IndexError, ValueError):
        update.message.reply_text("❗ Upotreba: /scs_min 65")


dispatcher.add_handler(CommandHandler('scs_min', set_scs_min))


# def mock_candle_stream():  # zamenjeno sa WebSocket varijantom
    import random
    import time

    while scalping_active:
        candle = {
            'open': random.uniform(3400, 3500),
            'high': random.uniform(3500, 3550),
            'low': random.uniform(3350, 3400),
            'close': random.uniform(3400, 3500),
            'volume': random.uniform(1000, 2000),
            'avg_volume': 1200,
            'ema': 3425,
            'vwap': 3430
        }
        signal, scs = scalping_engine.analyze_candle(candle)
        if signal and scs >= min_scs_threshold:
            msg = f"⚡ SCALPING SIGNAL ({signal})\n✅ SCS: {scs}\n💵 Cena: {candle['close']:.2f}"
            bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)

            if LIVE_TRADING:
                # ovde bi bila funkcija za entry, sada samo print
                print(f"ULAZ u {signal} poziciju na ceni {candle['close']:.2f} sa SCS={scs}")

        time.sleep(10)


# === Dnevni izveštaj u 22h ===

import threading
import time
import analyze_trades

last_report_day = None

def daily_report_scheduler():
    global last_report_day
    while True:
        now = datetime.utcnow()
        if now.hour == 22 and (last_report_day != now.date()):
            analyze_trades.analyze_trades(telegram=True)
            last_report_day = now.date()
        time.sleep(60)


threading.Thread(target=daily_report_scheduler, daemon=True).start()