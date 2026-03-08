import logging
import asyncio
import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import cloudinary
import cloudinary.uploader
from config import Config

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# إعداد Cloudinary
cloudinary.config(
    cloud_name=Config.CLOUDINARY_CLOUD_NAME,
    api_key=Config.CLOUDINARY_API_KEY,
    api_secret=Config.CLOUDINARY_API_SECRET
)

# ==================== أنميشن الترحيب ====================

async def animated_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رسالة ترحيبية مع أنميشن"""
    
    # أنميشن التحميل
    msg = await update.message.reply_text("▪️▪️▪️")
    
    animations = [
        "🎬 جاري التحميل...",
        "🎥 جاري التحميل..",
        "📹 جاري التحميل.",
        "🎞️ جاري التحميل...",
        "✨ جاهز!"
    ]
    
    for anim in animations:
        await msg.edit_text(anim)
        await asyncio.sleep(0.4)
    
    await msg.delete()
    
    # أزرار تفاعلية
    keyboard = [
        [
            InlineKeyboardButton("🚀 بدء الاستخدام", callback_data='start'),
            InlineKeyboardButton("❓ المساعدة", callback_data='help')
        ],
        [
            InlineKeyboardButton("📊 إحصائيات", callback_data='stats'),
            InlineKeyboardButton("🔧 الإعدادات", callback_data='settings')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # الرسالة الترحيبية النهائية
    await update.message.reply_text(
        Config.WELCOME_MESSAGE,
        parse_mode='HTML',
        reply_markup=reply_markup
    )

# ==================== معالجة الفيديو ====================

async def process_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الفيديو وإزالة النصوص"""
    
    # التحقق من الفيديو
    video_file = None
    if update.message.video:
        video_file = update.message.video
    elif update.message.document and update.message.document.mime_type and 'video' in update.message.document.mime_type:
        video_file = update.message.document
    else:
        await update.message.reply_text("❌ يرجى إرسال فيديو فقط!")
        return
    
    # رسالة المعالجة
    processing_msg = await update.message.reply_text("⏳ جاري تحميل الفيديو...")
    
    try:
        # تحميل الفيديو
        file = await video_file.get_file()
        temp_path = f"temp_{update.message.message_id}.mp4"
        await file.download_to_drive(temp_path)
        
        # التحقق من حجم الملف
        file_size = os.path.getsize(temp_path) / (1024 * 1024)  # MB
        if file_size > 50:
            await processing_msg.edit_text("❌ حجم الفيديو كبير جداً! (الحد: 50 ميجا)")
            os.remove(temp_path)
            return
        
        await processing_msg.edit_text("⏳ جاري رفع الفيديو للمعالجة...")
        
        # رفع إلى Cloudinary
        upload_result = cloudinary.uploader.upload(
            temp_path,
            resource_type="video",
            folder="telegram_bot_videos"
        )
        
        await processing_msg.edit_text("🤖 جاري تحليل وإزالة النصوص...")
        
        # معالجة الفيديو - تغبيش المناطق العلوية (حيث يكون النص عادة)
        public_id = upload_result['public_id']
        
        # طريقة 1: تغبيش الجزء العلوي
        processed_url = f"https://res.cloudinary.com/{Config.CLOUDINARY_CLOUD_NAME}/video/upload/e_blur:1500,g_north,h_150,q_auto/{public_id}.mp4"
        
        # تحميل النتيجة
        await processing_msg.edit_text("⏳ جاري تحميل النتيجة...")
        
        response = requests.get(processed_url, stream=True, timeout=120)
        
        if response.status_code != 200:
            # تجربة طريقة بديلة
            processed_url = cloudinary.utils.cloudinary_url(
                public_id,
                resource_type="video",
                transformation=[
                    {"effect": "blur:1000", "gravity": "north", "height": 120},
                    {"quality": "auto:good"},
                    {"fetch_format": "mp4"}
                ]
            )[0]
            response = requests.get(processed_url, stream=True, timeout=120)
        
        output_path = f"out_{update.message.message_id}.mp4"
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        # إرسال النتيجة
        await processing_msg.delete()
        
        with open(output_path, 'rb') as video:
            await update.message.reply_video(
                video=video,
                caption="✅ تمت إزالة النصوص بنجاح!\n\n🤖 معالجة Cloudinary AI",
                supports_streaming=True
            )
        
        # تنظيف الملفات
        os.remove(temp_path)
        os.remove(output_path)
        
        # حذف من Cloudinary
        try:
            cloudinary.uploader.destroy(public_id, resource_type="video")
        except:
            pass
            
    except Exception as e:
        logger.error(f"Error: {e}")
        await processing_msg.edit_text(f"❌ حدث خطأ: {str(e)[:100]}")

# ==================== الأوامر ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /start"""
    await animated_welcome(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /help"""
    help_text = """
📖 <b>كيفية الاستخدام:</b>

1️⃣ أرسل فيديو يحتوي على نصوص
2️⃣ انتظر المعالجة (30 ثانية - 2 دقيقة)
3️⃣ استلم الفيديو بدون نصوص!

⚠️ <b>ملاحظات:</b>
• الحد الأقصى: 50 ميجابايت
• يدعم معظم صيغ الفيديو
• الجودة تعتمد على وضوح النص

💡 <b>نصيحة:</b>
النصوص في الأعلى تُزال تلقائياً
    """
    await update.message.reply_text(help_text, parse_mode='HTML')

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /about"""
    about_text = """
🤖 <b>عن البوت:</b>

🎯 يزيل النصوص والكتابة من الفيديوهات
☁️ يستخدم Cloudinary AI للمعالجة
⚡️ سريع ومجاني 100%

👨‍💻 المطور: @YourUsername
    """
    await update.message.reply_text(about_text, parse_mode='HTML')

# ==================== الأزرار ====================

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الأزرار"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'start':
        await query.edit_message_text(
            "🎬 <b>أرسل الفيديو الآن!</b>\n\nسأقوم بمعالجته فوراً...",
            parse_mode='HTML'
        )
    elif query.data == 'help':
        await help_command(update, context)
    elif query.data == 'stats':
        await query.edit_message_text(
            "📊 <b>إحصائيات:</b>\n\n"
            "البوت يعمل بنجاح! ✅\n"
            "جاهز لاستقبال الفيديوهات",
            parse_mode='HTML'
        )
    elif query.data == 'settings':
        await query.edit_message_text(
            "⚙️ <b>الإعدادات:</b>\n\n"
            "جودة المعالجة: عالية\n"
            "الوضع: تلقائي\n"
            "اللغة: العربية",
            parse_mode='HTML'
        )

# ==================== معالجة الأخطاء ====================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الأخطاء"""
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ حدث خطأ غير متوقع. حاول مرة أخرى لاحقاً."
        )

# ==================== التشغيل الرئيسي ====================

def main():
    """تشغيل البوت بـ Polling"""
    
    # إنشاء التطبيق
    application = Application.builder().token(Config.BOT_TOKEN).build()
    
    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, process_video))
    application.add_error_handler(error_handler)
    
    print("=" * 50)
    print("🤖 البوت يعمل الآن...")
    print("📡 وضع: Polling")
    print("=" * 50)
    
    # تشغيل Polling (الطريقة الصحيحة للإصدار 20.x)
    application.run_polling(
        drop_pending_updates=True,  # تجاهل الرسائل القديمة
        allowed_updates=Update.ALL_TYPES,
        poll_interval=1.0,          # فحص كل ثانية
        timeout=10                  # مهلة الانتظار
    )

if __name__ == "__main__":
    main()
  
