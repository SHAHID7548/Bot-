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

# سیستم ترجمه (دری و انگلیسی)
TRANSLATIONS = {
    "dr": {
        "welcome": (
            "خوش آمدید! برای روشن کردن ربات خود ۵۰ امتیاز نیاز دارید.\n🔗 لینک"
            " دعوت شما:\n{link}"
        ),
        "profile": (
            "👤 پروفایل شما:\n🆔 آیدی: {id}\n👤 یوزرنیم:"
            " @{username}\n💰 امتیاز: {score}\n\n🔗 لینک دعوت شما:\n{link}"
        ),
        "not_enough": "❌ امتیاز شما کافی نیست (۵۰ امتیاز لازم است).",
        "bot_started": "✅ فایل دریافت شد. ربات شما با موفقیت روشن شد!",
        "ref_bonus": "🎉 یک کاربر با لینک دعوت شما پیوست! +۵ امتیاز دریافت کردید.",
        "support_prompt": "✍️ لطفاً پیام، سؤال یا مشکل خود را ارسال کنید تا به ادمین برسد:",
        "support_sent": "✅ پیام شما با موفقیت به پشتیبانی ارسال شد. به زودی پاسخ داده خواهد شد.",
        "btn_support": "📞 ارتباط با پشتیبانی",
        "join_lock": "🚨 **لطفاً برای استفاده از ربات، ابتدا در کانال و گروه زیر عضو شوید:**",
        "btn_check_join": "✅ عضو شدم، بررسی کن",
        "not_joined_alert": "❌ شما هنوز در تمام کانال‌ها و گروه‌های زیر عضو نشده‌اید!",
    },
    "en": {
        "welcome": (
            "Welcome! You need 50 points to turn on your bot.\n🔗 Your"
            " referral link:\n{link}"
        ),
        "profile": (
            "👤 Your Profile:\n🆔 ID: {id}\n👤 Username:"
            " @{username}\n💰 Score: {score}\n\n🔗 Your Referral Link:\n{link}"
        ),
        "not_enough": "❌ Not enough points (50 required).",
        "bot_started": "✅ File received. Your bot has been successfully started!",
        "ref_bonus": (
            "🎉 A user joined via your link! You received +5 points."
        ),
        "support_prompt": "✍️ Please send your message or question for the support:",
        "support_sent": "✅ Your message has been sent to support. You will receive a reply soon.",
        "btn_support": "📞 Contact Support",
        "join_lock": "🚨 **Please join our channel and group first to use the bot:**",
        "btn_check_join": "✅ I have joined, check",
        "not_joined_alert": "❌ You have not joined all required channels/groups yet!",
    },
}


def load_data():
  if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
      return json.load(f)
  return {}


def save_data(data):
  with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)


# مدیریت لیست ادمین‌ها
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


# مدیریت کانال‌ها و گروه‌های عضویت اجباری
def load_channels():
  if os.path.exists(CHANNELS_FILE):
    with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
      return json.load(f)
  # مقادیر پیش‌فرض درخواست شده شما
  default_channels = [
      {"name": "گروه اول", "url": "https://t.me/hackwhatandetc", "id": "@hackwhatandetc"},
      {"name": "کانال", "url": "https://t.me/hackwhatandetcb", "id": "@hackwhatandetcb"}
  ]
  save_channels(default_channels)
  return default_channels


def save_channels(channels):
  with open(CHANNELS_FILE, "w", encoding="utf-8") as f:
    json.dump(channels, f, ensure_ascii=False, indent=4)


# بررسی عضویت کاربر در کانال‌ها/گروه‌ها
def check_user_membership(user_id):
  channels = load_channels()
  for ch in channels:
    ch_id = ch["id"]
    try:
      member = bot.get_chat_member(ch_id, int(user_id))
      if member.status not in ["member", "administrator", "creator"]:
        return False
    except Exception as e:
      print(f"Error checking membership for {ch_id}: {e}")
      # اگر ربات نتواند بررسی کند (مثلاً ربات ادمین نباشد)، برای جلوگیری از قفل شدن، عبور می‌دهد یا خطا می‌دهد
      pass
  return True


