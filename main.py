import logging
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode, ChatAction
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import trade  # This should be your own module that does stock analysis

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Replace with your own bot token
BOT_TOKEN = "7946181710:AAFBmRnVEci-NnZ0h0FWtp9FNwEpNXrxHn4"

# Store user preferences if needed later
user_watchlists = {}

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    first_name = user.first_name

    keyboard = [
        [InlineKeyboardButton("🚀 Get Started", callback_data="help")],
        [InlineKeyboardButton("📈 Popular Stocks", callback_data="popular")],
        [InlineKeyboardButton("👤 View Profile", callback_data="profile")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        f"👋 *Welcome to StockSage Bot, {first_name}!*\n\n"
        "I'm your smart stock assistant 🤖. Just type any stock symbol (like `AAPL`, `TATASTEEL.NS`, `SBIN.NS`) and I’ll provide real-time insights 📊.\n\n"
        "Ready to explore the markets? 🔍"
    )

    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

# Help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📚 *StockSage Bot Help Guide*\n\n"
        "➤ Just send a stock symbol to get started (e.g., `RELIANCE.NS`, `AAPL`, `TCS.NS`).\n"
        "➤ `/start` - Restart the bot\n"
        "➤ `/help` - Show this message\n"
        "➤ `/profile` - View your profile info\n\n"
        "💡 *Tips:*\n"
        "• Indian stocks: use `.NS` or `.BO` suffix\n"
        "• Example: `TATASTEEL.NS`\n"
        "• US stocks: just the symbol (e.g., `AAPL`, `GOOG`)\n"
    )

    keyboard = [
        [InlineKeyboardButton("📈 Popular Stocks", callback_data="popular")],
        [InlineKeyboardButton("🔙 Back", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    else:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

# Popular stocks
async def popular_stocks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    popular_indian = [
        [
            InlineKeyboardButton("📊 RELIANCE", callback_data="analyze_RELIANCE.NS"),
            InlineKeyboardButton("💻 TCS", callback_data="analyze_TCS.NS"),
            InlineKeyboardButton("🧠 INFY", callback_data="analyze_INFY.NS")
        ],
        [
            InlineKeyboardButton("🏦 SBIN", callback_data="analyze_SBIN.NS"),
            InlineKeyboardButton("🚗 TATAMOTORS", callback_data="analyze_TATAMOTORS.NS"),
            InlineKeyboardButton("🏠 HDFCBANK", callback_data="analyze_HDFCBANK.NS")
        ],
        [
            InlineKeyboardButton("📱 ICICIBANK", callback_data="analyze_ICICIBANK.NS"),
            InlineKeyboardButton("🛠️ TATASTEEL", callback_data="analyze_TATASTEEL.NS"),
            InlineKeyboardButton("🧼 HINDUNILVR", callback_data="analyze_HINDUNILVR.NS")
        ],
        [InlineKeyboardButton("🔙 Back to Help", callback_data="help")]
    ]

    reply_markup = InlineKeyboardMarkup(popular_indian)
    text = "🌟 *Popular Indian Stocks*\n\nClick below to analyze a stock:"
    
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    else:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

# Handle symbol input
async def handle_symbol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action(action=ChatAction.TYPING)
    symbol = update.message.text.strip().upper()

    if re.match(r'^[A-Z&]+$', symbol) and '.' not in symbol:
        keyboard = [
            [
                InlineKeyboardButton(f"{symbol}.NS (NSE)", callback_data=f"analyze_{symbol}.NS"),
                InlineKeyboardButton(f"{symbol}.BO (BSE)", callback_data=f"analyze_{symbol}.BO")
            ],
            [InlineKeyboardButton(f"{symbol} (US)", callback_data=f"analyze_{symbol}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"📌 *Select Exchange for:* `{symbol}`",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        return

    try:
        result = trade.get_prediction(symbol)
        keyboard = [[InlineKeyboardButton("🔄 Refresh", callback_data=f"analyze_{symbol}")]]
        await update.message.reply_text(result, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error("Error in handle_symbol: %s", e)
        await update.message.reply_text("⚠️ Could not fetch data. Try again later.")

# Button callbacks
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data == "help":
        await help_command(update, context)
    elif data == "popular":
        await popular_stocks(update, context)
    elif data == "start":
        await start(update, context)
    elif data == "profile":
        user = query.from_user
        profile_text = (
            f"👤 *Your Profile*\n\n"
            f"• Name: {user.full_name}\n"
            f"• Username: @{user.username if user.username else 'N/A'}\n"
            f"• User ID: `{user.id}`"
        )
        await query.answer()
        await query.edit_message_text(profile_text, parse_mode=ParseMode.MARKDOWN)
    elif data.startswith("analyze_"):
        symbol = data.replace("analyze_", "")
        await query.answer(f"Analyzing {symbol}...")
        try:
            result = trade.get_prediction(symbol)
            keyboard = [[InlineKeyboardButton("🔄 Refresh", callback_data=f"analyze_{symbol}")]]
            await query.edit_message_text(result, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            logger.error("Error analyzing symbol %s: %s", symbol, e)
            await query.edit_message_text(f"⚠️ Could not analyze {symbol}", parse_mode=None)

# Profile command
async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    profile_text = (
        f"👤 *Your Profile*\n\n"
        f"• Name: {user.full_name}\n"
        f"• Username: @{user.username if user.username else 'N/A'}\n"
        f"• User ID: `{user.id}`"
    )
    await update.message.reply_text(profile_text, parse_mode=ParseMode.MARKDOWN)

# Main bot start
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("profile", profile_command))

    # Buttons
    app.add_handler(CallbackQueryHandler(button_callback))

    # Handle stock input
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_symbol))

    logger.info("🚀 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
