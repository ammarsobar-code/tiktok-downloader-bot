import os, telebot, yt_dlp, time
from telebot import types
from flask import Flask
from threading import Thread

# --- 1. سيرفر Flask ---
app = Flask('')
@app.route('/')
def home(): return "X Downloader is Live!"
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

# --- 3. نظام التحقق والمتابعة ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    welcome_text = (
        "اهلا بك 👋🏼\n"
        "شكرا لاستخدامك بوت حفظ السنابات 👻\n"
        "أولا سيجب عليك متابعة حسابي في سناب شات لتشغيل البوت \n"
        "ثم الضغط على /start \n\n"
        "Welcome 👋🏼\n"
        "Thank you for using the Snap Saver Bot 👻\n"
        "First, you'll need to follow my Snapchat account to activate the bot\n"
        "Then, click on /start"
    )
    markup = types.InlineKeyboardMarkup()
    btn_follow = types.InlineKeyboardButton("متابعة الحساب 👻 Follow", url=SNAP_LINK)
    btn_confirm = types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data="verify_x")
    markup.add(btn_follow)
    markup.add(btn_confirm)
    bot.send_message(user_id, welcome_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "verify_x")
def verify_user(call):
    user_id = call.message.chat.id
    user_status[user_id] = "verified"
    success_text = (
        "تم تفعيل البوت بنجاح ✅\n"
        "الرجاء ارسال الرابط 🔗\n\n"
        "The bot has been successfully activated ✅ \n"
        "Please send the link 🔗"
    )
    bot.delete_message(user_id, call.message.message_id)
    bot.send_message(user_id, success_text)

# --- 4. معالج تحميل منصة X ---
@bot.message_handler(func=lambda message: True)
def handle_x(message):
    user_id = message.chat.id
    url = message.text.strip()

    if user_status.get(user_id) != "verified":
        send_welcome(message)
        return

    if "x.com" in url or "twitter.com" in url:
        loading_msg = "جاري التحميل ... ⏳\nLoading... ⏳"
        prog = bot.reply_to(message, loading_msg)
        
        ydl_opts = {'format': 'best', 'quiet': True, 'no_warnings': True}
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                video_url = info.get('url')
                
                if video_url:
                    bot.send_video(user_id, video_url)
                    bot.send_message(user_id, "تم التحميل ✅\nDone ✅")
                    bot.delete_message(user_id, prog.message_id)
                else:
                    raise Exception()
        except:
            tech_error = (
                "نعتذر منك نواجه الان مشكله تقنية وسيتم معالجتها في أقرب وقت ❌\n\n"
                "We apologize, we are currently experiencing a technical issue and it will be resolved as soon as possible ❌"
            )
            bot.edit_message_text(tech_error, user_id, prog.message_id)
    else:
        bot.reply_to(message, "الرجاء ارسال رابط الصحيح ❌\nPlease send the correct link ❌")

# --- 5. التشغيل الآمن ---
if __name__ == "__main__":
    keep_alive()
    # تنظيف شامل قبل التشغيل
    bot.remove_webhook()
    time.sleep(1) # تأخير بسيط لضمان استقرار الاتصال
    print("X Bot is starting...")
    # استخدام skip_pending_updates من خلال polling
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
