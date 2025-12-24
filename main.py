import os
import telebot
from telebot import types
from yt_dlp import YoutubeDL
from flask import Flask
from threading import Thread
import requests

app = Flask('')
@app.route('/')
def home(): return "Active"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

API_TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(API_TOKEN)
user_status = {}

@bot.message_handler(commands=['start'])
def start(message):
    user_status[message.chat.id] = "verified" # للتجربة الآن تخطينا التحقق للتأكد من الصور
    bot.reply_to(message, "✅ أرسل رابط الصور الآن للتجربة.")

@bot.message_handler(func=lambda message: True)
def handle(message):
    url = message.text.strip()
    if "tiktok.com" in url:
        prog = bot.reply_to(message, "📸 جاري محاولة صيد الصور...")
        try:
            # إعدادات خاصة جداً للصور
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'skip_download': True,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                }
            }
            
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # فحص كل المسارات الممكنة للصور في بيانات تيك توك الجديدة
                imgs = info.get('images') or \
                       (info.get('entries')[0].get('images') if info.get('entries') else None) or \
                       info.get('thumbnails')

                if imgs and len(imgs) > 1: # إذا كان أكثر من صورة واحدة (سلايدشو)
                    media = []
                    for i in imgs:
                        u = i.get('url')
                        if u and not u.endswith('.webp'): # تليجرام يفضل jpg/png
                            media.append(types.InputMediaPhoto(u))
                        if len(media) == 10: break # حد تليجرام
                    
                    if media:
                        bot.send_media_group(message.chat.id, media)
                        bot.delete_message(message.chat.id, prog.message_id)
                        return

                # إذا لم تكن صور، يحمل فيديو كخيار بديل
                bot.edit_message_text("🎥 لم أجد صوراً، سأحاول تحميله كفيديو...", message.chat.id, prog.message_id)
                ydl_opts['skip_download'] = False
                ydl_opts['outtmpl'] = f'vid_{message.chat.id}.mp4'
                with YoutubeDL(ydl_opts) as ydl_v:
                    ydl_v.download([url])
                with open(f'vid_{message.chat.id}.mp4', 'rb') as v:
                    bot.send_video(message.chat.id, v)
                os.remove(f'vid_{message.chat.id}.mp4')
                bot.delete_message(message.chat.id, prog.message_id)

        except Exception as e:
            bot.edit_message_text(f"❌ فشل الصيد: {str(e)[:50]}", message.chat.id, prog.message_id)

keep_alive()
bot.infinity_polling()
