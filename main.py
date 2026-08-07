import json
import os
import subprocess
import telebot
from telebot import types

TOKEN = "8724320555:AAGQnxw2OaBnXV2-b_MNKm41Ypk4j_bYPH8"
INITIAL_ADMIN_ID = "8173349543"  # آیدی عددی مالک اصلی ربات (ریس شاهد)

bot = telebot.TeleBot(TOKEN)

DATA_FILE = "users_data.json"
ADMINS_FILE = "admins.json"
CHANNELS_FILE = "channels.json"
USER_BOTS_DIR = "user_bots"
os.makedirs(USER_BOTS_DIR, exist_ok=True)

# ذخیره پردازش ربات‌های کاربران برای امکان متوقف کردن آن‌ها
active_user_processes = {}

# سیستم ترجمه دو زبانه (دری و انگلیسی)
TRANSLATIONS = {
    "dr": {
        "choose_lang": "لطفاً زبان خود را انتخاب کنید:\n请选择您的语言 / Please choose your language:",
        "welcome_menu": (
            "به بهترین ربات‌ساز خوش آمدید ✨\n\n"
            "از منو زیر استفاده کنید: ✔️"
        ),
        "profile": (
            "کاربر ⚡ {name} | برای استفاده از این بخش به امتیاز نیاز دارید.\n"
            "هر کاربری که با لینک شما عضو شود امتیاز می‌گیرید.\n"
            "🟢 امتیاز فعلی شما: {score}\n"
            "🌐 لینک مخصوص شما:\n{link}"
        ),
        "ref_bonus": "🎉 یک کاربر با لینک دعوت شما پیوست! امتیاز دریافت کردید.",
        "support_prompt": "✍️ لطفاً پیام، سؤال یا مشکل خود را ارسال کنید تا به ادمین برسد:",
        "support_sent": "✅ پیام شما با موفقیت به پشتیبانی ارسال شد. به زودی پاسخ داده خواهد شد.",
        "join_lock": (
            "📢 برای استفاده از ربات ما لطفا در کانال ما عضو شوید\n"
            "بعد از عضویت روی عضو شدم کلیک کنید"
        ),
        "btn_check_join": "عضو شدم ✅",
        "not_joined_alert": "❌ شما هنوز در تمام کانال‌ها و گروه‌های زیر عضو نشده‌اید!",
        "btn_online": "🛠 آنلاین کردن ربات",
        "btn_delete": "❌ حذف ربات",
        "btn_transfer": "🔄 انتقال امتیاز",
        "btn_buy": "🛒 خریداری امتیاز",
        "btn_info": "✔ معلومات من",
        "btn_support": "✔ پشتیبانی",
    },
    "en": {
        "choose_lang": "Please choose your language:",
        "welcome_menu": (
            "Welcome to the best bot builder ✨\n\n"
            "Use the menu below: ✔️"
        ),
        "profile": (
            "User ⚡ {name} | You need score to use this feature.\n"
            "Every user who joins via your link gives you score.\n"
            "🟢 Your current score: {score}\n"
            "🌐 Your special link:\n{link}"
        ),
        "ref_bonus": "🎉 A user joined using your referral link! You received score.",
        "support_prompt": "✍️ Please send your message, question, or issue to reach the admin:",
        "support_sent": "✅ Your message has been successfully sent to support. It will be answered soon.",
        "join_lock": (
            "📢 To use our bot, please join our channel first\n"
            "After joining, click 'Joined' button"
        ),
        "btn_check_join": "Joined ✅",
        "not_joined_alert": "❌ You have not joined all required channels and groups yet!",
        "btn_online": "🛠 Online Bot",
        "btn_delete": "❌ Delete Bot",
        "btn_transfer": "🔄 Transfer Score",
        "btn_buy": "🛒 Buy Score",
        "btn_info": "✔ My Info",
        "btn_support": "✔ Support",
    }
}


def load_data():
  if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
      return json.load(f)
  return {}


def save_data(data):
  with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)


