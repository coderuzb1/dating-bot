import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from flask import Flask

app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Bot ishlayapti!"

async def start(update, context):
    await update.message.reply_text("Salom!")

async def handle_message(update, context):
    await update.message.reply_text(f"Siz yozdingiz: {update.message.text}")

def main():
    TOKEN = os.environ.get("BOT_TOKEN")
    if not TOKEN:
        print("XATO: BOT_TOKEN topilmadi!")
        return
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot ishga tushdi...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
