import os
import re
import telebot
from telebot import types
from yt_dlp import YoutubeDL

# --- إعدادات أساسية ---
API_TOKEN = '8128459308:AAFHJSWYqowaJbI-M8bzkcgOHZEvaPbMpP0'
ADMIN_ID = '5148560761'
SNAP_LINK = "https://snapchat.com/t/wxsuV6qD"

bot = telebot.TeleBot(API_TOKEN)
verified_users = set()

# دالة للتحقق هل الرابط تيك توك أم لا
def is_tiktok_url(url):
    pattern = r'(https?://)?(www\.|vm\.|vt\.)?tiktok\.com/.*'
    return re.match(pattern, url)

# --- دالة طلب الاشتراك ---
def send_subscription_request(chat_id):
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("تمت المتابعة ✅ Done", callback_data="verify_step")
    markup.add(btn)
    
    text = (
        "أهلاً بك في بوت تحميل مقاطع وصور التيك توك بدون العلامة المائية\n"
        "Welcome to TikTok video and photo downloader bot without watermark\n\n"
        "ولتشغيل البوت يرجى متابعة حسابي في سناب شات أولاً\n"
        "To activate the bot please follow my Snapchat account first\n\n"
        f"{SNAP_LINK}"
    )
    bot.send_message(chat_id, text, reply_markup=markup)

# --- نظام التحقق (الخطأ ثم النجاح) ---
@bot.callback_query_handler(func=lambda call: call.data == "verify_step")
def handle_verification(call):
    user_id = call.message.chat.id
    if user_id not in verified_users:
        verified_users.add(user_id) 
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("تمت المتابعة ✅ Done", callback_data="final_check")
        markup.add(btn)
        
        fail_text = (
            "لم يتم التحقق من متابعتك لحسابي على سناب شات\n"
            "Your follow to my Snapchat account has not been verified\n"
            "برجاء التأكد مرة أخرى\n"
            "Please check again\n\n"
            f"{SNAP_LINK}"
        )
        bot.edit_message_text(fail_text, user_id, call.message.message_id, reply_markup=markup)
    
@bot.callback_query_handler(func=lambda call: call.data == "final_check")
def handle_final_check(call):
    user_id = call.message.chat.id
    success_text = (
        "تم تفعيل البوت بنجاح\n"
        "Bot activated successfully\n"
        "الرجاء إرسال رابط تيك توك\n"
        "Please send TikTok link"
    )
    bot.edit_message_text(success_text, user_id, call.message.message_id)
    verified_users.add(f"active_{user_id}")

# --- معالجة التحميل والفرز ---
@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.chat.id
    url = message.text.strip()
    active_key = f"active_{user_id}"

    # 1. التحقق من التفعيل أولاً
    if active_key not in verified_users:
        send_subscription_request(user_id)
        return

    # 2. التحقق من صحة الرابط (هل هو تيك توك؟)
    if is_tiktok_url(url):
        prog_msg = bot.reply_to(message, "جاري التحميل... ⏳\nDownloading... ⏳")
        
        try:
            ydl_opts = {'quiet': True, 'no_warnings': True}
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # التعامل مع الصور (Slideshow)
                if 'images' in info and info['images']:
                    media_group = []
                    for i, img in enumerate(info['images'][:10]):
                        cap = "تمت التحميل بنجاح ✅\nDownloaded successfully ✅" if i == 0 else ""
                        media_group.append(types.InputMediaPhoto(img['url'], caption=cap))
                    bot.send_media_group(user_id, media_group)
                    bot.delete_message(user_id, prog_msg.message_id)
                    return

                # التعامل مع الفيديو
                filename = f"vid_{user_id}.mp4"
                ydl_opts_dl = {'outtmpl': filename, 'format': 'best', 'quiet': True}
                with YoutubeDL(ydl_opts_dl) as ydl_dl:
                    ydl_dl.download([url])
                
                with open(filename, 'rb') as video:
                    bot.send_video(user_id, video, caption="تمت التحميل بنجاح ✅\nDownloaded successfully ✅")
                
                os.remove(filename)
                bot.delete_message(user_id, prog_msg.message_id)
            
        except Exception as e:
            error_text = (
                "حدث خطأ في التحميل\n"
                "Download error occurred\n"
                "للمساهمة الرجاء ابلاغ المطور بالخطأ\n"
                "To contribute, please report the error to the developer"
            )
            bot.edit_message_text(error_text, user_id, prog_msg.message_id)
            bot.send_message(ADMIN_ID, f"🚨 Error Log:\nLink: {url}\nError: {str(e)[:200]}")
    
    # 3. إذا كان الرابط ليس تيك توك أو مجرد نص عادي
    else:
        invalid_text = (
            "الرجاء التحقق من الرابط\n"
            "Please check the link"
        )
        bot.reply_to(message, invalid_text)

bot.infinity_polling()
