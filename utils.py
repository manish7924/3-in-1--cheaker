# utils.py
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import config

_bot_status = "private"

def load_status():
    global _bot_status
    if os.path.exists(config.STATUS_FILE):
        with open(config.STATUS_FILE) as f:
            _bot_status = f.read().strip()
    else:
        _bot_status = "private"
    return _bot_status

def save_status(status):
    global _bot_status
    _bot_status = status
    with open(config.STATUS_FILE, "w") as f:
        f.write(status)

def get_status():
    return _bot_status

def is_private():
    return _bot_status == "private"

def is_subscribed(bot, user_id):
    if user_id == config.OWNER_ID:
        return True
    try:
        return bot.get_chat_member(config.CHANNEL_ID, user_id).status in ['member', 'administrator', 'creator']
    except Exception:
        return False

def force_join_warning(bot, chat_id):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("Join Channel", url=config.CHANNEL_LINK),
        InlineKeyboardButton("Joined ✅", callback_data="check_joined")
    )
    bot.send_message(chat_id, "You must join our channel to use this bot!", reply_markup=markup)

def private_warning(bot, chat_id):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Join Our Channel", url="https://t.me/+dP_iEnSkfj8yNjA1"))
    markup.add(InlineKeyboardButton("Contact ALEX (Admin)", url=f"tg://openmessage?user_id={config.OWNER_ID}"))
    bot.send_message(chat_id, "Bot is under Maintenance\n\nPlease Contact Owner or Try again later", reply_markup=markup)
