import os
import sqlite3
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN not set")

# Database
conn = sqlite3.connect("data.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER,
    text TEXT
)
""")
conn.commit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is running!\nUse /search <keyword>")

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /search <keyword>")
        return

    key = context.args[0]
    cursor.execute("SELECT text FROM messages WHERE text LIKE ? LIMIT 5", (f"%{key}%",))
    rows = cursor.fetchall()

    if not rows:
        await update.message.reply_text("No results found.")
        return

    msg = "🔍 Results:\n\n"
    for r in rows:
        msg += f"• {r[0]}\n\n"

    await update.message.reply_text(msg)

async def index_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        cursor.execute(
            "INSERT INTO messages (chat_id, text) VALUES (?, ?)",
            (update.message.chat_id, update.message.text)
        )
        conn.commit()

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("search", search))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, index_group))

    print("🤖 Bot started successfully on Railway")
    app.run_polling()

if __name__ == "__main__":
    main()