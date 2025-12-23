import os
import telebot
from telebot import types
from yt_dlp import YoutubeDL
from flask import Flask
from threading import Thread

# --- إعداد سيرفر Flask لتجاوز مشكلة البورت في Render ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is Running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- إعداد البوت ---
API_TOKEN = os.getenv('BOT_TOKEN')
# ضع رابط حسابك في السناب شات هنا
SNAP_LINK = "https://snapchat.com/t/wxsuV6qD" 
bot = telebot.TeleBot(API_TOKEN)

# قاموس لتخزين حالة المستخدم
user_status = {}

# --- معالج أمر /start ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    
    # المرحلة الأولى: لم يسبق له الضغط على ستارت
    if user_id not in user_status:
        user_status[user_id] = "step_1"
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("تم المتابعة ✅ | Done ✅", callback_data="check_follow")
        markup.add(btn)
        
        msg = (f"أولاً، الرجاء متابعة حسابي في سناب شات لتشغيل البوت:\n"
               f"{SNAP_LINK}\n\n"
               f"-----------------------------------\n"
               f"First, please follow my Snapchat account to activate the bot:\n"
               f"{SNAP_LINK}\n\n"
               f"بعد المتابعة اضغط على الزر بالأسفل.\n"
               f"After following, click the button below.")
        bot.send_message(user_id, msg, reply_markup=markup)
    
    # المرحلة الثانية: بعد ظهور رسالة التنبيه والضغط على ستارت مجدداً
    elif user_status[user_id] == "step_2":
        user_status[user_id] = "verified"
        msg = ("تم تفعيل البوت بنجاح! أرسل الآن رابط تيك توك.\n"
               "-----------------------------------\n"
               "Bot activated successfully! Send TikTok link now.")
        bot.send_message(user_id, msg)
    
    # إذا كان مفعلاً بالفعل
    else:
        bot.send_message(user_id, "أرسل رابط تيك توك | Send TikTok link")

# --- معالج أزرار التحقق ---
@bot.callback_query_handler(func=lambda call: call.data == "check_follow")
def callback_inline(call):
    user_id = call.message.chat.id
    
    if user_status.get(user_id) == "step_1":
        user_status[user_id] = "step_2"
        msg = (f"⚠️ يبدو أنك لم تتابع حسابي في سناب شات بعد!\n"
               f"الرجاء التأكد من المتابعة: {SNAP_LINK}\n"
               f"ثم اضغط /start للبدء.\n\n"
               f"-----------------------------------\n"
               f"⚠️ It seems you haven't followed my Snapchat yet!\n"
               f"Please make sure to follow: {SNAP_LINK}\n"
               f"Then press /start to begin.")
        bot.edit_message_text(msg, user_id, call.message.message_id)

# --- معالج تحميل الفيديو ---
@bot.message_handler(func=lambda message: True)
def handle_download(message):
    user_id = message.chat.id
    url = message.text

    if user_status.get(user_id) != "verified":
        bot.reply_to(message, "الرجاء الضغط على /start أولاً\nPlease press /start first")
        return

    if "tiktok.com" in url:
        progress_msg = bot.reply_to(message, "جاري التحميل... ⏳ | Downloading... ⏳")
        try:
            filename = f"video_{user_id}.mp4"
            ydl_opts = {
                'outtmpl': filename,
                'format': 'best',
                'quiet': True,
            }
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            with open(filename, 'rb') as video:
                bot.send_video(user_id, video, caption="تم تحميل الفيديو بنجاح ✅\nVideo downloaded successfully ✅")
            
            os.remove(filename)
            bot.delete_message(user_id, progress_msg.message_id)
            
        except Exception as e:
            bot.edit_message_text("خطأ في التحميل، تأكد من الرابط.\nDownload error, check the link.", user_id, progress_msg.message_id)
    else:
        bot.reply_to(message, "رابط غير صحيح | Invalid link")

# تشغيل البوت
if __name__ == "__main__":
    keep_alive()
    bot.polling(non_stop=True)