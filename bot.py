import os
import logging
import telebot
import random
import string
from telebot import types
from config import TELEGRAM_TOKEN, CHANNEL_ID, BOT_OWNER_ID, PASTEBIN_API_KEY, URL_SHORTENER_API_KEY
from db import init_db, can_claim_cookie, can_generate_giftcode, is_valid_giftcode, get_random_cookie_file, redeem_giftcode, add_bulk_cookies, add_giftcode, add_user, get_all_users
from utils import generate_gift_code, create_pastebin_entry, shorten_url

logger = logging.getLogger(__name__)

bot = telebot.TeleBot(TELEGRAM_TOKEN)
bot_owner_uploading = {}

# Ensure necessary directories exist
if not os.path.exists('cookies'):
    os.makedirs('cookies')
if not os.path.exists('bulk_cookies'):
    os.makedirs('bulk_cookies')

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    add_user(user_id)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton('Generate Gift Code'))
    keyboard.add(types.KeyboardButton('Claim Cookies'))
    keyboard.add(types.KeyboardButton('Support'))
    bot.send_message(message.chat.id, "Welcome! Please choose an option:", reply_markup=keyboard)

@bot.message_handler(func=lambda message: message.text == 'Generate Gift Code')
def handle_generate_gift_code(message):
    user_id = message.from_user.id
    if can_generate_giftcode(user_id):
        gift_code = generate_gift_code()
        cookie_data = f"Cookie data for {gift_code}"  # Replace with actual cookie data generation
        pastebin_url = create_pastebin_entry(gift_code, cookie_data, PASTEBIN_API_KEY)
        if pastebin_url:
            shortened_url = shorten_url(pastebin_url, URL_SHORTENER_API_KEY)
            if shortened_url:
                add_giftcode(user_id, gift_code)
                bot.send_message(message.chat.id, f"Here is your gift code URL: {shortened_url}")
            else:
                bot.send_message(message.chat.id, "Failed to shorten URL. Please try again.")
        else:
            bot.send_message(message.chat.id, "Failed to create Pastebin entry. Please try again.")
    else:
        bot.send_message(message.chat.id, "You can only generate a gift code every 6 hours. Please try again later.")

@bot.message_handler(func=lambda message: message.text == 'Claim Cookies')
def handle_claim_cookies(message):
    bot.send_message(message.chat.id, "Please enter your gift code.")

@bot.message_handler(func=lambda message: message.text == 'Support')
def handle_support(message):
    bot.send_message(message.chat.id, "Support: contact@example.com")

@bot.message_handler(commands=['upload_cookies'])
def handle_bulk_upload_command(message):
    if str(message.from_user.id) == str(BOT_OWNER_ID):
        bot.send_message(message.chat.id, "Please send the bulk cookies file.")
        bot_owner_uploading[message.from_user.id] = 'upload_cookies'
    else:
        bot.send_message(message.chat.id, "You are not authorized to use this command.")

@bot.message_handler(content_types=['document'])
def handle_bulk_upload(message):
    if bot_owner_uploading.get(message.from_user.id) == 'upload_cookies':
        try:
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            extension = os.path.splitext(message.document.file_name)[1]
            random_name = ''.join(random.choices(string.digits, k=10)) + extension
            file_path = f"bulk_cookies/{random_name}"
            with open(file_path, 'wb') as new_file:
                new_file.write(downloaded_file)
            process_bulk_cookies(file_path, random_name)
            bot.reply_to(message, "Bulk cookies uploaded and processed.")
            bot_owner_uploading[message.from_user.id] = False
        except Exception as e:
            logger.error(f"Error uploading bulk cookies: {e}")
            bot.reply_to(message, f"There was an error uploading the bulk cookies: {e}")
            bot_owner_uploading[message.from_user.id] = False
    else:
        bot.reply_to(message, "You are not authorized to upload cookies.")

def process_bulk_cookies(file_path, file_name):
    add_bulk_cookies([(file_name, file_path)])

@bot.message_handler(commands=['broadcast'])
def handle_broadcast_command(message):
    if str(message.from_user.id) == str(BOT_OWNER_ID):
        bot.send_message(message.chat.id, "Please send the message you want to broadcast.")
        bot_owner_uploading[message.from_user.id] = 'broadcast'
    else:
        bot.send_message(message.chat.id, "You are not authorized to use this command.")

@bot.message_handler(func=lambda message: message.from_user.id in bot_owner_uploading and bot_owner_uploading[message.from_user.id] == 'broadcast')
def handle_broadcast_message(message):
    if str(message.from_user.id) == str(BOT_OWNER_ID):
        broadcast_message = message.text
        users = get_all_users()
        for user_id in users:
            try:
                bot.send_message(user_id, broadcast_message)
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")
        bot.reply_to(message, "Broadcast message sent to all users.")
        bot_owner_uploading[message.from_user.id] = False
    else:
        bot.reply_to(message, "You are not authorized to send broadcast messages.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    user_text = message.text
    add_user(user_id)  # Store user ID

    if is_member(user_id):
        if is_valid_giftcode(user_text):
            if can_claim_cookie(user_id):
                cookie_file = get_random_cookie_file()
                if cookie_file:
                    try:
                        with open(cookie_file, 'rb') as doc:
                            bot.send_document(message.chat.id, doc)
                        redeem_giftcode(user_id, user_text)
                    except FileNotFoundError:
                        bot.send_message(message.chat.id, "Error: The cookie file was not found. Please try again later.")
                else:
                    bot.send_message(message.chat.id, "No cookies available. Please try again later.")
            else:
                bot.send_message(message.chat.id, "You can only claim one cookie every 3 hours. Please try again later.")
        else:
            bot.send_message(message.chat.id, "Invalid or already redeemed gift code. Please try again.")
    else:
        bot.send_message(message.chat.id, "You must join our channel to use this bot. Please join and try again.")

def is_member(user_id):
    try:
        member_status = bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id).status
        return member_status in ["member", "administrator", "creator"]
    except telebot.apihelper.ApiTelegramException as e:
        logger.error(f"Failed to check membership for user {user_id}: {e}")
        return False

if __name__ == '__main__':
    init_db()
    bot.polling(none_stop=True)
