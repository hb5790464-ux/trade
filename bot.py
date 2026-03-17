import logging
import sys
import yfinance as yf
import pandas as pd
import numpy as np
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update

# ========== DEBUG SETUP ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

print("=" * 50)
print("🔍 STOCK ANALYSIS BOT - FINAL WORKING VERSION")
print("=" * 50)

# ========== YOUR TOKEN ==========
TOKEN = "PASTE_YOUR_TOKEN_HERE"

# ========== BUILD BOT ==========
app = ApplicationBuilder().token(TOKEN).build()

# ========== ANALYZE FUNCTION ==========
async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a stock symbol.\nExample: /analyze RELIANCE"
            )
            return
        
        stock_input = context.args[0].upper()
        stock_nse = stock_input if stock_input.endswith(".NS") else stock_input + ".NS"

        await update.message.reply_text(f"🔄 Analyzing {stock_input}... Please wait")

        # 🔥 Robust data fetch (Railway fix)
        data = None

        try:
            data = yf.download(stock_nse, period="5d", interval="1d", progress=False)
        except:
            pass

        if data is None or data.empty:
            try:
                data = yf.download(stock_nse, period="1mo", interval="1d", progress=False)
            except:
                pass

        if data is None or data.empty:
            await update.message.reply_text(f"❌ No data found for {stock_input}")
            return

        # Extract data
        close_series = data['Close']
        volume_series = data['Volume']

        latest_close = float(close_series.iloc[-1])
        latest_volume = int(volume_series.iloc[-1])

        # Indicators
        ema20 = close_series.ewm(span=20, adjust=False).mean().iloc[-1]
        ema50 = close_series.ewm(span=50, adjust=False).mean().iloc[-1]

        delta = close_series.diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi_series = 100 - (100 / (1 + rs))
        latest_rsi = float(rsi_series.iloc[-1]) if not pd.isna(rsi_series.iloc[-1]) else 50

        # Trend
        trend = "Bullish 📈" if ema20 > ema50 else "Bearish 📉"

        # Levels
        buy_above = round(latest_close * 1.01, 2)
        stop_loss = round(latest_close * 0.97, 2)
        target = round(latest_close * 1.05, 2)

        # RSI signal
        if latest_rsi < 30:
            rsi_signal = "🟢 OVERSOLD - Buy"
            rsi_emoji = "🟢"
        elif latest_rsi > 70:
            rsi_signal = "🔴 OVERBOUGHT - Sell"
            rsi_emoji = "🔴"
        else:
            rsi_signal = "⚪ NEUTRAL"
            rsi_emoji = "⚪"

        # Volume
        avg_volume = volume_series.rolling(window=20).mean().iloc[-1]
        if latest_volume > avg_volume * 1.5:
            volume_signal = "🔥 HIGH VOLUME"
        elif latest_volume < avg_volume * 0.5:
            volume_signal = "💤 LOW VOLUME"
        else:
            volume_signal = "📊 NORMAL"

        # Message
        msg = f"""
📊 *{stock_input} STOCK ANALYSIS*

━━━━━━━━━━━━━━━━━━━━━
💰 *Price:* ₹{latest_close:.2f}
📈 *Trend:* {trend}

📌 *Buy Above:* ₹{buy_above}
🛑 *Stop Loss:* ₹{stop_loss}
🎯 *Target:* ₹{target}

━━━━━━━━━━━━━━━━━━━━━
📊 *RSI:* {latest_rsi:.1f} {rsi_emoji}
_{rsi_signal}_

📈 *Volume:* {latest_volume:,}
_{volume_signal}_

━━━━━━━━━━━━━━━━━━━━━
📊 *EMA20:* ₹{ema20:.2f}
📉 *EMA50:* ₹{ema50:.2f}
━━━━━━━━━━━━━━━━━━━━━

⚠️ *Disclaimer:* Educational only
"""

        await update.message.reply_text(msg, parse_mode='Markdown')

    except Exception as e:
        print(f"❌ Error: {e}")
        await update.message.reply_text("❌ Error occurred")

# ========== START ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 *Stock Bot Ready*\n\nUse:\n/analyze RELIANCE",
        parse_mode='Markdown'
    )

# ========== HANDLERS ==========
app.add_handler(CommandHandler("analyze", analyze))
app.add_handler(CommandHandler("start", start))

# ========== RUN ==========
if __name__ == "__main__":
    app.run_polling()
