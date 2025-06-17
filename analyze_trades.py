
import pandas as pd
from datetime import datetime
import os
from telegram import Bot

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def summarize_section(df, header):
    lines = [f"\n{header}"]
    lines.append(f"Ukupno trejdova: {len(df)}")
    win_count = len(df[df['result'].str.contains('TP|TRAIL', case=False)])
    lose_count = len(df[df['result'].str.contains('SL', case=False)])
    lines.append(f"✅ Dobitnih: {win_count} | ❌ Gubitnih: {lose_count}")

    avg_scs_win = round(df[df['result'].str.contains('TP|TRAIL')]['scs'].mean(), 2) if win_count else 0
    avg_scs_loss = round(df[df['result'].str.contains('SL')]['scs'].mean(), 2) if lose_count else 0
    lines.append(f"📈 Prosečan SCS (TP): {avg_scs_win} | 📉 SCS (SL): {avg_scs_loss}")

    lines.append("\n🧪 Efikasnost po izlazu:")
    for etype in df['exit_type'].unique():
        subset = df[df['exit_type'] == etype]
        total = len(subset)
        wins = len(subset[subset['result'].str.contains('TP|TRAIL')])
        rate = round(wins / total * 100, 1) if total > 0 else 0
        lines.append(f" - {etype}: {wins}/{total} ({rate}%)")

    lines.append("\n📊 SCS raspodela:")
    zones = [(55, 64), (65, 74), (75, 84), (85, 100)]
    for low, high in zones:
        z = df[(df['scs'] >= low) & (df['scs'] <= high)]
        wins = len(z[z['result'].str.contains('TP|TRAIL')])
        rate = round(wins / len(z) * 100, 1) if len(z) > 0 else 0
        lines.append(f" - SCS {low}-{high}: {len(z)} trejdova, uspešnost {rate}%")

    return lines

def analyze_trades(log_path="trades_log.csv", telegram=False):
    try:
        df = pd.read_csv(log_path, names=[
            "timestamp", "direction", "entry_price", "exit_price", "result", "scs", "exit_type"
        ])
    except FileNotFoundError:
        print("⚠ trades_log.csv nije pronađen.")
        return

    if df.empty:
        print("⚠ trades_log.csv je prazan.")
        return

    report_lines = [f"📊 Dnevni izveštaj ({datetime.utcnow().strftime('%Y-%m-%d')} UTC)"]

    swing_df = df[df["exit_type"] == "swing"]
    scalp_df = df[df["exit_type"] != "swing"]

    if not swing_df.empty:
        report_lines += summarize_section(swing_df, "🔷 SWING (1h/4h)")

    if not scalp_df.empty:
        report_lines += summarize_section(scalp_df, "🔹 SCALPING (5m/1m)")

    report = "\n".join(report_lines)
    print(report)

    if telegram and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        try:
            bot = Bot(token=TELEGRAM_TOKEN)
            bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=report)
        except Exception as e:
            print("❌ Greška pri slanju u Telegram:", e)

if __name__ == "__main__":
    analyze_trades(telegram=True)
