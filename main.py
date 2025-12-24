import os
import telebot
from telebot import types
import requests
from flask import Flask
from threading import Thread

# --- 1. سيرفر Flask لمنع النوم ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Live!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. إعدادات البوت ---
API_TOKEN = os.getenv('BOT_TOKEN')
SNAP_LINK = "https://snapchat.com/t/wxsuV6qD" 
bot = telebot.TeleBot(API_TOKEN)
user_status = {}

# --- 3. نظام التحقق (رسائل منفصلة بتنسيق موحد) ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    user_status[user_id] = "step_1"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ تمت المتابعة | Done", callback_data="check_1"))
    
    msg = f"⚠️ يرجى متابعة حسابي أولاً لتفعيل البوت:\nPlease follow my account first:\n\n{SNAP_LINK}"
    bot.send_message(user_id, msg, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    user_id = call.message.chat.id
    if call.data == "check_1":
        user_status[user_id] = "step_2"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ تأكيد | Confirm", callback_data="check_final"))
        bot.send_message(user_id, f"❌ لم يتم التحقق بعد، تأكد من المتابعة ثم اضغط تأكيد\nVerification failed, make sure to follow then confirm:\n\n{SNAP_LINK}", reply_markup=markup)
        bot.edit_message_reply_markup(user_id, call.message.message_id, reply_markup=None)
    
    elif call.data == "check_final":
        user_status[user_id] = "verified"
        bot.send_message(user_id, "✅ تم تفعيل البوت بنجاح! أرسل الرابط الآن\nBot activated successfully! Send the link now")
        bot.edit_message_reply_markup(user_id, call.message.message_id, reply_markup=None)

# --- 4. معالج التحميل باستخدام الـ API الخارجي ---
@bot.message_handler(func=lambda message: True)
def handle_tiktok(message):
    user_id = message.chat.id
    url = message.text.strip()

    if user_status.get(user_id) != "verified":
        send_welcome(message)
        return

    if "tiktok.com" in url or "douyin.com" in url:
        prog = bot.reply_to(message, "⏳ جاري التحميل... | Downloading...")
        try:
            api_url = f"https://www.tikwm.com/api/?url={url}"
            response = requests.get(api_url).json()
            
            if response.get('code') == 0:
                data = response['data']
                
                # تحميل الصور (Slideshow)
                images = data.get('images')
                if images:
                    media_group = []
                    for img_url in images[:10]:
                        media_group.append(types.InputMediaPhoto(img_url))
                    bot.send_media_group(user_id, media_group)
                    bot.delete_message(user_id, prog.message_id)
                    return

                # تحميل الفيديو
                video_url = data.get('play')
                if video_url:
                    bot.send_video(user_id, video_url, caption="✅ تم التحميل بنجاح | Downloaded Successfully")
                    bot.delete_message(user_id, prog.message_id)
                    return
            else:
                bot.edit_message_text("❌ فشل جلب الرابط، تأكد أنه ليس حساباً خاصاً\nFailed to get link, make sure it's not private", user_id, prog.message_id)
        
        except Exception as e:
            bot.edit_message_text(f"❌ خطأ تقني | Technical Error", user_id, prog.message_id)
    else:
        bot.reply_to(message, "❌ يرجى إرسال رابط صحيح | Please send a valid link")

keep_alive()
bot.infinity_polling()