def send_profile_or_welcome(message_or_call, uid):
  data = load_data()
  chat_id = message_or_call.message.chat.id if hasattr(message_or_call, 'message') else message_or_call.chat.id
  user = message_or_call.from_user

  # بررسی عضویت اجباری
  if not check_user_membership(uid):
    lang = data.get(uid, {}).get("lang", "dr")
    channels = load_channels()
    markup = types.InlineKeyboardMarkup()
    for ch in channels:
      markup.add(types.InlineKeyboardButton(ch["name"], url=ch["url"]))
    markup.add(types.InlineKeyboardButton(TRANSLATIONS[lang]["btn_check_join"], callback_data="check_join"))
    
    text = TRANSLATIONS[lang]["join_lock"]
    if hasattr(message_or_call, 'data'):
      bot.answer_callback_query(message_or_call.id, TRANSLATIONS[lang]["not_joined_alert"], show_alert=True)
    else:
      bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")
    return

  ref_link = f"https://t.me/Robat_online_bot?start={uid}"

  if uid not in data:
    data[uid] = {"score": 0, "lang": "dr"}
    save_data(data)

  lang = data[uid]["lang"]
  photos = bot.get_user_profile_photos(user.id)
  text = TRANSLATIONS[lang]["profile"].format(
      id=uid,
      username=user.username or "None",
      score=data[uid]["score"],
      link=ref_link,
  )

  markup = types.InlineKeyboardMarkup()
  markup.add(types.InlineKeyboardButton(TRANSLATIONS[lang]["btn_support"], callback_data="support_btn"))

  if photos.photos:
    bot.send_photo(chat_id, photos.photos[0][0].file_id, caption=text, reply_markup=markup)
  else:
    bot.send_message(chat_id, text, reply_markup=markup)


@bot.message_handler(commands=["start"])
def start(message):
  data = load_data()
  uid = str(message.from_user.id)
  args = message.text.split()

  if uid not in data:
    data[uid] = {"score": 0, "lang": "dr"}
    if len(args) > 1:
      referrer_id = args[1]
      if referrer_id in data and referrer_id != uid:
        data[referrer_id]["score"] += 5
        try:
          lang_ref = data[referrer_id].get("lang", "dr")
          bot.send_message(
              int(referrer_id), TRANSLATIONS[lang_ref]["ref_bonus"]
          )
        except:
          pass
    save_data(data)

  send_profile_or_welcome(message, uid)


@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def check_join_callback(call):
  uid = str(call.from_user.id)
  if check_user_membership(uid):
    bot.answer_callback_query(call.id, "✅ تایید شد! حالا می‌توانید از ربات استفاده کنید.")
    try:
      bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
      pass
    send_profile_or_welcome(call, uid)
  else:
    data = load_data()
    lang = data.get(uid, {}).get("lang", "dr")
    bot.answer_callback_query(call.id, TRANSLATIONS[lang]["not_joined_alert"], show_alert=True)


# مدیریت کلیک روی دکمه پشتیبانی
@bot.callback_query_handler(func=lambda call: call.data == "support_btn")
def support_callback(call):
  uid = str(call.from_user.id)
  data = load_data()
  lang = data.get(uid, {}).get("lang", "dr")
  
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


# مدیریت پاسخ ادمین‌ها به پیام‌های کاربران (با ریپلای کردن)
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


# دستور مدیریت کانال‌ها/گروه‌های جوین اجباری: /GROUP (فقط مالک اصلی)
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
  ch_list_text = "\n".join([f"📌 {c['name']} | آیدی: `{c['id']}` | لینک: {c['url']}" for c in channels])
  
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
        "✍️ لطفاً اطلاعات را با این فرمت ارسال کنید:\n\n`نام,لینک,آیدی`\n\nمثال:\n`کانال دوم,https://t.me/mychan,@mychan`",
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
      bot.reply_to(message, "❌ فرمت اشتباه است. لطفاً دقیقاً مانند مثال بفرستید.")
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
    else:
      bot.answer_callback_query(call.id, "❌ پیدا نشد!")
  except Exception as e:
    bot.answer_callback_query(call.id, f"❌ خطا: {e}")


# دستور مدیریت ادمین‌ها: /SHAHID ایدی_کاربر (فقط توسط مالک اصلی)
@bot.message_handler(commands=["SHAHID"])
def manage_admins(message):
  if str(message.from_user.id) != str(INITIAL_ADMIN_ID):
    bot.reply_to(message, "❌ فقط مالک اصلی ربات اجازه استفاده از این دستور را دارد.")
    return

  args = message.text.split()
  if len(args) < 2:
    bot.reply_to(
        message,
        "دستور اشتباه است.\nفرمت صحیح:\n`/SHAHID USER_ID`",
        parse_mode="Markdown",
    )
    return

  target_uid = args[1]
  if target_uid == str(INITIAL_ADMIN_ID):
    bot.reply_to(message, "❌ شما مالک اصلی ربات هستید و نمی‌توانید خود را از ادمینی خارج کنید.")
    return

  admins = load_admins()
  if target_uid in admins:
    admins.remove(target_uid)
    save_admins(admins)
    bot.reply_to(message, f"🗑️ کاربر `{target_uid}` از لیست ادمین‌ها حذف شد.", parse_mode="Markdown")
  else:
    admins.append(target_uid)
    save_admins(admins)
    bot.reply_to(message, f"⭐ کاربر `{target_uid}` به عنوان ادمین جدید اضافه شد.", parse_mode="Markdown")