def load_admins():
  if os.path.exists(ADMINS_FILE):
    with open(ADMINS_FILE, "r", encoding="utf-8") as f:
      admins = json.load(f)
      if str(INITIAL_ADMIN_ID) not in admins:
        admins.insert(0, str(INITIAL_ADMIN_ID))
      return admins
  return [str(INITIAL_ADMIN_ID)]


def save_admins(admins):
  with open(ADMINS_FILE, "w", encoding="utf-8") as f:
    json.dump(admins, f, ensure_ascii=False, indent=4)


def is_admin(user_id):
  admins = load_admins()
  return str(user_id) in admins


def load_channels():
  if os.path.exists(CHANNELS_FILE):
    with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
      return json.load(f)
  default_channels = [
      {"name": "@hackwhatandetc", "url": "https://t.me/hackwhatandetc", "id": "@hackwhatandetc"},
      {"name": "@hackwhatandetcb", "url": "https://t.me/hackwhatandetcb", "id": "@hackwhatandetcb"}
  ]
  save_channels(default_channels)
  return default_channels


def save_channels(channels):
  with open(CHANNELS_FILE, "w", encoding="utf-8") as f:
    json.dump(channels, f, ensure_ascii=False, indent=4)


def check_user_membership(user_id):
  channels = load_channels()
  if not channels:
    return True
  for ch in channels:
    ch_id = ch["id"]
    try:
      member = bot.get_chat_member(ch_id, int(user_id))
      if member.status not in ["member", "administrator", "creator"]:
        return False
    except Exception as e:
      print(f"Error checking membership for {ch_id}: {e}")
      return False
  return True


# ساخت منوی اصلی شیشه‌ای بر اساس زبان کاربر
def get_main_menu(lang="dr"):
  t = TRANSLATIONS.get(lang, TRANSLATIONS["dr"])
  markup = types.InlineKeyboardMarkup(row_width=2)
  markup.add(
      types.InlineKeyboardButton(t["btn_online"], callback_data="online_bot_menu"),
      types.InlineKeyboardButton(t["btn_delete"], callback_data="delete_bot_menu"),
      types.InlineKeyboardButton(t["btn_transfer"], callback_data="transfer_score"),
      types.InlineKeyboardButton(t["btn_buy"], callback_data="buy_score"),
      types.InlineKeyboardButton(t["btn_info"], callback_data="my_info"),
      types.InlineKeyboardButton(t["btn_support"], callback_data="support_btn")
  )
  return markup


def send_main_menu(chat_id, lang="dr"):
  t = TRANSLATIONS.get(lang, TRANSLATIONS["dr"])
  bot.send_message(chat_id, t["welcome_menu"], reply_markup=get_main_menu(lang))


@bot.message_handler(commands=["start"])
def start(message):
  uid = str(message.from_user.id)
  data = load_data()
  args = message.text.split()

  if uid not in data:
    # اگر کاربر جدید است، اطلاعات اولیه را ذخیره می‌کنیم اما زبان را بعد از انتخاب می‌گذاریم
    data[uid] = {"score": 0, "lang": None}
    if len(args) > 1:
      referrer_id = args[1]
      if referrer_id in data and referrer_id != uid:
        data[referrer_id]["score"] += 5
        ref_lang = data[referrer_id].get("lang", "dr")
        try:
          bot.send_message(int(referrer_id), TRANSLATIONS[ref_lang]["ref_bonus"])
        except:
          pass
    save_data(data)

  # اگر زبان انتخاب نشده باشد، ابتدا منوی انتخاب زبان ظاهر می‌شود
  if data[uid].get("lang") is None:
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("دری 🇦🇫", callback_data="lang_dr"),
        types.InlineKeyboardButton("English 🇬🇧", callback_data="lang_en")
    )
    bot.send_message(message.chat.id, TRANSLATIONS["dr"]["choose_lang"], reply_markup=markup)
    return

  lang = data[uid]["lang"]
  if not check_user_membership(uid):
    channels = load_channels()
    markup = types.InlineKeyboardMarkup(row_width=1)
    for ch in channels:
      markup.add(types.InlineKeyboardButton(ch["name"], url=ch["url"]))
    markup.add(types.InlineKeyboardButton(TRANSLATIONS[lang]["btn_check_join"], callback_data="check_join"))
    
    bot.send_message(message.chat.id, TRANSLATIONS[lang]["join_lock"], reply_markup=markup)
    return

  send_main_menu(message.chat.id, lang)


