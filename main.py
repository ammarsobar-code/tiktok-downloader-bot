import os
import telebot
from yt_dlp import YoutubeDL

# ضع التوكن الخاص بك هنا أو استخدم متغيرات البيئة (أفضل للأمان)
API_TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "أهلاً بك! أرسل لي رابط فيديو تيك توك وسأقوم بتحميله لك.")

@bot.message_handler(func=lambda message: True)
def download_video(message):
    url = message.text
    if "tiktok.com" in url:
        msg = bot.reply_to(message, "جاري معالجة الفيديو... انتظر قليلاً ⏳")
        try:
            ydl_opts = {
                'outtmpl': 'video.mp4',
                'format': 'best',
            }
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            with open('video.mp4', 'rb') as video:
                bot.send_video(message.chat.id, video)
            
            os.remove('video.mp4') # حذف الفيديو بعد الإرسال لتوفير المساحة
            bot.delete_message(message.chat.id, msg.message_id)
        except Exception as e:
            bot.edit_message_text(f"حدث خطأ أثناء التحميل: {e}", message.chat.id, msg.message_id)
    else:
        bot.reply_to(message, "عذراً، أرسل رابط تيك توك صحيح فقط.")

bot.polling()