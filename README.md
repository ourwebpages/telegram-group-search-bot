# telegram-group-search-bot

# Telegram Resource Bot

A lightweight Telegram bot for storing, searching, and discovering resources using a private Telegram group as storage.

## ✨ Features
- 🔍 Typo-tolerant search
- 🌐 Web summary command
- 🔐 Admin system (multiple admins)
- 📦 Telegram group as database
- 🔒 Upload lock/unlock
- 🔥 Daily Top Picks
- ☁️ Cloud-host friendly (no disk usage)

## 📌 Commands

### Users
/start  
/help  
/search <query>  
/web <query>  
/list  

### Admins
/add <text>  
/delete <number>  
/lock  
/unlock  

## 🚀 Deploy on Pella.app

1. Create a Python app
2. Connect this GitHub repository
3. Add Environment Variables:
   - BOT_TOKEN
   - STORAGE_GROUP_ID
   - ADMIN_IDS
4. Run command:
   ```bash
   python bot.py