import ccxt
import pandas as pd
import ta
import requests
import os
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
TIMEFRAME = "5m"

PAIRS = {
    "BTC/USD": "BTC/USDT",
    "EUR/GBP": "EURGBP",
    "EUR/USD": "EURUSD",
    "GBP/USD": "GBPUSD",
    "GBP/EUR": "GBPEUR",
}

exchange = ccxt.binance()

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")

def get_signal(symbol):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, TIMEFRAME, limit=100)
        df = pd.DataFrame(ohlcv, columns=['time','open','high','low','close','volume'])
        
        df['ema_fast'] = ta.trend.EMAIndicator(df['close'], window=9).ema_indicator()
        df['ema_slow'] = ta.trend.EMAIndicator(df['close'], window=21).ema_indicator()
        df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
        
        last = df.iloc[-1]
        prev = df.iloc[-2]
        
        if prev['ema_fast'] <= prev['ema_slow'] and last['ema_fast'] > last['ema_slow'] and last['rsi'] < 55:
            return "BUY", last['close'], last['rsi']
        elif prev['ema_fast'] >= prev['ema_slow'] and last['ema_fast'] < last['ema_slow'] and last['rsi'] > 45:
            return "SELL", last['close'], last['rsi']
        return None, None, None
    except Exception as e:
        print(f"Error {symbol}: {e}")
        return None, None, None

def check_all_pairs():
    signals_found = []
    for display_name, binance_symbol in PAIRS.items():
        signal, price, rsi = get_signal(binance_symbol)
        if signal:
            signals_found.append({
                'pair': display_name,
                'signal': signal,
                'price': price,
                'rsi': rsi
            })
    
    if signals_found:
        msg = "📡 <b>5M SIGNALS</b>\n━━━━━━━━━━━━━━━\n"
        for s in signals_found:
            emoji = "🟢" if s['signal'] == "BUY" else "🔴"
            msg += (f"{emoji} <b>{s['pair']}</b> → {s['signal']}\n"
                    f"   Price: {s['price']}\n"
                    f"   RSI: {s['rsi']:.1f}\n"
                    f"   Expiry: 5 min\n\n")
        msg += f"🕐 {datetime.utcnow().strftime('%H:%M')} UTC"
        send_telegram(msg)
        print(f"✅ {len(signals_found)} signals sent")
    else:
        print("No signals found")

if __name__ == "__main__":
    check_all_pairs()
