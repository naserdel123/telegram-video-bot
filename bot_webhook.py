import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import cloudinary
import cloudinary.uploader
import requests
import asyncio
from config import Config

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

cloudinary.config(
    cloud_name=Config.CLOUDINARY_CLOUD_NAME,
    api_key=Config.CLOUDINARY_API_KEY,
    api_secret=Config.CLOUDINARY_API_SECRET
)

# ==================== المعالجات ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رسالة ترحيبية"""
    keyboard = [
        [InlineKeyboardButton("🚀 أرسل فيديو", callback_data='send_video')],
        [InlineKeyboardButton("❓ المساعدة", callback_data='help')]
    ]
    
    await update.message.reply_text(
        "🎬 <b>مرحباً بك في بوت إزالة النصوص!</b>\n\n"
        "أرسل لي أي فيديو وسأقوم بإزالة النصوص منه تلقائياً",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'send_video':
        await query.edit_message_text("🎬 <b>أرسل الفيديو الآن!</b>", parse_mode='HTML')
    elif query.data == 'help':
        await query.edit_message_text(
            "📖 <b>الطريقة:</b>\n1️⃣ أرسل فيديو\n2️⃣ انتظر المعالجة\n3️⃣ استلم النتيجة!",
            parse_mode='HTML'
        )

async def process_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الفيديو"""
    processing = await update.message.reply_text("⏳ جاري المعالجة...")
    
    try:
        # تحميل الفيديو
        video = await update.message.video.get_file()
        temp_path = f"video_{update.message.message_id}.mp4"
        await video.download_to_drive(temp_path)
        
        await processing.edit_text("⏳ جاري الرفع...")
        
        # رفع لـ Cloudinary
        upload = cloudinary.uploader.upload(
            temp_path,
            resource_type="video",
            folder="telegram_bot"
        )
        
        await processing.edit_text("🤖 جاري إزالة النصوص...")
        
        # معالجة Cloudinary
        processed_url = cloudinary.utils.cloudinary_url(
            upload['public_id'],
            resource_type="video",
            transformation=[
                {"effect": "blur:1000", "gravity": "north", "height": 200},
                {"quality": "auto"},
                {"fetch_format": "mp4"}
            ]
        )[0]
        
        # تحميل النتيجة
        await processing.edit_text("⏳ جاري التحميل...")
        
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
                caption="✅ تمت المعالجة بنجاح!"
            )
        
        # تنظيف
        os.remove(temp_path)
        os.remove(output_path)
        cloudinary.uploader.destroy(upload['public_id'], resource_type="video")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        await processing.edit_text(f"❌ خطأ: {str(e)[:200]}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {context.error}")

# ==================== التشغيل ====================

def main():
    """تشغيل البوت بـ Polling"""
    application = Application.builder().token(Config.BOT_TOKEN).build()
    
    # المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.VIDEO, process_video))
    application.add_error_handler(error_handler)
    
    print("🤖 البوت يعمل...")
    
    # تشغيل Polling (الطريقة الصحيحة للإصدار 20.x)
    application.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,
        poll_interval=1.0,
        timeout=10
    )

if __name__ == "__main__":
    main()
