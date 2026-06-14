# main.py
import telebot
import time
import os

import config
import utils
from handlers import register_handlers

def start_bot():
    # Load state from file (public/private)
    utils.load_status()
    
    # Initialize Bot instance
    bot = telebot.TeleBot(config.TOKEN)
    
    # Register all handlers
    register_handlers(bot)

    print(f"Bot Running | Mode: {utils.get_status().upper()}")
    
    try:
        bot.send_message(config.OWNER_ID, "✅ Bot Restarted Successfully!")
    except Exception:
        pass
    
    bot.infinity_polling(timeout=60, long_polling_timeout=60)

if __name__ == "__main__":
    while True:
        try:
            start_bot()
        except Exception as e:
            print(f"Crash → Restarting in 3s... ({e})")
            time.sleep(3)
            os.system("cls" if os.name == "nt" else "clear")