# تنظیم زبان انتخاب شده توسط کاربر
@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def set_language_callback(call):
  uid = str(call.from_user.id)
  selected_lang = call.data.split("_")[1]  # dr یا en
  
  data = load_data()
  if uid not in data:
    data[uid] = {"score": 0}
  data[uid]["lang"] = selected_lang
  save_data(data)

  bot.answer_callback_query(call.id, "✅ Language saved!" if selected_lang == "en" else "✅ زبان ذخیره شد!")
  try:
    bot.delete_message(call.message.chat.id, call.message.message_id)
  except:
    pass

  if not check_user_membership(uid):
    channels = load_channels()
    markup = types.InlineKeyboardMarkup(row_width=1)
    for ch in channels:
      markup.add(types.InlineKeyboardButton(ch["name"], url=ch["url"]))
    markup.add(types.InlineKeyboardButton(TRANSLATIONS[selected_lang]["btn_check_join"], callback_data="check_join"))
    
    bot.send_message(call.message.chat.id, TRANSLATIONS[selected_lang]["join_lock"], reply_markup=markup)
    return

  send_main_menu(call.message.chat.id, selected_lang)


@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def check_join_callback(call):
  uid = str(call.from_user.id)
  data = load_data()
  lang = data.get(uid, {}).get("lang", "dr")

  if check_user_membership(uid):
    bot.answer_callback_query(call.id, "✅ Approved!" if lang == "en" else "✅ عضویت شما تایید شد!")
    try:
      bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
      pass
    send_main_menu(call.message.chat.id, lang)
  else:
    bot.answer_callback_query(call.id, TRANSLATIONS[lang]["not_joined_alert"], show_alert=True)


@bot.callback_query_handler(func=lambda call: call.data == "my_info")
def my_info_callback(call):
  uid = str(call.from_user.id)
  data = load_data()
  lang = data.get(uid, {}).get("lang", "dr")
  
  if not check_user_membership(uid):
    bot.answer_callback_query(call.id, "❌ Join channels first!" if lang == "en" else "❌ ابتدا باید در کانال و گروه عضو شوید!", show_alert=True)
    return

  if uid not in data:
    data[uid] = {"score": 0, "lang": lang}
    save_data(data)

  user = call.from_user
  ref_link = f"https://t.me/Robat_online_bot?start={uid}"
  
  text = TRANSLATIONS[lang]["profile"].format(
      name=user.first_name,
      score=data[uid]["score"],
      link=ref_link,
  )
  bot.answer_callback_query(call.id)
  bot.send_message(call.message.chat.id, text, reply_markup=get_main_menu(lang))


@bot.callback_query_handler(func=lambda call: call.data == "online_bot_menu")
def online_bot_callback(call):
  uid = str(call.from_user.id)
  data = load_data()
  lang = data.get(uid, {}).get("lang", "dr")
  
  if not check_user_membership(uid):
    bot.answer_callback_query(call.id, "❌ Join channels first!" if lang == "en" else "❌ ابتدا باید در کانال و گروه عضو شوید!", show_alert=True)
    return

  score = data.get(uid, {}).get("score", 0)

  bot.answer_callback_query(call.id)
  if score < 50:
    msg_text = f"❌ Not enough score! Need 50 score, you have {score}." if lang == "en" else f"❌ امتیاز شما کافی نیست!\nبرای آنلاین کردن ربات ۵۰ امتیاز نیاز دارید اما امتیاز فعلی شما {score} است."
    bot.send_message(call.message.chat.id, msg_text)
    return

  prompt_text = "📂 Please send your bot file (`.py`):" if lang == "en" else "📂 لطفاً فایل ربات خود (با فرمت `.py`) را ارسال کنید:"
  msg = bot.send_message(call.message.chat.id, prompt_text)
  bot.register_next_step_handler(msg, handle_docs_from_step)


