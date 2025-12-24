import os
import telebot
from telebot import types
from yt_dlp import YoutubeDL
from flask import Flask
from threading import Thread

# --- 1. سيرفر Flask لمنع النوم ---
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
SNAP_LINK = "https://snapchat.com/t/wxsuV6qD" 

bot = telebot.TeleBot(API_TOKEN)
user_status = {}

# --- 3. نظام التحقق (رسائل منفصلة) ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    user_status[user_id] = "step_1"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("تمت المتابعة ✅ Done", callback_data="check_1"))
    
    msg = f"⚠️ يرجى متابعة حسابي في سناب شات أولاً لتفعيل البوت:\n\n{SNAP_LINK}"
    bot.send_message(user_id, msg, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    user_id = call.message.chat.id
    if call.data == "check_1":
        user_status[user_id] = "step_2"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("تأكيد المتابعة ✅ Confirm", callback_data="check_final"))
        bot.send_message(user_id, "❌ لم يتم التحقق، تأكد من المتابعة ثم اضغط تأكيد.\n" + SNAP_LINK, reply_markup=markup)
        bot.edit_message_reply_markup(user_id, call.message.message_id, reply_markup=None)
    elif call.data == "check_final":
        user_status[user_id] = "verified"
        bot.send_message(user_id, "✅ تم تفعيل البوت! أرسل الآن رابط الفيديو أو الصور.")
        bot.edit_message_reply_markup(user_id, call.message.message_id, reply_markup=None)

# --- 4. معالج التحميل الذكي ---
@bot.message_handler(func=lambda message: True)
def handle_download(message):
    user_id = message.chat.id
    url = message.text.strip()

    if user_status.get(user_id) != "verified":
        send_welcome(message)
        return

    # فحص شامل لروابط تيك توك بجميع أنواعها
    is_tiktok = any(x in url for x in ["tiktok.com", "douyin.com"])
    
    if is_tiktok:
        progress = bot.reply_to(message, "⏳ جاري التحميل ومعالجة الرابط...")
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'format': 'best',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # أولاً: محاولة جلب الصور (Slideshow)
                images_list = info.get('images') or (info.get('entries')[0].get('images') if info.get('entries') else None)
                
                if images_list:
                    media_group = []
                    for img in images_list[:10]: # حد أقصى 10 صور
                        if img.get('url'):
                            media_group.append(types.InputMediaPhoto(img['url']))
                    
                    if media_group:
                        bot.send_media_group(user_id, media_group)
                        bot.delete_message(user_id, progress.message_id)
                        return

                # ثانياً: إذا لم تكن صور، نحمل الفيديو
                file_name = f"video_{user_id}.mp4"
                ydl_opts['outtmpl'] = file_name
                with YoutubeDL(ydl_opts) as ydl_dl:
                    ydl_dl.download([url])
                
                with open(file_name, 'rb') as v:
                    bot.send_video(user_id, v, supports_streaming=True, caption="تم التحميل بنجاح ✅")
                
                os.remove(file_name)
                bot.delete_message(user_id, progress.message_id)
                
        except Exception as e:
            bot.edit_message_text(f"❌ حدث خطأ أثناء التحميل.\nتأكد أن الحساب ليس خاصاً (Private).", user_id, progress.message_id)
    else:
        bot.reply_to(message, "❌ هذا الرابط غير مدعوم، يرجى إرسال رابط تيك توك صحيح.")

if __name__ == "__main__":
    keep_alive() 
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
