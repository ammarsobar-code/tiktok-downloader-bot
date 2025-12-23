import os
import telebot
from yt_dlp import YoutubeDL
from flask import Flask
from threading import Thread

# إعداد سيرفر بسيط لإرضاء Render
app = Flask('')

@app.route('/')
def home():
    return "I am alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# إعداد البوت
API_TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "أهلاً بك! أرسل رابط تيك توك للتحميل.")

@bot.message_handler(func=lambda message: True)
def download_video(message):
    url = message.text
    if "tiktok.com" in url:
        msg = bot.reply_to(message, "جاري معالجة الفيديو... ⏳")
        try:
            ydl_opts = {'outtmpl': 'video.mp4', 'format': 'best'}
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            with open('video.mp4', 'rb') as video:
                bot.send_video(message.chat.id, video)
            
            os.remove('video.mp4')
            bot.delete_message(message.chat.id, msg.message_id)
        except Exception as e:
            bot.edit_message_text(f"خطأ: {e}", message.chat.id, msg.message_id)

if __name__ == "__main__":
    keep_alive()  # تشغيل السيرفر الوهمي
    bot.polling(non_stop=True)