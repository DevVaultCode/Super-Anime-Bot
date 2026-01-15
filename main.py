import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# --- CONFIGURATION ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK")
DISK_KEY = os.environ.get("DISK_KEY")
SHORTENER_API = os.environ.get("SHORTENER_API") 
SHORTENER_DOMAIN = os.environ.get("SHORTENER_DOMAIN")

# --- 1. LINK SHORTENER ---
def get_money_link(long_url):
    if not SHORTENER_API: return long_url
    try:
        api_url = f"https://{SHORTENER_DOMAIN}/api?api={SHORTENER_API}&url={long_url}"
        resp = requests.get(api_url).json()
        if resp.get("status") == "success" or resp.get("shortenedUrl"):
            return resp.get("shortenedUrl")
    except:
        pass
    return long_url

# --- 2. UPLOAD TO STORAGE ---
def upload_file(file_path):
    url = "https://diskwala.com/api/upload" 
    try:
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {'key': DISK_KEY}
            resp = requests.post(url, files=files, data=data)
            if resp.status_code == 200:
                return resp.json().get('link')
    except:
        return None
    return None

# --- 3. BOT ACTIONS ---
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_msg = await update.message.reply_text("📥 Downloading... (Server)")
    
    file = await context.bot.get_file(update.message.document.file_id)
    file_name = update.message.document.file_name
    await file.download_to_drive(file_name)
    
    await status_msg.edit_text("🚀 Uploading to Cloud...")
    cloud_link = upload_file(file_name)
    
    if os.path.exists(file_name):
        os.remove(file_name)
    
    if cloud_link:
        final_link = get_money_link(cloud_link)
        await status_msg.edit_text(f"✅ **Done!**\n\n🔗 Link: {final_link}")
        
        if DISCORD_WEBHOOK:
            requests.post(DISCORD_WEBHOOK, json={"content": f"New File: {file_name}\nLink: {final_link}"})
    else:
        await status_msg.edit_text("❌ Upload Failed.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.run_polling()