# دستور ادمین برای مدیریت امتیاز: /add ID SCORE
@bot.message_handler(commands=["add"])
def manage_score(message):
  if not is_admin(message.from_user.id):
    bot.reply_to(message, "❌ شما دسترسی به این دستور را ندارید.")
    return

  args = message.text.split()
  if len(args) < 3:
    bot.reply_to(
        message,
        "دستور اشتباه است.\nفرمت صحیح:\n`/add ID SCORE`",
        parse_mode="Markdown",
    )
    return

  target_uid = args[1]
  try:
    amount = int(args[2])
  except ValueError:
    bot.reply_to(message, "❌ مقدار امتیاز باید عدد باشد.")
    return

  data = load_data()
  if target_uid not in data:
    data[target_uid] = {"score": 0, "lang": "dr"}

  data[target_uid]["score"] += amount
  save_data(data)

  bot.reply_to(
      message,
      f"✅ موجودی جدید کاربر `{target_uid}` برابر با"
      f" `{data[target_uid]['score']}` شد.",
      parse_mode="Markdown",
  )


# دستور پنل ادمین و ارسال پیام همگانی: /admin
@bot.message_handler(commands=["admin"])
def admin_panel(message):
  if not is_admin(message.from_user.id):
    bot.reply_to(message, "❌ شما دسترسی ندارید.")
    return

  msg = bot.reply_to(
      message,
      "📢 لطفاً پیامی را که می‌خواهید به تمام کاربران ارسال کنید بفرستید:",
  )
  bot.register_next_step_handler(msg, send_broadcast_to_all)


def send_broadcast_to_all(message):
  if not is_admin(message.from_user.id):
    return

  data = load_data()
  success_count = 0
  fail_count = 0

  sent_msg = bot.reply_to(message, "⏳ در حال ارسال پیام به تمام کاربران...")

  for uid in data.keys():
    try:
      bot.copy_message(chat_id=int(uid), from_chat_id=message.chat.id, message_id=message.message_id)
      success_count += 1
    except Exception:
      fail_count += 1

  bot.edit_message_text(
      f"✅ ارسال پیام به پایان رسید!\n\n📤 موفق: {success_count}\n❌ ناموفق"
      f" (بلاک کرده‌اند): {fail_count}",
      chat_id=sent_msg.chat.id,
      message_id=sent_msg.message_id,
  )


@bot.message_handler(content_types=["document"])
def handle_docs(message):
  uid = str(message.from_user.id)
  data = load_data()
  lang = data.get(uid, {}).get("lang", "dr")

  if not check_user_membership(uid):
    bot.reply_to(message, "❌ ابتدا باید در کانال و گروه عضو شوید!")
    return

  if data.get(uid, {}).get("score", 0) < 50:
    bot.reply_to(message, TRANSLATIONS[lang]["not_enough"])
    return

  try:
    admins = load_admins()
    for admin_id in admins:
      try:
        bot.forward_message(int(admin_id), message.chat.id, message.message_id)
        bot.send_message(
            int(admin_id),
            f"📂 فایل جدید از طرف:\n👤 آیدی: `{uid}`\n🔗 یوزرنیم:"
            f" @{message.from_user.username or 'ندارد'}",
            parse_mode="Markdown",
        )
      except Exception:
        pass
  except Exception as e:
    print(f"Error forwarding to admin: {e}")

  file_info = bot.get_file(message.document.file_id)
  downloaded_file = bot.download_file(file_info.file_path)
  path = os.path.join(USER_BOTS_DIR, f"{uid}_bot.py")
  with open(path, "wb") as f:
    f.write(downloaded_file)

  subprocess.Popen(["python3", path])

  data[uid]["score"] -= 50
  save_data(data)

  success_text = (
      "🚀 **تبریک! ربات شما با موفقیت روشن شد** ✨\n\n"
      "🤖 ربات شما توسط مدیریت سیستم (**ریس شاهد**) آنلاین گردید و روی سرور فعال شد.\n\n"
      "💡 اگر می‌خواهید ربات‌های دیگری بسازید یا سؤالی دارید، می‌توانید از طریق دکمه «📞 ارتباط با پشتیبانی» با ما در تماس باشید."
  )
  
  markup = types.InlineKeyboardMarkup()
  markup.add(types.InlineKeyboardButton(TRANSLATIONS[lang]["btn_support"], callback_data="support_btn"))

  bot.send_message(message.chat.id, success_text, reply_markup=markup, parse_mode="Markdown")


if __name__ == "__main__":
  print("Bot Manager is running...")
  bot.infinity_polling()
