import telebot
from telebot import types
import json
import threading
import time

TOKEN = '8972517683:AAF3QEEO_tmHaYXGhFS3_bUSFCtZkJIngJA'
ADMIN_ID = 8173349543
bot = telebot.TeleBot(TOKEN)
DB_FILE = 'users.json'

def load_users():
    try:
        with open(DB_FILE, 'r') as f: return set(json.load(f))
    except: return set()

users = load_users()

def save_users():
    with open(DB_FILE, 'w') as f: json.dump(list(users), f)

# --- منوی مدیریت (Admin Panel) ---
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.chat.id == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("📊 آمار", "📝 ارسال پیام به همه")
        bot.send_message(message.chat.id, "📊 منوی مدیریت رئیس شاهد:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "📊 آمار" and message.chat.id == ADMIN_ID)
def admin_stats(message):
    bot.reply_to(message, f"🟢 کل کاربران فعال: {len(users)} نفر\n🔴 وضعیت سیستم: روشن و فعال")

@bot.message_handler(func=lambda message: message.text == "📝 ارسال پیام به همه" and message.chat.id == ADMIN_ID)
def broadcast_start(message):
    msg = bot.send_message(message.chat.id, "📝 لطفاً پیام خود را برای ارسال به همه کاربران بنویسید:")
    bot.register_next_step_handler(msg, broadcast_send)

def broadcast_send(message):
    count = 0
    for user_id in users:
        try:
            bot.send_message(user_id, message.text)
            count += 1
        except: continue
    bot.reply_to(message, f"✅ پیام با موفقیت برای {count} کاربر ارسال شد.")

# --- دستور شروع (اصلاح شده برای مطابقت با عکس) ---
@bot.message_handler(commands=['start'])
def start(message):
    users.add(message.chat.id)
    save_users()
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Dari 🇦🇫", callback_data='lang_fa'),
               types.InlineKeyboardButton("English 🇬🇧", callback_data='lang_en'),
               types.InlineKeyboardButton("Russian 🇷🇺", callback_data='lang_ru'))
    markup.add(types.InlineKeyboardButton("📩 پشتیبانی / Support", callback_data='support'))
    
    text = "✨ **سلام، به ربات رسمی رئیس شاهد خوش آمدید!** ✨\n\nما اینجا هستیم تا هر نوع رباتی که نیاز دارید برایتان طراحی کنیم.\n\n🌐 **انتخاب زبان:**\nDari 🇦🇫 | English 🇬🇧 | Russian 🇷🇺\n\n---------------------------\n💎 Powered by Reis Shahid"
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

# --- بخش اصلاح شده تغییر زبان ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def handle_lang(call):
    lang = call.data.split('_')[1]
    user_name = call.from_user.first_name
    user_id = call.from_user.id
    
    # متون مطابق با عکس
    if lang == 'fa':
        info_text = f"👤 نام: {user_name}\n🆔 آیدی: `{user_id}`\n\n🚀 برای سفارش ربات از دکمه پشتیبانی استفاده کنید.\n---------------------------\n💎 Powered by Reis Shahid"
    elif lang == 'en':
        info_text = f"👤 Name: {user_name}\n🆔 ID: `{user_id}`\n\n🚀 Use the support button to order a bot.\n---------------------------\n💎 Powered by Reis Shahid"
    else:
        info_text = f"👤 Имя: {user_name}\n🆔 ID: `{user_id}`\n\n🚀 Используйте кнопку поддержки, чтобы заказать бота.\n---------------------------\n💎 Powered by Reis Shahid"
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📩 ارتباط با رئیس شاهد", callback_data='support'))
    bot.edit_message_text(info_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == 'support')
def support_request(call):
    msg = bot.send_message(call.message.chat.id, "📩 لطفاً درخواست خود را بنویسید:")
    bot.register_next_step_handler(msg, forward_to_admin)

def forward_to_admin(message):
    bot.send_message(ADMIN_ID, f"📢 **درخواست جدید**\n👤 {message.chat.first_name}\n🆔 `{message.chat.id}`\n📝 متن: {message.text}")
    bot.reply_to(message, "✅ پیام شما ارسال شد.")

# پیام خودکار ۱۲ ساعته
def auto_message():
    while True:
        time.sleep(43200)
        announcement = "🔔 **یادآوری ویژه از طرف رئیس شاهد**\nبرای دسترسی به ابزارهای هک: 👉 @Skgjfydydybot 👈"
        for user_id in users:
            try: bot.send_message(user_id, announcement)
            except: continue

threading.Thread(target=auto_message, daemon=True).start()

print("ربات روشن شد...")
bot.polling(none_stop=True)

