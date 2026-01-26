import os
import telebot
import requests
import time
import sys
import subprocess
import shutil
from telebot import types
from flask import Flask
from threading import Thread
from yt_dlp import YoutubeDL

# --- 1. سيرفر Flask للحفاظ على نشاط البوت على Koyeb ---
app = Flask('')

@app.route('/')
def home():
    return "TikTok Ultra Bot is Online 24/7"

def run():
    # تعديل المنفذ ليتوافق مع إعدادات Koyeb التي ظهرت في صورك (8000)
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. وظيفة التنظيف التلقائي (Auto-Clean) ---
def auto_clean_environment():
    """تنظيف مخلفات المعالجة والذاكرة لضمان استمرار البوت بدون ريستارت"""
    try:
        # مسح كاش yt-dlp لمنع أخطاء الحظر 403
        subprocess.run([sys.executable, "-m", "yt_dlp", "--rm-cache-dir"], stderr=subprocess.DEVNULL)
        
        # قتل أي عملية معالجة فيديو لم تنتهِ في الخلفية
        if os.name != 'nt':
            subprocess.run(["pkill", "-9", "-f", "yt-dlp"], stderr=subprocess.DEVNULL)
            
        # تنظيف مجلد التحميلات إذا وُجد
        if os.path.exists("downloads"):
            shutil.rmtree("downloads", ignore_errors=True)
            os.makedirs("downloads", exist_ok=True)
            
    except:
        pass

# --- 3. إعدادات البوت ---
API_TOKEN = os.getenv('BOT_TOKEN')
SNAP_LINK = "https://snapchat.com/t/wxsuV6qD" 
bot = telebot.TeleBot(API_TOKEN)
user_status = {}

# --- 4. وظائف التحميل ---

def get_tikwm(url):
    try:
        res = requests.get(f"https://www.tikwm.com/api/?url={url}", timeout=10).json()
        if res.get('code') == 0:
            return res['data']
    except:
        return None

def get_ytdlp(url):
    try:
        ydl_opts = {
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
            'cachedir': False
        }
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {'play': info['url']}
    except:
        return None

# --- 5. نظام التحقق والمتابعة ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    welcome_text = (
        "<b>اهلا بك 👋🏼</b>\n"
        "شكرا لاستخدامك بوت تحميل مقاطع تيك توك\n"
        "<b>⚠️ أولاً سيجب عليك متابعة حسابي في سناب شات لتشغيل البوت</b>"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("متابعة الحساب 👻 Follow", url=SNAP_LINK))
    markup.add(types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data="tt_step_1"))
    bot.send_message(user_id, welcome_text, reply_markup=markup, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: True)
def handle_verification(call):
    user_id = call.message.chat.id
    if call.data == "tt_step_1":
        fail_msg = "<b>نعتذر منك لم يتم التحقق من المتابعة ❌👻</b>"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("متابعة الحساب 👻 Follow", url=SNAP_LINK))
        markup.add(types.InlineKeyboardButton("تفعيل البوت 🔓 Activate", callback_data="tt_step_2"))
        bot.send_message(user_id, fail_msg, reply_markup=markup, parse_mode='HTML')
    elif call.data == "tt_step_2":
        user_status[user_id] = "verified"
        bot.send_message(user_id, "<b>تم تفعيل البوت بنجاح ✅\nالرجاء ارسال الرابط 🔗</b>", parse_mode='HTML')

# --- 6. معالج التحميل الرئيسي ---

@bot.message_handler(func=lambda message: True)
def handle_tiktok(message):
    user_id = message.chat.id
    url = message.text.strip()

    if user_status.get(user_id) != "verified":
        send_welcome(message)
        return

    if "tiktok.com" in url or "douyin.com" in url:
        prog = bot.reply_to(message, "<b>جاري التحميل ... ⏳</b>", parse_mode='HTML')
        
        try:
            # محاولة 1: TikWM
            data = get_tikwm(url)
            
            if data:
                images = data.get('images')
                if images:
                    media_group = [types.InputMediaPhoto(img_url) for img_url in images[:10]]
                    bot.send_media_group(user_id, media_group)
                else:
                    video_url = data.get('play')
                    if video_url:
                        bot.send_video(user_id, video_url, caption="<b>✅ تم التحميل بنجاح</b>", parse_mode='HTML')
                
                bot.delete_message(user_id, prog.message_id)
                return

            # محاولة 2: yt-dlp
            bot.edit_message_text("<b>جاري استخدام المحرك الاحتياطي... ⚙️</b>", user_id, prog.message_id, parse_mode='HTML')
            data_alt = get_ytdlp(url)
            
            if data_alt:
                bot.send_video(user_id, data_alt['play'], caption="<b>✅ تم التحميل (محرك احتياطي)</b>", parse_mode='HTML')
                bot.delete_message(user_id, prog.message_id)
            else:
                bot.edit_message_text("<b>الرابط غير مدعوم حالياً ❌</b>", user_id, prog.message_id, parse_mode='HTML')

        except Exception as e:
            bot.send_message(user_id, "<b>حدث خطأ أثناء المعالجة ❌</b>", parse_mode='HTML')
        
        finally:
            auto_clean_environment()
            
    else:
        bot.reply_to(message, "<b>الرجاء ارسال رابط تيك توك صحيح 🔗</b>", parse_mode='HTML')

# --- 7. التشغيل الآمن ---
if __name__ == "__main__":
    keep_alive()
    auto_clean_environment()
    print("TikTok Bot is starting...")
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
