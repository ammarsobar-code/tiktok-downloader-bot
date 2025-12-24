import os
import re
import telebot
from telebot import types
from yt_dlp import YoutubeDL
from flask import Flask
from threading import Thread

# --- 1. إعداد سيرفر Flask (للبقاء حياً على Render) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is Running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 2. إعداد البوت ---
# سيقوم البوت بسحب التوكن من إعدادات ريندر (Environment Variables)
API_TOKEN = '8128459308:AAFHJSWYqowaJbI-M8bzkcgOHZEvaPbMpP0'
ADMIN_ID = '5148560761'
SNAP_LINK = "https://snapchat.com/t/wxsuV6qD" 

bot = telebot.TeleBot(API_TOKEN)
user_status = {}

# دالة للتحقق من الرابط
def is_tiktok(url):
    return "tiktok.com" in url

# --- 3. معالج أمر /start ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    user_status[user_id] = "step_1"
    
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("تمت المتابعة ✅ Done", callback_data="check_follow")
    markup.add(btn)
    
    msg = (
        "أهلاً بك في بوت تحميل مقاطع وصور التيك توك بدون العلامة المائية\n"
        "Welcome to TikTok video and photo downloader bot without watermark\n"
        "ولتشغيل البوت يرجى متابعة حسابي في سناب شات أولاً\n"
        "To activate the bot please follow my Snapchat account first\n\n"
        f"{SNAP_LINK}"
    )
    bot.send_message(user_id, msg, reply_markup=markup)

# --- 4. معالج أزرار التحقق (نظام الخطوتين) ---
@bot.callback_query_handler(func=lambda call: call.data == "check_follow")
def callback_inline(call):
    user_id = call.message.chat.id
    
    if user_status.get(user_id) == "step_1":
        user_status[user_id] = "step_2"
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("تمت المتابعة ✅ Done", callback_data="check_follow")
        markup.add(btn)
        
        fail_msg = (
            "لم يتم التحقق من متابعتك لحسابي على سناب شات\n"
            "Your follow to my Snapchat account has not been verified\n"
            "برجاء التأكد مرة أخرى\n"
            "Please check again\n\n"
            f"{SNAP_LINK}"
        )
        bot.edit_message_text(fail_msg, user_id, call.message.message_id, reply_markup=markup)

    elif user_status.get(user_id) == "step_2":
        user_status[user_id] = "verified"
        success_msg = (
            "تم تفعيل البوت بنجاح\n"
            "Bot activated successfully\n"
            "الرجاء إرسال رابط تيك توك\n"
            "Please send TikTok link"
        )
        bot.edit_message_text(success_msg, user_id, call.message.message_id)

# --- 5. معالج التحميل الرئيسي (فيديو + صور) ---
@bot.message_handler(func=lambda message: True)
def handle_download(message):
    user_id = message.chat.id
    url = message.text.strip()

    if user_status.get(user_id) != "verified":
        bot.reply_to(message, "الرجاء الضغط على /start أولاً\nPlease press /start first")
        return

    if is_tiktok(url):
        progress_msg = bot.reply_to(message, "جاري التحميل... ⏳\nDownloading... ⏳")
        
        try:
            ydl_opts_info = {'quiet': True, 'no_warnings': True}
            with YoutubeDL(ydl_opts_info) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # التعامل مع ألبوم الصور
                if 'images' in info and info['images']:
                    media_group = []
                    for i, img in enumerate(info['images'][:10]):
                        caption = "تمت التحميل بنجاح ✅\nDownloaded successfully ✅" if i == 0 else ""
                        media_group.append(types.InputMediaPhoto(img['url'], caption=caption))
                    bot.send_media_group(user_id, media_group)
                    bot.delete_message(user_id, progress_msg.message_id)
                    return

                # التعامل مع الفيديو
                filename = f"video_{user_id}.mp4"
                ydl_opts_dl = {'outtmpl': filename, 'format': 'best', 'quiet': True}
                with YoutubeDL(ydl_opts_dl) as ydl_dl:
                    ydl_dl.download([url])
                
                with open(filename, 'rb') as video:
                    bot.send_video(user_id, video, caption="تمت التحميل بنجاح ✅\nDownloaded successfully ✅")
                
                os.remove(filename)
                bot.delete_message(user_id, progress_msg.message_id)
            
        except Exception as e:
            error_text = (
                "حدث خطأ في التحميل\n"
                "Download error occurred\n"
                "للمساهمة الرجاء ابلاغ المطور بالخطأ\n"
                "To contribute, please report the error to the developer"
            )
            bot.edit_message_text(error_text, user_id, progress_msg.message_id)
            if ADMIN_ID:
                bot.send_message(ADMIN_ID, f"🚨 Error: {str(e)[:150]}")
            
    else:
        bot.reply_to(message, "الرجاء التحقق من الرابط\nPlease check the link")

# --- 6. تشغيل البوت ---
if __name__ == "__main__":
    keep_alive() # تشغيل سيرفر ويب صغير في الخلفية
    print("Bot is Running on Render...")
    bot.infinity_polling()