@bot.callback_query_handler(func=lambda call: call.data == "delete_bot_menu")
def delete_bot_callback(call):
  uid = str(call.from_user.id)
  data = load_data()
  lang = data.get(uid, {}).get("lang", "dr")
  bot.answer_callback_query(call.id)
  
  path = os.path.join(USER_BOTS_DIR, f"{uid}_bot.py")
  deleted_any = False

  if uid in active_user_processes:
    try:
      active_user_processes[uid].terminate()
      del active_user_processes[uid]
      deleted_any = True
    except:
      pass

  if os.path.exists(path):
    try:
      os.remove(path)
      deleted_any = True
    except:
      pass

  if deleted_any:
    msg_text = "🗑️ Your bot has been deleted and stopped." if lang == "en" else "🗑️ ربات شما با موفقیت از سرور پاک شد و متوقف گردید."
    bot.send_message(call.message.chat.id, msg_text, reply_markup=get_main_menu(lang))
  else:
    msg_text = "❌ You have no active bots on the server." if lang == "en" else "❌ شما هیچ ربات فعالی روی سرور ندارید."
    bot.send_message(call.message.chat.id, msg_text, reply_markup=get_main_menu(lang))


@bot.callback_query_handler(func=lambda call: call.data in ["transfer_score", "buy_score"])
def other_options_callback(call):
  uid = str(call.from_user.id)
  data = load_data()
  lang = data.get(uid, {}).get("lang", "dr")
  bot.answer_callback_query(call.id, "🚧 Coming soon!" if lang == "en" else "🚧 این بخش به زودی فعال خواهد شد.", show_alert=True)


@bot.callback_query_handler(func=lambda call: call.data == "support_btn")
def support_callback(call):
  uid = str(call.from_user.id)
  data = load_data()
  lang = data.get(uid, {}).get("lang", "dr")

  if not check_user_membership(uid):
    bot.answer_callback_query(call.id, "❌ Join channels first!" if lang == "en" else "❌ ابتدا باید در کانال و گروه عضو شوید!", show_alert=True)
    return

  bot.answer_callback_query(call.id)
  msg = bot.send_message(call.message.chat.id, TRANSLATIONS[lang]["support_prompt"])
  bot.register_next_step_handler(msg, forward_to_support_admin)


def forward_to_support_admin(message):
  uid = str(message.from_user.id)
  data = load_data()
  lang = data.get(uid, {}).get("lang", "dr")

  if message.text and message.text.startswith("/"):
    return

  try:
    admins = load_admins()
    for admin_id in admins:
      try:
        bot.send_message(
            int(admin_id),
            f"📩 **پیام جدید پشتیبانی**\n\n"
            f"👤 از طرف: @{message.from_user.username or 'ندارد'}\n"
            f"🆔 آیدی عددی: `{uid}`\n"
            f"متن پیام زیر را برای پاسخ دادن **ریپلای (Reply)** کنید:",
            parse_mode="Markdown"
        )
        bot.forward_message(int(admin_id), message.chat.id, message.message_id)
      except Exception:
        pass
        
    bot.reply_to(message, TRANSLATIONS[lang]["support_sent"])
  except Exception as e:
    print(f"Error forwarding support message: {e}")


@bot.message_handler(func=lambda message: is_admin(message.from_user.id) and message.reply_to_message is not None)
def admin_reply_to_user(message):
  try:
    replied_msg = message.reply_to_message
    target_uid = None

    if replied_msg.forward_from:
      target_uid = replied_msg.forward_from.id
    else:
      lines = replied_msg.text.split("\n")
      for line in lines:
        if "آیدی عددی:" in line:
          target_uid = line.split("`")[1]
          break
      if not target_uid:
        target_uid = replied_msg.chat.id

    bot.send_message(
        chat_id=int(target_uid),
        text=f"💬 **پاسخ پشتیبانی:**\n\n{message.text}",
        parse_mode="Markdown"
    )
    bot.reply_to(message, "✅ پاسخ شما با موفقیت به کاربر ارسال شد.")
  except Exception as e:
    bot.reply_to(message, f"❌ خطا در ارسال پاسخ: {e}")


