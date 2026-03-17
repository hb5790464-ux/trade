import logging
import sys
import yfinance as yf
import pandas as pd
import numpy as np
import ta
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update

# ========== DEBUG SETUP ==========
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

print("=" * 50)
print("🔍 STOCK ANALYSIS BOT - FINAL VERSION")
print("=" * 50)

# ========== YOUR TOKEN ==========
# 🔴 REPLACE WITH YOUR REAL TOKEN FROM @BotFather
TOKEN = "8362825548:AAHzzPBDtOmW8ou7GHz1zLK1_Ymg4RTbYgs"  # <-- CHANGE THIS!

print(f"\n📌 Token length: {len(TOKEN)} characters")
print(f"📌 Token has colon: {'✅ YES' if ':' in TOKEN else '❌ NO'}")

# ========== BUILD BOT ==========
print(f"\n🔄 Building bot...")
try:
    app = ApplicationBuilder().token(TOKEN).build()
    print("✅ Bot built successfully!")
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

# ========== SIMPLIFIED ANALYZE FUNCTION ==========
async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Simplified stock analysis function"""
    print(f"\n{'='*40}")
    print(f"📩 /analyze received")
    print(f"{'='*40}")
    
    try:
        # Check if symbol provided
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a stock symbol.\n"
                "Example: /analyze RELIANCE"
            )
            return
        
        # Get stock symbol
        stock_input = context.args[0].upper()
        stock_nse = stock_input + ".NS"
        
        print(f"🔍 Stock: {stock_nse}")
        await update.message.reply_text(f"🔄 Analyzing {stock_input}... Please wait")
        
        # Download data
        print("📥 Downloading data...")
        data = yf.download(stock_nse, period="1mo", interval="1d", progress=False)
        
        if data.empty:
            await update.message.reply_text(f"❌ No data found for {stock_input}")
            return
            
        print(f"✅ Downloaded {len(data)} days")
        
        # Get the latest data - SIMPLIFIED APPROACH
        try:
            # Get close price (always the first column if multi-index)
            if isinstance(data['Close'], pd.DataFrame):
                # If it's a DataFrame, take the first column
                close_series = data['Close'].iloc[:, 0]
                volume_series = data['Volume'].iloc[:, 0]
            else:
                # If it's already a Series
                close_series = data['Close']
                volume_series = data['Volume']
            
            # Get latest values
            latest_close = float(close_series.iloc[-1])
            latest_volume = int(volume_series.iloc[-1])
            
            print(f"💰 Price: ₹{latest_close:.2f}")
            print(f"📊 Volume: {latest_volume}")
            
        except Exception as e:
            print(f"❌ Data extraction error: {e}")
            await update.message.reply_text("❌ Error reading stock data")
            return
        
        # Calculate indicators using the series
        try:
            # Simple moving averages
            ema20 = close_series.ewm(span=20, adjust=False).mean().iloc[-1]
            ema50 = close_series.ewm(span=50, adjust=False).mean().iloc[-1]
            
            # Simple RSI calculation
            delta = close_series.diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi_series = 100 - (100 / (1 + rs))
            latest_rsi = float(rsi_series.iloc[-1]) if not pd.isna(rsi_series.iloc[-1]) else 50
            
            print(f"📈 EMA20: ₹{ema20:.2f}")
            print(f"📉 EMA50: ₹{ema50:.2f}")
            print(f"📊 RSI: {latest_rsi:.2f}")
            
        except Exception as e:
            print(f"❌ Indicator error: {e}")
            ema20 = latest_close
            ema50 = latest_close
            latest_rsi = 50
        
        # Determine trend
        if ema20 > ema50:
            trend = "Bullish 📈"
        else:
            trend = "Bearish 📉"
        
        # Calculate levels
        buy_above = round(latest_close * 1.01, 2)
        stop_loss = round(latest_close * 0.97, 2)
        target = round(latest_close * 1.05, 2)
        
        # RSI interpretation
        if latest_rsi < 30:
            rsi_signal = "🟢 OVERSOLD - Buy Signal"
            rsi_emoji = "🟢"
        elif latest_rsi > 70:
            rsi_signal = "🔴 OVERBOUGHT - Sell Signal"
            rsi_emoji = "🔴"
        else:
            rsi_signal = "⚪ NEUTRAL"
            rsi_emoji = "⚪"
        
        # Volume analysis
        avg_volume = volume_series.rolling(window=20).mean().iloc[-1]
        if latest_volume > avg_volume * 1.5:
            volume_signal = "🔥 HIGH VOLUME"
        elif latest_volume < avg_volume * 0.5:
            volume_signal = "💤 LOW VOLUME"
        else:
            volume_signal = "📊 NORMAL VOLUME"
        
        # Create message
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

⚠️ *Disclaimer:* Educational purpose only
"""
        
        await update.message.reply_text(msg, parse_mode='Markdown')
        print("✅ Response sent!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        await update.message.reply_text("❌ Sorry, something went wrong. Please try again.")

# ========== START COMMAND ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    welcome_msg = """
🚀 *Stock Analysis Bot*

I analyze Indian stocks using RSI and Volume.

*Commands:*
🔍 /analyze SYMBOL - Analyze a stock
   Example: `/analyze RELIANCE`
   Example: `/analyze TCS`

*Features:*
• RSI (Relative Strength Index)
• EMA Trend Analysis
• Volume Analysis
• Buy/Sell Levels

Type /analyze RELIANCE to start!
"""
    await update.message.reply_text(welcome_msg, parse_mode='Markdown')
    print("✅ Welcome sent")

# ========== HELP COMMAND ==========
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = """
📚 *Help*

/start - Welcome message
/help - Show this help
/analyze SYMBOL - Analyze stock

*Examples:*
/analyze RELIANCE
/analyze TCS
/analyze HDFCBANK
/analyze INFY
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

# ========== ADD HANDLERS ==========
app.add_handler(CommandHandler("analyze", analyze))
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))

print("✅ Handlers: /analyze, /start, /help")

# ========== START BOT ==========
print("\n" + "=" * 50)
print("🚀 BOT RUNNING!")
print("=" * 50)
print("\n📱 Send /start to your bot on Telegram")
print("⚠️  Press Ctrl+C to stop\n")

if __name__ == "__main__":
    try:
        app.run_polling()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped")
    except Exception as e:
        print(f"❌ Error: {e}")