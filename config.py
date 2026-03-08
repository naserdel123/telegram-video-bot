import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")
    
    # رسائل البوت
    WELCOME_MESSAGE = """
🎬 <b>مرحباً بك في بوت إزالة النصوص من الفيديو!</b>

✨ <i>أرسل لي أي فيديو يحتوي على نصوص أو كتابة</i>
🤖 <i>وسأقوم بمعالجته وإزالة النصوص تلقائياً باستخدام الذكاء الاصطناعي</i>

📌 <b>الأوامر المتاحة:</b>
/start - بدء البوت
/help - المساعدة
/about - عن البوت

⚡️ <b>جاهز لاستقبال الفيديوهات...</b>
    """
    
    PROCESSING_MESSAGE = "⏳ جاري معالجة الفيديو... قد يستغرق هذا بضع دقائق"
    SUCCESS_MESSAGE = "✅ تمت المعالجة بنجاح!"
    ERROR_MESSAGE = "❌ حدث خطأ أثناء المعالجة. حاول مرة أخرى."