@bot.message_handler(commands=["admin"])
def admin_panel(message):
  if not is_admin(message.from_user.id):
    return
  
  markup = types.InlineKeyboardMarkup(row_width=2)
  markup.add(
      types.InlineKeyboardButton("📢 ارسال پیام همگانی", callback_data="admin_broadcast"),
      types.InlineKeyboardButton("📊 آمار کاربران", callback_data="admin_stats")
  )
  bot.reply_to(message, "⚙️ **پنل مدیریت ربات**\nیکی از گزینه‌ها را انتخاب کنید:", reply_markup=markup, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data == "admin_stats")
def admin_stats_callback(call):
  if not is_admin(call.from_user.id):
    return
  data = load_data()
  total_users = len(data)
  bot.answer_callback_query(call.id, f"👥 مجموع کاربران ربات: {total_users} نفر", show_alert=True)


@bot.callback_query_handler(func=lambda call: call.data == "admin_broadcast")
def admin_broadcast_callback(call):
  if not is_admin(call.from_user.id):
    return
  msg = bot.send_message(call.message.chat.id, "✍️ پیام خود را برای ارسال به همه کاربران بنویسید:")
  bot.register_next_step_handler(msg, perform_broadcast)


def perform_broadcast(message):
  data = load_data()
  count = 0
  for uid in data:
    try:
      bot.send_message(int(uid), message.text)
      count += 1
    except:
      pass
  bot.reply_to(message, f"✅ پیام با موفقیت برای {count} کاربر ارسال شد.")


@bot.message_handler(commands=["GROUP"])
def manage_groups_channels(message):
  if str(message.from_user.id) != str(INITIAL_ADMIN_ID):
    bot.reply_to(message, "❌ فقط مالک اصلی ربات اجازه استفاده از این دستور را دارد.")
    return

  markup = types.InlineKeyboardMarkup()
  markup.add(
      types.InlineKeyboardButton("➕ افزودن کانال/گروه", callback_data="grp_add"),
      types.InlineKeyboardButton("🗑️ حذف کانال/گروه", callback_data="grp_remove")
  )
  channels = load_channels()
  ch_list_text = "\n".join([f"📌 {c['name']} | لینک: {c['url']}" for c in channels])
  
  text = f"⚙️ **مدیریت کانال و گروه‌های عضویت اجباری**\n\nلیست فعلی:\n{ch_list_text if channels else 'خالی است'}"
  bot.reply_to(message, text, reply_markup=markup, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data in ["grp_add", "grp_remove"])
def group_callback_handler(call):
  if str(call.from_user.id) != str(INITIAL_ADMIN_ID):
    return
  
  bot.answer_callback_query(call.id)
  if call.data == "grp_add":
    msg = bot.send_message(
        call.message.chat.id,
        "✍️ اطلاعات را با این فرمت بفرستید:\n\n`نام,لینک,آیدی`\n\nمثال:\n`کانال دوم,https://t.me/mychan,@mychan`",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, save_new_channel_step)
  elif call.data == "grp_remove":
    channels = load_channels()
    if not channels:
      bot.send_message(call.message.chat.id, "❌ هیچ کانال یا گروهی ثبت نشده است.")
      return
    
    markup = types.InlineKeyboardMarkup()
    for i, c in enumerate(channels):
      markup.add(types.InlineKeyboardButton(f"حذف: {c['name']}", callback_data=f"del_ch_{i}"))
    bot.send_message(call.message.chat.id, "🗑️ موردی را که می‌خواهید حذف کنید انتخاب کنید:", reply_markup=markup)


