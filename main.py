import os
import telebot
from telebot import types
import requests
from flask import Flask
from threading import Thread

# --- سيرفر Flask لمنع النوم ---
app = Flask('')
@app.route('/')
def home(): return "API Bot is Live!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

API_TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "✅ تم الربط بـ API الصور! أرسل رابط (سلايدشو) تيك توك الآن.")

@bot.message_handler(func=lambda message: True)
def handle_tiktok(message):
    url = message.text.strip()
    if "tiktok.com" in url:
        prog = bot.reply_to(message, "🚀 جاري سحب الصور عبر API...")
        try:
            # استخدام API خارجي مجاني لفك تشفير الرابط
            api_url = f"https://www.tikwm.com/api/?url={url}"
            response = requests.get(api_url).json()
            
            if response.get('code') == 0:
                data = response['data']
                
                # 1. إذا كان المنشور عبارة عن صور (Slideshow)
                images = data.get('images')
                if images:
                    media_group = []
                    for img_url in images[:10]: # حد تليجرام 10 صور
                        media_group.append(types.InputMediaPhoto(img_url))
                    
                    bot.send_media_group(message.chat.id, media_group)
                    bot.delete_message(message.chat.id, prog.message_id)
                    return

                # 2. إذا كان فيديو (بدون علامة مائية)
                video_url = data.get('play')
                if video_url:
                    bot.send_video(message.chat.id, video_url, caption="✅ تم التحميل عبر API")
                    bot.delete_message(message.chat.id, prog.message_id)
                    return
            else:
                bot.edit_message_text("❌ الـ API لم يستطع قراءة هذا الرابط.", message.chat.id, prog.message_id)
        
        except Exception as e:
            bot.edit_message_text(f"❌ خطأ في الاتصال بالـ API: {str(e)[:50]}", message.chat.id, prog.message_id)
    else:
        bot.reply_to(message, "❌ يرجى إرسال رابط تيك توك فقط.")

keep_alive()
bot.infinity_polling()
