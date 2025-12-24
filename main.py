import os
import telebot
from telebot import types
from yt_dlp import YoutubeDL
from flask import Flask
from threading import Thread

# --- 1. سيرفر Flask لمنع دخول البوت في وضع "النوم" ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is Running!"

def run():
    # تشغيل السيرفر على المنفذ 8080 وهو المتوافق مع Render
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. إعدادات البوت ---
# سيقوم الكود بقراءة التوكن من Environment Variables في Render باسم BOT_TOKEN
API_TOKEN = os.getenv('BOT_TOKEN')
SNAP_LINK = "https://snapchat.com/t/wxsuV6qD" 

bot = telebot.TeleBot(API_TOKEN)
user_status = {}

# --- 3. نظام التحقق والمتابعة ---
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
        bot.send_message(user_id, "✅ تم تفعيل البوت بنجاح! أرسل الآن رابط الفيديو أو الصور.")
        bot.edit_message_reply_markup(user_id, call.message.message_id, reply_markup=None)

# --- 4. معالج التحميل المطور (يدعم الفيديو والصور Slideshow) ---
@bot.message_handler(func=lambda message: True)
def handle_download(message):
    user_id = message.chat.id
    url = message.text.strip()

    # التحقق من حالة المتابعة
    if user_status.get(user_id) != "verified":
        send_welcome(message)
        return

    # دعم شامل لجميع أنواع روابط تيك توك بما فيها المختصرة vt.tiktok
    if any(x in url for x in ["tiktok.com", "douyin.com"]):
        progress = bot.reply_to(message, "⏳ جاري المعالجة واستخراج المحتوى...")
        try:
            # إعدادات متقدمة لاستخراج البيانات دون تحميلها فوراً
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'format': 'best',
                'extract_flat': False,
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # --- محاولة جلب الصور أولاً (Slideshow) ---
                images_data = info.get('images') or (info.get('entries')[0].get('images') if info.get('entries') else None)
                
                if images_data:
                    media_group = []
                    for img in images_data[:10]: # تليجرام يدعم حد أقصى 10 صور في الرسالة الواحدة
                        img_url = img.get('url')
                        if img_url:
                            media_group.append(types.InputMediaPhoto(img_url))
                    
                    if media_group:
                        bot.send_media_group(user_id, media_group)
                        bot.delete_message(user_id, progress.message_id)
                        return

                # --- إذا لم تكن صور، يتم تحميل الفيديو ---
                file_name = f"video_{user_id}.mp4"
                ydl_opts['outtmpl'] = file_name
                with YoutubeDL(ydl_opts) as ydl_dl:
                    ydl_dl.download([url])
                
                if os.path.exists(file_name):
                    with open(file_name, 'rb') as v:
                        bot.send_video(user_id, v, supports_streaming=True, caption="✅ تم تحميل الفيديو بنجاح")
                    os.remove(file_name) # حذف الملف بعد الإرسال لتوفير المساحة
                
                bot.delete_message(user_id, progress.message_id)
                
        except Exception as e:
            bot.edit_message_text(f"❌ حدث خطأ في التحميل.\nتأكد من أن الرابط عام وليس لحساب خاص.", user_id, progress.message_id)
    else:
        bot.reply_to(message, "❌ الرابط غير مدعوم، يرجى إرسال رابط تيك توك صحيح.")

if __name__ == "__main__":
    # تشغيل سيرفر التنبيه
    keep_alive() 
    # تشغيل البوت مع إعدادات تحمل انقطاع السيرفر
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
