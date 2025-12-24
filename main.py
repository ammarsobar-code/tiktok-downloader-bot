import os
import re
import telebot
from telebot import types
from yt_dlp import YoutubeDL
from flask import Flask
from threading import Thread

# --- 1. إعداد سيرفر Flask للبقاء حياً ---
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

# --- 3. معالج أمر /start ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    user_status[user_id] = "step_1"
    
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("تمت المتابعة ✅ Done", callback_data="check_1")
    markup.add(btn)
    
    msg = (
        "أهلاً بك في بوت تحميل مقاطع وصور التيك توك بدون العلامة المائية\n"
        "Welcome to TikTok video and photo downloader bot without watermark\n"
        "ولتشغيل البوت يرجى متابعة حسابي في سناب شات أولاً\n"
        "To activate the bot please follow my Snapchat account first\n\n"
        f"{SNAP_LINK}"
    )
    bot.send_message(user_id, msg, reply_markup=markup)

# --- 4. نظام التحقق بخطوات منفصلة ---
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    user_id = call.message.chat.id
    
    if call.data == "check_1":
        user_status[user_id] = "step_2"
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("تأكيد المتابعة ✅ Confirm", callback_data="check_final")
        markup.add(btn)
        
        fail_msg = (
            "لم يتم التحقق من متابعتك لحسابي على سناب شات\n"
            "Your follow to my Snapchat account has not been verified\n"
            "برجاء التأكد مرة أخرى من المتابعة ثم اضغط تأكيد\n"
            "Please make sure to follow then press confirm\n\n"
            f"{SNAP_LINK}"
        )
        bot.edit_message_text(fail_msg, user_id, call.message.message_id, reply_markup=markup)

    elif call.data == "check_final":
        user_status[user_id] = "verified"
        success_msg = (
            "تم تفعيل البوت بنجاح\n"
            "Bot activated successfully\n"
            "الرجاء إرسال رابط تيك توك (فيديو أو صور)\n"
            "Please send TikTok link (video or photos)"
        )
        bot.edit_message_text(success_msg, user_id, call.message.message_id)

# --- 5. معالج التحميل الرئيسي (فيديو بمقاسات صحيحة + صور) ---
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
            # إعدادات متطورة لجلب أفضل جودة وفصل الصور عن الفيديو
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best', # للحفاظ على المقاسات والجودة
            }
            
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # أ: إذا كان الرابط ألبوم صور
                if 'entries' in info or info.get('format_id') == 'images':
                    # استخراج الصور سواء كانت في entries أو قائمة مباشرة
                    images_data = info.get('entries', [info])[0].get('images', [])
                    if not images_data: # محاولة أخرى لاستخراج الصور
                        images_data = info.get('images', [])

                    if images_data:
                        media_group = []
                        for i, img in enumerate(images_data[:10]):
                            link = img.get('url')
                            cap = "تمت التحميل بنجاح ✅\nDownloaded successfully ✅" if i == 0 else ""
                            media_group.append(types.InputMediaPhoto(link, caption=cap))
                        
                        bot.send_media_group(user_id, media_group)
                        bot.delete_message(user_id, progress_msg.message_id)
                        return

                # ب: إذا كان الرابط فيديو
                filename = f"vid_{user_id}.mp4"
                ydl_opts_dl = {'outtmpl': filename, 'format': 'best', 'quiet': True}
                with YoutubeDL(ydl_opts_dl) as ydl_dl:
                    ydl_dl.download([url])
                
                with open(filename, 'rb') as video:
                    # إرسال الفيديو مع تحديد الأبعاد تلقائياً
                    bot.send_video(user_id, video, caption="تمت التحميل بنجاح ✅\nDownloaded successfully ✅", supports_streaming=True)
                
                os.remove(filename)
                bot.delete_message(user_id, progress_msg.message_id)
            
        except Exception as e:
            error_text = (
                "حدث خطأ في التحميل، تأكد من أن الرابط عام وليس خاص\n"
                "Download error, make sure the link is public\n"
                "للمساعدة تواصل مع المطور\n"
                "For help contact the developer"
            )
            bot.edit_message_text(error_text, user_id, progress_msg.message_id)
            
    else:
        bot.reply_to(message, "الرجاء التحقق من الرابط\nPlease check the link")

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
