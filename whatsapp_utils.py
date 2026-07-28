import requests

WAHA_BASE_URL = "http://localhost:3000"

def send_whatsapp_text(to_phone: str, message: str):
    url = f"{WAHA_BASE_URL}/api/sendText"
    chat_id = f"{to_phone}@c.us" 
    payload = {
        "chatId": chat_id,
        "text": message,
        "session": "default"
    }
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        print("Error:", e)
        return None
