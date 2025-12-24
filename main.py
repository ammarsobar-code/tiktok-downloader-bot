import os
import re
import telebot
from telebot import types
from yt_dlp import YoutubeDL
from flask import Flask
from threading import Thread

# --- 1. إعداد سيرفر Flask للبقاء حياً على Render ---
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
API_TOKEN = '8128459308:AAFHJSWYqowaJbI-M8bzkcgOHZEvaPbMpP0'
SNAP_LINK = "https://snapchat.com/t/wxsuV6qD" 

bot = telebot.TeleBot(API_TOKEN)
user_status = {}

def is_tiktok(url):
    return "tiktok.com" in url

# --- 3. معالج أمر /start (الرسالة الأولى) ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    user_status[user_id] = "step_1"
    
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("تمت المتابعة ✅ Done", callback_data="check_1")
    markup.add(btn)
    
    msg = (
        "أهلاً بك في بوت تحميل مقاطع وصور التيك توك بدون العلامة المائية\n"
        "Welcome to TikTok video and photo downloader bot without watermark\n\n"
        "ولتشغيل البوت يرجى متابعة حسابي في سناب شات أولاً\n"
        "To activate the bot please follow my Snapchat account first\n\n"
        f"{SNAP_LINK}"
    )
    bot.send_message(user_id, msg, reply_markup=markup)

# --- 4. نظام التحقق برسائل منفصلة وجديدة ---
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    user_id = call.message.chat.id
    
    # عند الضغط أول مرة (إرسال رسالة فشل جديدة)
    if call.data == "check_1":
        user_status[user_id] = "step_2"
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("تمت المتابعة ✅ Done", callback_data="check_final")
        markup.add(btn)
        
        fail_msg = (
            "لم يتم التحقق من متابعتك لحسابي على سناب شات\n"
            "Your follow to my Snapchat account has not been verified\n\n"
            "برجاء التأكد مرة أخرى\n"
            "Please check again\n\n"
            f"{SNAP_LINK}"
        )
        # إرسال رسالة جديدة تماماً وليس تعديل القديمة
        bot.send_message(user_id, fail_msg, reply_markup=markup)
        # حذف أزرار الرسالة القديمة لترتيب المحادثة
        bot.edit_message_reply_markup(user_id, call.message.message_id, reply_markup=None)

    # عند الضغط ثاني مرة (إرسال رسالة نجاح جديدة)
    elif call.data == "check_final":
        user_status[user_id] = "verified"
        success_msg = (
            "تم تفعيل البوت بنجاح\n"
            "Bot activated successfully\n\n"
            "الرجاء إرسال رابط تيك توك\n"
            "Please send TikTok link"
        )
        bot.send_message(user_id, success_msg)
        bot.edit_message_reply_markup(user_id, call.message.message_id, reply_markup=None)

# --- 5. معالج التحميل (فيديو بمقاسات صحيحة + صور) ---
@bot.message_handler(func=lambda message: True)
def handle_download(message):
    user_id = message.chat.id
    url = message.text.strip()

    if user_status.get(user_id) != "verified":
        send_welcome(message) # إعادة إرسال رسالة البداية إذا لم يفعل
        return

    if is_tiktok(url):
        progress_msg = bot.reply_to(message, "جاري التحميل... ⏳\nDownloading... ⏳")
        
        try:
            # إعدادات سحب أفضل جودة فيديو أو صور
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'format': 'best',
            }
            
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # أ: دعم الصور (Slideshow)
                images = info.get('images') or (info.get('entries')[0].get('images') if info.get('entries') else None)
                
                if images:
                    media_group = []
                    for i, img in enumerate(images[:10]):
                        cap = "تمت التحميل بنجاح ✅\nDownloaded successfully ✅" if i == 0 else ""
                        media_group.append(types.InputMediaPhoto(img['url'], caption=cap))
                    
                    bot.send_media_group(user_id, media_group)
                    bot.delete_message(user_id, progress_msg.message_id)
                    return

                # ب: دعم الفيديو (مع الحفاظ على المقاسات)
                filename = f"vid_{user_id}.mp4"
                ydl_opts_dl = {'outtmpl': filename, 'format': 'best', 'quiet': True}
                with YoutubeDL(ydl_opts_dl) as ydl_dl:
                    ydl_dl.download([url])
                
                with open(filename, 'rb') as video:
                    bot.send_video(user_id, video, caption="تمت التحميل بنجاح ✅\nDownloaded successfully ✅", supports_streaming=True)
                
                os.remove(filename)
                bot.delete_message(user_id, progress_msg.message_id)
            
        except Exception as e:
            error_msg = (
                "حدث خطأ في التحميل\n"
                "Download error occurred\n\n"
                "للمساهمة الرجاء ابلاغ المطور بالخطأ\n"
                "To contribute, please report the error to the developer"
            )
            bot.edit_message_text(error_msg, user_id, progress_msg.message_id)
            
    else:
        bot.reply_to(message, "الرجاء التحقق من الرابط\nPlease check the link")

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
