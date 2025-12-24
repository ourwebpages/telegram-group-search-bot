import os
import json
import uuid
import logging
import requests
from datetime import datetime, time
from bs4 import BeautifulSoup
from rapidfuzz import fuzz

from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, ContextTypes, filters
)

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
STORAGE_GROUP_ID = int(os.getenv("STORAGE_GROUP_ID"))
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",")]

DATA_FILE = "data.json"
UPLOAD_LOCK = False

logging.basicConfig(level=logging.INFO)

# ================= DATA =================
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump([], f)

def load_data():
    with open(DATA_FILE) as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ================= HELPERS =================
def is_admin(user_id):
    return user_id in ADMIN_IDS

def auto_tags(text):
    tags = []
    for word in ["python", "ai", "bot", "telegram", "discord", "api", "pdf"]:
        if word in text.lower():
            tags.append(word)
    return list(set(tags))

def typo_match(a, b):
    return fuzz.partial_ratio(a.lower(), b.lower()) > 70

# ================= COMMANDS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Resource Bot Ready!\n\n"
        "/search <query>\n"
        "/web <query>\n"
        "/list\n"
        "/help"
    )

async def help_cmd(update: Update, context):
    await update.message.reply_text(
        "📌 Commands:\n"
        "/search python\n"
        "/web latest ai news\n"
        "/list\n\n"
        "Admins:\n"
        "/add, /edit, /delete, /lock, /unlock, /top"
    )

async def list_cmd(update: Update, context):
    data = load_data()
    if not data:
        await update.message.reply_text("No resources yet.")
        return

    msg = "📚 Stored Resources:\n"
    for i, d in enumerate(data):
        msg += f"{i+1}. {d['title']} ({', '.join(d['tags'])})\n"
    await update.message.reply_text(msg)

async def search_cmd(update: Update, context):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("Usage: /search <query>")
        return

    data = load_data()
    results = []

    for d in data:
        if typo_match(query, d["title"]) or any(typo_match(query, t) for t in d["tags"]):
            results.append(d)

    if not results:
        await update.message.reply_text("❌ No results found.")
        return

    msg = "🔍 Results:\n"
    for d in results[:10]:
        msg += f"- {d['title']}\n"
    await update.message.reply_text(msg)

# ================= WEB =================
async def web_cmd(update: Update, context):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("Usage: /web <query>")
        return

    try:
        r = requests.get(
            f"https://duckduckgo.com/html/?q={query}",
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        soup = BeautifulSoup(r.text, "html.parser")
        texts = [a.text for a in soup.select(".result__snippet")[:3]]
        summary = " ".join(texts)[:1000]

        await update.message.reply_text(f"🌐 Web Summary:\n{summary}")
    except Exception as e:
        await update.message.reply_text("Web search failed.")

# ================= ADMIN =================
async def add_resource(update: Update, context):
    global UPLOAD_LOCK
    if not is_admin(update.effective_user.id):
        return

    if UPLOAD_LOCK:
        await update.message.reply_text("🔒 Uploads locked.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /add <title | description>")
        return

    text = " ".join(context.args)
    tags = auto_tags(text)

    data = load_data()
    data.append({
        "id": str(uuid.uuid4())[:8],
        "title": text[:50],
        "tags": tags,
        "added": datetime.utcnow().isoformat()
    })
    save_data(data)

    await update.message.reply_text("✅ Resource added.")

async def delete_resource(update: Update, context):
    if not is_admin(update.effective_user.id):
        return

    if not context.args:
        await update.message.reply_text("Usage: /delete <number>")
        return

    idx = int(context.args[0]) - 1
    data = load_data()

    if idx < 0 or idx >= len(data):
        await update.message.reply_text("Invalid ID.")
        return

    data.pop(idx)
    save_data(data)
    await update.message.reply_text("🗑 Deleted.")

async def lock_cmd(update: Update, context):
    global UPLOAD_LOCK
    if is_admin(update.effective_user.id):
        UPLOAD_LOCK = True
        await update.message.reply_text("🔒 Upload locked.")

async def unlock_cmd(update: Update, context):
    global UPLOAD_LOCK
    if is_admin(update.effective_user.id):
        UPLOAD_LOCK = False
        await update.message.reply_text("🔓 Upload unlocked.")

# ================= DAILY TOP =================
async def daily_top(context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not data:
        return

    top = data[-3:]
    msg = "🔥 Top Picks Today:\n"
    for d in top:
        msg += f"- {d['title']}\n"

    await context.bot.send_message(chat_id=STORAGE_GROUP_ID, text=msg)

# ================= MAIN =================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_cmd))
app.add_handler(CommandHandler("list", list_cmd))
app.add_handler(CommandHandler("search", search_cmd))
app.add_handler(CommandHandler("web", web_cmd))

app.add_handler(CommandHandler("add", add_resource))
app.add_handler(CommandHandler("delete", delete_resource))
app.add_handler(CommandHandler("lock", lock_cmd))
app.add_handler(CommandHandler("unlock", unlock_cmd))

app.job_queue.run_daily(daily_top, time(hour=9))

print("✅ Bot running...")
app.run_polling()