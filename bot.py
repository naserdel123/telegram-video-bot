import logging
import asyncio
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import cloudinary
import cloudinary.uploader
import requests
from config import Config

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

cloudinary.config(
    cloud_name=Config.CLOUDINARY_CLOUD_NAME,
    cloud_key=Config.CLOUDINARY_API_KEY,
    api_secret=Config.CLOUDINARY_API_SECRET
)

async def animated_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    frames = ["🎬", "🎥", "📹", "🎞️", "✨"]
    msg = await update.message.reply_text("جاري التحميل...")
    
    for frame in frames:
        await msg.edit_text(f"{frame} <b>جاري تشغيل البوت...</b>", parse_mode='HTML')
        await asyncio.sleep(0.3)
    
    await msg.delete()
    
    keyboard = [
        [InlineKeyboardButton("🚀 بدء الاستخدام", callback_data='start')],
        [InlineKeyboardButton("❓ المساعدة", callback_data='help')]
    ]
    
    await update.message.reply_text(
        Config.WELCOME_MESSAGE,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def process_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.video:
        await update.message.reply_text("❌ أرسل فيديو فقط!")
        return
    
    processing = await update.message.reply_text("⏳ جاري تحميل الفيديو...")
    
    try:
        # تحميل الفيديو
        video = await update.message.video.get_file()
        temp_path = f"video_{update.message.message_id}.mp4"
        await video.download_to_drive(temp_path)
        
        await processing.edit_text("⏳ جاري رفع الفيديو للمعالجة...")
        
        # رفع لـ Cloudinary
        upload = cloudinary.uploader.upload(
            temp_path,
            resource_type="video",
            folder="telegram_bot"
        )
        
        await processing.edit_text("🤖 جاري إزالة النصوص بالذكاء الاصطناعي...")
        
        # معالجة: تغبيش + إزالة تلقائية
        processed_url = cloudinary.utils.cloudinary_url(
            upload['public_id'],
            resource_type="video",
            transformation=[
                {"effect": "blur:800", "gravity": "north", "height": 150},
                {"effect": "improve"},
                {"quality": "auto"},
                {"fetch_format": "mp4"}
            ]
        )[0]
        
        # تحميل النتيجة
        await processing.edit_text("⏳ جاري تحميل النتيجة...")
        
        response = requests.get(processed_url, stream=True)
        output_path = f"out_{update.message.message_id}.mp4"
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # إرسال
        await processing.delete()
        with open(output_path, 'rb') as f:
            await update.message.reply_video(
                f,
                caption="✅ تمت المعالجة!\n\n🎬 الفيديو معالج بـ Cloudinary AI"
            )
        
        # تنظيف
        os.remove(temp_path)
        os.remove(output_path)
        cloudinary.uploader.destroy(upload['public_id'], resource_type="video")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        await processing.edit_text(f"❌ خطأ: {str(e)[:100]}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await animated_welcome(update, context)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'start':
        await query.edit_message_text("🎬 <b>أرسل الفيديو الآن!</b>", parse_mode='HTML')
    elif query.data == 'help':
        await query.edit_message_text(
            "📖 <b>طريقة الاستخدام:</b>\n\n"
            "1️⃣ أرسل فيديو يحتوي على نصوص\n"
            "2️⃣ انتظر المعالجة (1-2 دقيقة)\n"
            "3️⃣ استلم الفيديو منظف!\n\n"
            "⚠️ الحد الأقصى: 20 ميجابايت",
            parse_mode='HTML'
        )

def main():
    app = Application.builder().token(Config.BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.VIDEO, process_video))
    
    print("🤖 البوت يعمل...")
    app.run_polling()

if __name__ == "__main__":
    main()
      
