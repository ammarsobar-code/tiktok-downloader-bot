import os, telebot, requests, time
from telebot import types
from flask import Flask
from threading import Thread

# --- 1. سيرفر Flask للحفاظ على نشاط البوت ---
app = Flask('')
@app.route('/')
def home(): return "TikTok Downloader Live"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. إعدادات البوت ---
API_TOKEN = os.getenv('BOT_TOKEN')
SNAP_LINK = "https://snapchat.com/t/wxsuV6qD" 
bot = telebot.TeleBot(API_TOKEN)
user_status = {}

# --- 3. نظام التحقق والمتابعة (Bold + HTML) ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    welcome_text = (
        "<b>اهلا بك 👋🏼</b>\n"
        "شكرا لاستخدامك بوت تحميل مقاطع تيك توك\n"
        "<b>⚠️ أولاً سيجب عليك متابعة حسابي في سناب شات لتشغيل البوت</b>\n\n"
        "<b>Welcome 👋🏼</b>\n"
        "Thank you for using TikTok Downloader Bot\n"
        "<b>⚠️ First, you'll need to follow my Snapchat account to activate the bot</b>"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("متابعة الحساب 👻 Follow", url=SNAP_LINK))
    markup.add(types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data="tt_step_1"))
    bot.send_message(user_id, welcome_text, reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: True)
def handle_verification(call):
    user_id = call.message.chat.id
    if call.data == "tt_step_1":
        fail_msg = (
            "<b>نعتذر منك لم يتم التحقق من متابعتك لحساب سناب شات ❌👻</b>\n"
            "الرجاء الضغط على متابعة الحساب وسيتم توجيهك لسناب شات وبعد المتابعة اضغط على زر <b>تفعيل البوت 🔓</b>\n\n"
            "<b>We apologize, but your Snapchat account follow request has not been verified. ❌👻</b>\n"
            "Please click Follow Account and you will be redirected to Snapchat. After following, click the <b>Activate</b> button. 🔓"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("متابعة الحساب 👻 Follow", url=SNAP_LINK))
        markup.add(types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data="tt_step_2"))
        bot.send_message(user_id, fail_msg, reply_markup=markup, parse_mode='HTML')
    elif call.data == "tt_step_2":
        user_status[user_id] = "verified"
        bot.send_message(user_id, "<b>تم تفعيل البوت بنجاح ✅\nالرجاء ارسال الرابط 🔗\n\n<b>The bot has been successfully activated ✅</b></b>", parse_mode='HTML')

# --- 4. معالج تحميل تيك توك المطور ---
@bot.message_handler(func=lambda message: True)
def handle_tiktok(message):
    user_id = message.chat.id
    url = message.text.strip()

    if user_status.get(user_id) != "verified":
        send_welcome(message)
        return

    if "tiktok.com" in url or "douyin.com" in url:
        prog = bot.reply_to(message, "<b>جاري التحميل ... ⏳\nLoading... ⏳</b>", parse_mode='HTML')
        
        try:
            api_url = f"https://www.tikwm.com/api/?url={url}"
            response = requests.get(api_url).json()
            
            if response.get('code') == 0:
                data = response['data']
                
                # 1. تحميل الصور (Slideshow)
                images = data.get('images')
                if images:
                    media_group = [types.InputMediaPhoto(img_url) for img_url in images[:10]]
                    bot.send_media_group(user_id, media_group)
                
                # 2. تحميل الفيديو (بدون علامة مائية)
                else:
                    video_url = data.get('play')
                    if video_url:
                        bot.send_video(user_id, video_url)
                
                bot.send_message(user_id, "<b>تم التحميل ✅\nDone ✅</b>", parse_mode='HTML')
                bot.delete_message(user_id, prog.message_id)
                
            else:
                raise Exception("API Error")
        
        except Exception:
            # رسالة المشكلة التقنية بالخط العريض
            error_tech = (
                "<b>نعتذر منك نواجه الان مشكله تقنية وسيتم معالجتها في أقرب وقت ❌</b>\n\n"
                "<b>We apologize, we are currently experiencing a technical issue and it will be resolved as soon as possible ❌</b>"
            )
            bot.edit_message_text(error_tech, user_id, prog.message_id, parse_mode='HTML')
    else:
        bot.reply_to(message, "<b>الرجاء ارسال الرابط الصحيح ❌\nPlease send the correct link ❌</b>", parse_mode='HTML')

# --- 5. التشغيل الآمن ---
if __name__ == "__main__":
    keep_alive()
    try:
        bot.remove_webhook()
    except:
        pass
    time.sleep(1)
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
