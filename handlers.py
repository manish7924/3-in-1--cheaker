# handlers.py
import re
import os
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

import config
import utils
import checkers

def register_handlers(bot):

    def execute_bulk_check(m, emails_to_check, domain="gmail"):
        if not utils.is_subscribed(bot, m.from_user.id):
            utils.force_join_warning(bot, m.chat.id)
            return
        if utils.is_private() and m.from_user.id != config.OWNER_ID:
            utils.private_warning(bot, m.chat.id)
            return
        if not emails_to_check:
            bot.reply_to(m, "No valid addresses found to check.")
            return

        rm_msg = bot.send_message(m.chat.id, "🔄 Processing...", reply_markup=ReplyKeyboardRemove())
        bot.delete_message(m.chat.id, rm_msg.message_id)

        available = []
        total = len(emails_to_check)
        status = bot.send_message(m.chat.id, f"0/{total} checked")
        
        for i, email in enumerate(emails_to_check, 1):
            if domain == "gmail":
                username = email.split("@")[0]
                TL, gaps = checkers.get_valid_tokens()
                is_available = checkers.GmailChecker(username, TL, gaps).check() if TL and gaps else False
            elif domain == "aol":
                username = email.split("@")[0]
                is_available = checkers.check_aol_username(username)
            else:
                is_available = checkers.check_fakemail(email)
            
            if is_available:
                available.append(email)
                bot.send_message(config.OWNER_ID, f"New Available Found!\nEmail: {email}")

            if i % 10 == 0 or i == total:
                try:
                    bot.edit_message_text(f"🔄 {i}/{total} checked\n✅ AVAILABLE: {len(available)}", m.chat.id, status.message_id)
                except:
                    pass

        try:
            bot.edit_message_text(f"✅ {total}/{total} checked\nAVAILABLE found: {len(available)}", m.chat.id, status.message_id)
        except:
            pass

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("𝗖𝗼𝗻𝘁𝗮𝗰𝘁 𝗢𝘄𝗻𝗲𝗿", url=f"tg://openmessage?user_id={config.OWNER_ID}", style="primary"))

        if available:
            txt = "\n".join(available)
            if len(txt) > 3900:
                output_filename = "available.txt"
                with open(output_filename, "w", encoding="utf-8") as f:
                    f.write(txt)
                with open(output_filename, "rb") as f:
                    bot.send_document(m.chat.id, f, caption=f"✅ {len(available)} AVAILABLE", reply_markup=markup)
                os.remove(output_filename)
            else:
                bot.send_message(m.chat.id, f"✅ {len(available)} AVAILABLE:\n\n{txt}", reply_markup=markup)
        else:
            bot.send_message(m.chat.id, "No available found.", reply_markup=markup)
        
        try:
            bot.delete_message(m.chat.id, status.message_id)
        except:
            pass

    def process_single(m, domain):
        if not utils.is_subscribed(bot, m.from_user.id):
            utils.force_join_warning(bot, m.chat.id)
            return
        if utils.is_private() and m.from_user.id != config.OWNER_ID: return
        if m.text and m.text.lower() in ['cancel', 'cancle']:
            bot.reply_to(m, "Cancelled.", reply_markup=ReplyKeyboardRemove())
            return
        text = m.text.strip().lower()
        if domain == "fakemail":
            email = text if "@" in text else None
        else:
            username = text.split("@")[0] if "@" in text else text
            email = f"{username}@{domain}.com"
        
        if not email:
            bot.reply_to(m, "Invalid email format.", reply_markup=ReplyKeyboardRemove())
            return

        rm_msg = bot.send_message(m.chat.id, "🔄 Processing...", reply_markup=ReplyKeyboardRemove())
        bot.delete_message(m.chat.id, rm_msg.message_id)

        sent = bot.reply_to(m, f"🔍 Checking <code>{email}</code>...", parse_mode="HTML")
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("𝗖𝗼𝗻𝘁𝗮𝗰𝘁 𝗢𝘄𝗻𝗲𝗿", url=f"tg://openmessage?user_id={config.OWNER_ID}", style="primary"))
        
        if domain == "gmail":
            TL, gaps = checkers.get_valid_tokens()
            is_available = checkers.GmailChecker(email.split("@")[0], TL, gaps).check() if TL and gaps else False
        elif domain == "aol":
            is_available = checkers.check_aol_username(email.split("@")[0])
        else:
            is_available = checkers.check_fakemail(email)
        
        if is_available:
            bot.edit_message_text(f"<code>{email}</code>\n✅ AVAILABLE", m.chat.id, sent.message_id, parse_mode="HTML", reply_markup=markup)
            bot.send_message(config.OWNER_ID, f"New Available Found!\nEmail: {email}")
        else:
            bot.edit_message_text(f"<code>{email}</code>\n❤️‍🩹 TAKEN", m.chat.id, sent.message_id, parse_mode="HTML", reply_markup=markup)

    def process_bulk_message(m, domain):
        if not utils.is_subscribed(bot, m.from_user.id):
            utils.force_join_warning(bot, m.chat.id)
            return
        if utils.is_private() and m.from_user.id != config.OWNER_ID:
            utils.private_warning(bot, m.chat.id)
            return
        if m.text and m.text.lower() in ['cancel', 'cancle']:
            bot.reply_to(m, "Cancelled.", reply_markup=ReplyKeyboardRemove())
            return

        all_lines = [l.strip().lower() for l in m.text.splitlines() if l.strip()]
        emails_list = []
        for line in all_lines:
            if "@" in line:
                emails_list.append(line)
            elif domain != "fakemail" and re.fullmatch(r'[\w\.-]+', line):
                emails_list.append(line + f'@{domain}.com')

        emails_to_check = list(set(emails_list))[:100]
        execute_bulk_check(m, emails_to_check, domain)
        
    def process_bulk_document(m, domain):
        if not utils.is_subscribed(bot, m.from_user.id):
            utils.force_join_warning(bot, m.chat.id)
            return
        if utils.is_private() and m.from_user.id != config.OWNER_ID:
            utils.private_warning(bot, m.chat.id)
            return
            
        if m.text and m.text.lower() in ['cancel', 'cancle']:
            bot.reply_to(m, "Cancelled.", reply_markup=ReplyKeyboardRemove())
            return
            
        if not m.document or not str(m.document.file_name).lower().endswith('.txt'):
            bot.reply_to(m, "Send only a .txt file.", reply_markup=ReplyKeyboardRemove())
            return

        bot.reply_to(m, "Downloading file...", reply_markup=ReplyKeyboardRemove())
        file = bot.download_file(bot.get_file(m.document.file_id).file_path)
        all_lines = [l.strip().lower() for l in file.decode('utf-8', errors='ignore').splitlines() if l.strip()]
        
        emails_list = []
        for line in all_lines:
            if "@" in line:
                emails_list.append(line)
            elif domain != "fakemail" and re.fullmatch(r'[\w\.-]+', line):
                emails_list.append(line + f'@{domain}.com')

        emails_to_check = list(set(emails_list))[:100]
        execute_bulk_check(m, emails_to_check, domain)

    # --- TELEGRAM HANDLERS ---
    @bot.callback_query_handler(func=lambda call: call.data == "check_joined")
    def check_joined_callback(call):
        if utils.is_subscribed(bot, call.from_user.id):
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("Contact Owner", url=f"tg://openmessage?user_id={config.OWNER_ID}", style="primary"))
            bot.edit_message_text(
                f"Hello {call.from_user.first_name}!\nThank you for joining our channel.\n\nUse /help to see commands.",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup
            )
        else:
            bot.answer_callback_query(call.id, "You haven't joined yet!", show_alert=True)

    @bot.message_handler(commands=['start'])
    def start(m):
        if not utils.is_subscribed(bot, m.from_user.id):
            utils.force_join_warning(bot, m.chat.id)
            return
        if utils.is_private() and m.from_user.id != config.OWNER_ID:
            utils.private_warning(bot, m.chat.id)
            return
            
        name = m.from_user.first_name
        checkers.get_valid_tokens() # Warm up tokens
        
        # New styled welcome message
        welcome_msg = (
            f"✅ 𝗪𝗲𝗹𝗰𝗼𝗺𝗲, {name}! \n\n"
            "𝗜 𝗮𝗺 𝘆𝗼𝘂𝗿 𝗵𝗶𝗴𝗵-𝗽𝗲𝗿𝗳𝗼𝗿𝗺𝗮𝗻𝗰𝗲 𝘁𝗼𝗼𝗹 𝗳𝗼𝗿 𝗳𝗮𝘀𝘁 𝗮𝗻𝗱 𝗮𝗰𝗰𝘂𝗿𝗮𝘁𝗲 𝗱𝗮𝘁𝗮 𝘃𝗮𝗹𝗶𝗱𝗮𝘁𝗶𝗼𝗻. \n\n"
            "—————\n"
            "🔰 𝗠𝗮𝗶𝗻 𝗖𝗼𝗺𝗺𝗮𝗻𝗱𝘀 : \n"
            "✦ /check — 𝗦𝘁𝗮𝗿𝘁 𝗮 𝗻𝗲𝘄 𝘃𝗮𝗹𝗶𝗱𝗮𝘁𝗶𝗼𝗻\n"
            "✦ /help — 𝗧𝗼 𝗢𝗽𝗲𝗻 𝗖𝗼𝗺𝗺𝗮𝗻𝗱𝘀 𝗟𝗶𝘀𝘁\n"
            "—————\n"
            "💡 𝗡𝗲𝗲𝗱 𝘀𝘂𝗽𝗽𝗼𝗿𝘁? 𝗥𝗲𝗮𝗰𝗵 𝗼𝘂𝘁 𝘁𝗼 𝗔𝗟𝗘𝗫."
        )
        
        # Create the inline button linking to Admin
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("#𝗔𝗹𝗲𝘅", url=f"tg://openmessage?user_id={config.OWNER_ID}", style="primary"))
        
        bot.send_message(m.chat.id, welcome_msg, reply_markup=markup)

    @bot.message_handler(commands=['help'])
    def help_cmd(m):
        if not utils.is_subscribed(bot, m.from_user.id):
            utils.force_join_warning(bot, m.chat.id)
            return
        if utils.is_private() and m.from_user.id != config.OWNER_ID:
            utils.private_warning(bot, m.chat.id)
            return
        bot.send_message(m.chat.id, "/check → Start checking\n/help → Commands\n/status → Change mode (owner)\n/ping → Check bot latency")

    @bot.message_handler(commands=['ping'])
    def ping_command(message):
        if not utils.is_subscribed(bot, message.from_user.id):
            utils.force_join_warning(bot, message.chat.id)
            return
        bot.send_chat_action(message.chat.id, 'typing')
        start_time = time.time()
        sent_msg = bot.send_message(message.chat.id, "<b>📡 Testing connection...</b>", parse_mode='HTML')
        duration = time.time() - start_time
        bot.edit_message_text(
            chat_id=message.chat.id, 
            message_id=sent_msg.message_id, 
            parse_mode='HTML',
            text=f"<b>🏓 Pong!</b>\n──────────────\n<b>Latency:</b> <code>{duration:.2f}s</code>"
        )

    @bot.message_handler(commands=['status'])
    def status_cmd(m):
        if not utils.is_subscribed(bot, m.from_user.id):
            utils.force_join_warning(bot, m.chat.id)
            return
        if m.from_user.id != config.OWNER_ID:
            bot.reply_to(m, "Owner only.")
            return
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("Public It", callback_data="set_public", style="success"),
            InlineKeyboardButton("Private It", callback_data="set_private", style="danger")
        )
        bot.send_message(m.chat.id, f"Current: {utils.get_status().upper()}\nSelect mode:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data in ["set_public", "set_private"])
    def change_status(call):
        if not utils.is_subscribed(bot, call.from_user.id):
            utils.force_join_warning(bot, call.message.chat.id)
            return
        if call.from_user.id != config.OWNER_ID: return
        new = "public" if call.data == "set_public" else "private"
        utils.save_status(new)
        bot.answer_callback_query(call.id, f"Bot → {new.upper()}")
        bot.edit_message_text(f"Status → {new.upper()}", call.message.chat.id, call.message.message_id)

    @bot.message_handler(func=lambda m: m.text and m.text.lower() in ['cancel', 'cancle'])
    def cancel_action(m):
        if not utils.is_subscribed(bot, m.from_user.id):
            utils.force_join_warning(bot, m.chat.id)
            return
        bot.clear_step_handler_by_chat_id(chat_id=m.chat.id)
        bot.reply_to(m, "Cancelled.", reply_markup=ReplyKeyboardRemove())

    @bot.message_handler(commands=['check'])
    def check_cmd(m):
        if not utils.is_subscribed(bot, m.from_user.id):
            utils.force_join_warning(bot, m.chat.id)
            return
        if utils.is_private() and m.from_user.id != config.OWNER_ID:
            utils.private_warning(bot, m.chat.id)
            return
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("📧 Gmail", callback_data="domain_gmail", style="primary"),
            InlineKeyboardButton("📨 AOL", callback_data="domain_aol", style="primary"),
            InlineKeyboardButton("🎭 FakeMail", callback_data="domain_fakemail", style="success")
        )
        bot.send_message(m.chat.id, "<b>⚙️ Select Domain Checker:</b>", parse_mode="HTML", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data == "back_to_domains")
    def back_to_domains_handler(call):
        # ⏳ 60-Second Expiration Check
        if int(time.time()) - call.message.date > 60:
            bot.answer_callback_query(call.id, "This Command is expired", show_alert=True)
            bot.edit_message_text("⏳ <b>This Command is expired.</b>\nPlease use /check again.", call.message.chat.id, call.message.message_id, parse_mode="HTML")
            return

        if not utils.is_subscribed(bot, call.from_user.id):
            utils.force_join_warning(bot, call.message.chat.id)
            return
        if utils.is_private() and call.from_user.id != config.OWNER_ID: return
        
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("📧 Gmail", callback_data="domain_gmail", style="primary"),
            InlineKeyboardButton("📨 AOL", callback_data="domain_aol", style="primary"),
            InlineKeyboardButton("🎭 FakeMail", callback_data="domain_fakemail", style="success")
        )
        bot.edit_message_text("<b>⚙️ Select Domain Checker:</b>", call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("domain_"))
    def domain_selected(call):
        # ⏳ 60-Second Expiration Check
        if int(time.time()) - call.message.date > 60:
            bot.answer_callback_query(call.id, "This Command is expired", show_alert=True)
            bot.edit_message_text("⏳ <b>This Command is expired.</b>\nPlease use /check again.", call.message.chat.id, call.message.message_id, parse_mode="HTML")
            return

        if not utils.is_subscribed(bot, call.from_user.id):
            utils.force_join_warning(bot, call.message.chat.id)
            return
        if utils.is_private() and call.from_user.id != config.OWNER_ID: return
        
        domain = call.data.split("_")[1]
        
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("👤 Single Check", callback_data=f"single_{domain}", style="primary"),
            InlineKeyboardButton("📁 Bulk Check (File)", callback_data=f"bulk_{domain}", style="primary"),
            InlineKeyboardButton("📝 Bulk Check (Message)", callback_data=f"bulk_message_{domain}", style="primary"),
            InlineKeyboardButton("🔙 Back", callback_data="back_to_domains", style="danger")
        )
        bot.edit_message_text(f"<b>🌐 {domain.upper()} Checker</b>\n\nChoose your checking mode:", call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith(("single_", "bulk_", "bulk_message_")))
    def mode_selected(call):
        # ⏳ 60-Second Expiration Check
        if int(time.time()) - call.message.date > 60:
            bot.answer_callback_query(call.id, "This Command is expired", show_alert=True)
            bot.edit_message_text("⏳ <b>This Command is expired.</b>\nPlease use /check again.", call.message.chat.id, call.message.message_id, parse_mode="HTML")
            return

        if not utils.is_subscribed(bot, call.from_user.id):
            utils.force_join_warning(bot, call.message.chat.id)
            return
        if utils.is_private() and call.from_user.id != config.OWNER_ID: return
        
        # Split correctly from the right to avoid breaking on "bulk_message"
        parts = call.data.rsplit("_", 1)
        mode = parts[0]
        domain = parts[1]

        cancel_markup = ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_markup.add(KeyboardButton("Cancel"))

        if mode == "single":
            msg = "Send full email (e.g. user@hi2.in)" if domain == "fakemail" else f"Send username for @{domain}.com"
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, msg, reply_markup=cancel_markup)
            bot.register_next_step_handler(call.message, lambda m: process_single(m, domain))

        elif mode == "bulk":
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, "Send your .txt file with emails/usernames (one per line)", reply_markup=cancel_markup)
            bot.register_next_step_handler(call.message, lambda m: process_bulk_document(m, domain))

        elif mode == "bulk_message":
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, "Send emails/usernames separated by newlines", reply_markup=cancel_markup)
            bot.register_next_step_handler(call.message, lambda m: process_bulk_message(m, domain))