def save_new_channel_step(message):
  if str(message.from_user.id) != str(INITIAL_ADMIN_ID):
    return
  try:
    parts = message.text.split(",")
    if len(parts) < 3:
      bot.reply_to(message, "❌ فرمت اشتباه است.")
      return
    name, url, ch_id = parts[0].strip(), parts[1].strip(), parts[2].strip()
    channels = load_channels()
    channels.append({"name": name, "url": url, "id": ch_id})
    save_channels(channels)
    bot.reply_to(message, f"✅ کانال/گروه `{name}` با موفقیت اضافه شد!")
  except Exception as e:
    bot.reply_to(message, f"❌ خطا: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("del_ch_"))
def delete_channel_callback(call):
  if str(call.from_user.id) != str(INITIAL_ADMIN_ID):
    return
  try:
    idx = int(call.data.split("_")[2])
    channels = load_channels()
    if 0 <= idx < len(channels):
      removed = channels.pop(idx)
      save_channels(channels)
      bot.answer_callback_query(call.id, f"✅ {removed['name']} حذف شد.")
      bot.edit_message_text("✅ با موفقیت حذف گردید.", call.message.chat.id, call.message.message_id)
  except Exception as e:
    bot.answer_callback_query(call.id, f"❌ خطا: {e}")


@bot.message_handler(commands=["SHAHID"])
def manage_admins(message):
  if str(message.from_user.id) != str(INITIAL_ADMIN_ID):
    bot.reply_to(message, "❌ فقط مالک اصلی اجازه دارد.")
    return
  args = message.text.split()
  if len(args) < 2:
    bot.reply_to(message, "فرمت صحیح:\n`/SHAHID USER_ID`", parse_mode="Markdown")
    return
  target_uid = args[1]
  admins = load_admins()
  if target_uid in admins:
    admins.remove(target_uid)
    save_admins(admins)
    bot.reply_to(message, f"🗑️ کاربر `{target_uid}` حذف شد.", parse_mode="Markdown")
  else:
    admins.append(target_uid)
    save_admins(admins)
    bot.reply_to(message, f"⭐ کاربر `{target_uid}` اضافه شد.", parse_mode="Markdown")


@bot.message_handler(commands=["add"])
def manage_score(message):
  if not is_admin(message.from_user.id):
    return
  args = message.text.split()
  if len(args) < 3:
    bot.reply_to(message, "❌ فرمت صحیح:\n`/add USER_ID SCORE`", parse_mode="Markdown")
    return
  target_uid = args[1]
  amount = int(args[2])
  data = load_data()
  if target_uid not in data:
    data[target_uid] = {"score": 0, "lang": "dr"}
  data[target_uid]["score"] += amount
  save_data(data)
  bot.reply_to(message, f"✅ امتیاز اضافه شد. موجودی جدید: {data[target_uid]['score']}")


@bot.message_handler(content_types=["document"])
def handle_docs_from_step(message):
  uid = str(message.from_user.id)
  data = load_data()
  lang = data.get(uid, {}).get("lang", "dr")

  if not check_user_membership(uid):
    bot.reply_to(message, "❌ Join channels first!" if lang == "en" else "❌ ابتدا باید در کانال و گروه عضو شوید!")
    return

  if data.get(uid, {}).get("score", 0) < 50:
    msg_text = "❌ Not enough score! Need 50 score." if lang == "en" else "❌ امتیاز شما برای آنلاین کردن ربات کافی نیست (۵۰ امتیاز لازم است)."
    bot.reply_to(message, msg_text)
    return

  file_info = bot.get_file(message.document.file_id)
  downloaded_file = bot.download_file(file_info.file_path)
  path = os.path.join(USER_BOTS_DIR, f"{uid}_bot.py")
  with open(path, "wb") as f:
    f.write(downloaded_file)

  process = subprocess.Popen(["python3", path])
  active_user_processes[uid] = process

  data[uid]["score"] -= 50
  save_data(data)

  success_text = (
      "🚀 **Congratulations! Your bot is now online** ✨\n\n"
      "🤖 Your bot has been activated on the server."
  ) if lang == "en" else (
      "🚀 **تبریک! ربات شما با موفقیت آنلاین و روشن شد** ✨\n\n"
      "🤖 ربات شما آنلاین گردید و روی سرور فعال شد."
  )
  bot.send_message(message.chat.id, success_text, reply_markup=get_main_menu(lang), parse_mode="Markdown")


if __name__ == "__main__":
  print("Bot Manager is running...")
  bot.infinity_polling()
