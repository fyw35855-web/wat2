import requests
import logging

# إعداد الـ Logging بدل الـ print العادي حتى تتبع الأخطاء بشكل احترافي
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WAHA_BASE_URL = "http://localhost:3000"

def clean_phone_number(phone: str) -> str:
    """دالة لتنظيف رقم الهاتف من الزوائد (مثل علامة + أو المسافات)"""
    return ''.join(filter(str.isdigit, str(phone)))

def send_whatsapp_text(to_phone: str, message: str) -> dict | None:
    url = f"{WAHA_BASE_URL}/api/sendText"
    
    # تنظيف الرقم لضمان عدم وجود أخطاء في الـ chat_id
    clean_number = clean_phone_number(to_phone)
    chat_id = f"{clean_number}@c.us" 
    
    payload = {
        "chatId": chat_id,
        "text": message,
        "session": "default"
    }
    
    try:
        # إضافة timeout (10 ثوانٍ) حتى ما يعلق النظام إذا كان سيرفر WAHA طافي
        response = requests.post(url, json=payload, timeout=10)
        
        # التأكد من أن حالة الرد ناجحة (بدون أخطاء 404 أو 500)
        response.raise_for_status() 
        
        return response.json()
        
    except requests.exceptions.Timeout:
        logger.error(f"⏳ انتهى وقت الاتصال (Timeout) عند الإرسال للرقم {clean_number}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ خطأ في الاتصال بسيرفر الواتساب WAHA: {e}")
        return None
    except Exception as e:
        logger.error(f"⚠️ خطأ غير متوقع: {e}")
        return None
