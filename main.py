import os
import telebot
from telebot import types
from yt_dlp import YoutubeDL
from flask import Flask
from threading import Thread

# --- 1. سيرفر Flask الصغير (لحل مشكلة البورت في Render) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is Running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 2. إعدادات البوت ---
API_TOKEN = os.getenv('BOT_TOKEN')
SNAP_LINK = "https://snapchat.com/t/wxsuV6qD" # ضع حسابك هنا
bot = telebot.TeleBot(API_TOKEN)

# لتخزين من ضغط على زر المتابعة
verified_users = set()

# --- 3. الدوال المساعدة للنصوص ---
def send_follow_request(chat_id):
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("تم المتابعة ✅ | Done ✅", callback_data="verify_me")
    markup.add(btn)
    
    text = (f"أولاً، الرجاء متابعة حسابي في سناب شات لتشغيل البوت:\n{SNAP_LINK}\n\n"
            f"-----------------------------------\n"
            f"First, please follow my Snapchat account to activate the bot:\n{SNAP_LINK}")
    bot.send_message(chat_id, text, reply_markup=markup)

# --- 4. معالجة زر "تم المتابعة" (خطوة واحدة فقط) ---
@bot.callback_query_handler(func=lambda call: call.data == "verify_me")
def verify_user(call):
    user_id = call.message.chat.id
    verified_users.add(user_id)
    
    success_text = ("تم تفعيل البوت بنجاح! ✅ أرسل الآن رابط تيك توك.\n"
                    "-----------------------------------\n"
                    "Bot activated successfully! ✅ Send TikTok link now.")
    bot.edit_message_text(success_text, user_id, call.message.message_id)

# --- 5. معالج الرسائل الرئيسي ---
@bot.message_handler(func=lambda message: True)
def handle_all(message):
    user_id = message.chat.id
    text = message.text

    # إذا لم يضغط المستخدم على الزر بعد
    if user_id not in verified_users:
        send_follow_request(user_id)
        return

    # إذا كان المستخدم مفعلاً
    if "tiktok.com" in text:
        progress_msg = bot.reply_to(message, "جاري التحميل... ⏳ | Downloading... ⏳")
        try:
            filename = f"video_{user_id}.mp4"
            ydl_opts = {
                'outtmpl': filename,
                'format': 'best',
                'quiet': True,
                'no_warnings': True
            }
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([text])
            
            with open(filename, 'rb') as video:
                bot.send_video(user_id, video, caption="تم تحميل الفيديو بنجاح ✅\nVideo downloaded successfully ✅")
            
            os.remove(filename)
            bot.delete_message(user_id, progress_msg.message_id)
            
        except Exception:
            bot.edit_message_text("حدث خطأ، تأكد من الرابط.\nError, check the link.", user_id, progress_msg.message_id)
    
    else:
        # إذا أرسل أي شيء غير رابط تيك توك
        bot.reply_to(message, "⚠️ عذراً، هذا ليس رابط تيك توك صحيح!\n"
                             "-----------------------------------\n"
                             "⚠️ Sorry, this is not a valid TikTok link!")

# تشغيل البوت
if __name__ == "__main__":
    keep_alive()
    bot.polling(non_stop=True)

