import os
import json
import time
import requests

# --- CONFIGURATION ---
ACCESS_TOKEN = os.getenv('IG_ACCESS_TOKEN')
BUSINESS_ID = os.getenv('IG_BUSINESS_ID')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

REPO_BASE_URL = "https://raw.githubusercontent.com/CleviaHub/clevia-marketing-ai/main/"
PRODUCTS_FILE = "products.json"
COUNTER_FILE = "post_counter.txt"
APPROVAL_TIMEOUT = 1800 # 30 Menit

def get_next_product(products):
    try:
        with open(COUNTER_FILE, "r") as f:
            index = int(f.read().strip())
    except:
        index = 0
    product = products[index % len(products)]
    with open(COUNTER_FILE, "w") as f:
        f.write(str((index + 1) % len(products)))
    return product

def clean_gdrive_link(url):
    """Mengubah link GDrive biasa jadi Direct Link yang bisa dibaca Instagram"""
    if "drive.google.com" in url:
        file_id = ""
        if "/file/d/" in url:
            file_id = url.split("/file/d/")[1].split("/")[0]
        elif "id=" in url:
            file_id = url.split("id=")[1].split("&")[0]
        if file_id:
            return f"https://drive.google.com/uc?export=download&id={file_id}"
    return url

def generate_caption(product):
    print("🤖 Generating caption with Groq...")
    # Cek apakah ini post lifestyle atau produk
    if product.get('type') == 'lifestyle':
        prompt_detail = f"Tema: {product['name']}. Buat caption estetik tentang rumah bersih tanpa sebut nama produk."
    else:
        prompt_detail = f"Produk: {product['name']} - {product['variant']}. Harga: {product['price']}. Keunggulan: {product['highlights']}"

    prompt = f"""Kamu adalah copywriter Instagram Clevia. Tone: Profesional & Ramah.
{prompt_detail}
Aturan: Hook menarik, maks 150 kata, 2-3 emoji, CTA: Order via DM!, Hashtag: #Clevia #CleviaEveryday.
Tulis hanya caption saja."""

    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    body = {"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt}], "temperature": 0.8}
    
    r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=body)
    return r.json()['choices'][0]['message']['content'].strip() if r.status_code == 200 else None

def send_telegram_preview(product, caption, image_url):
    print("📨 Kirim preview ke Telegram...")
    display_name = product.get('name', 'Clevia Post')
    text = f"🔔 CLEVIA PREVIEW\n\n📦 {display_name}\n📝 Caption:\n{caption}\n\n👇 Approve?"
    
    reply_markup = {"inline_keyboard": [[{"text": "✅ Approve & Post", "callback_data": "approve"},{"text": "❌ Reject", "callback_data": "reject"}]]}
    
    # Kirim foto langsung dari URL (GitHub/GDrive)
    r = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto",
        data={"chat_id": TELEGRAM_CHAT_ID, "photo": image_url, "caption": text, "reply_markup": json.dumps(reply_markup)}
    )
    return r.json().get("result", {}).get("message_id") if r.status_code == 200 else None

def wait_for_approval(message_id):
    print("⏳ Menunggu klik di Telegram...")
    start_time = time.time()
    offset = None
    while time.time() - start_time < APPROVAL_TIMEOUT:
        try:
            r = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates", params={"timeout": 10, "offset": offset})
            updates = r.json().get("result", [])
            for update in updates:
                offset = update["update_id"] + 1
                if "callback_query" in update:
                    cb = update["callback_query"]
                    if cb.get("message", {}).get("message_id") == message_id:
                        action = cb.get("data")
                        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery", data={"callback_query_id": cb["id"]})
                        # Hapus tombol
                        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/editMessageReplyMarkup", 
                                      data={"chat_id": TELEGRAM_CHAT_ID, "message_id": message_id, "reply_markup": json.dumps({"inline_keyboard": []})})
                        return action == "approve"
        except: pass
        time.sleep(2)
    return False

def post_to_ig(image_url, caption):
    print("📤 Step 1: Upload Container...")
    # Gunakan API v21.0
    r = requests.post(f"https://graph.facebook.com/v21.0/{BUSINESS_ID}/media", 
                      data={'image_url': image_url, 'caption': caption, 'access_token': ACCESS_TOKEN})
    
    if r.status_code != 200:
        err = r.json().get('error', {}).get('message', 'Unknown Error')
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", data={"chat_id": TELEGRAM_CHAT_ID, "text": f"❌ GAGAL UPLOAD: {err}"})
        return

    creation_id = r.json().get('id')
    print(f"✅ Container ID: {creation_id}. Jeda 5 detik...")
    time.sleep(5)

    print("🚀 Step 2: Publishing...")
    r_pub = requests.post(f"https://graph.facebook.com/v21.0/{BUSINESS_ID}/media_publish", 
                          data={'creation_id': creation_id, 'access_token': ACCESS_TOKEN})
    
    if r_pub.status_code == 200:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", data={"chat_id": TELEGRAM_CHAT_ID, "text": "✅ SUCCESS! Konten Clevia sudah LIVE di Instagram!"})
    else:
        err = r_pub.json().get('error', {}).get('message', 'Publish Failed')
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", data={"chat_id": TELEGRAM_CHAT_ID, "text": f"❌ GAGAL PUBLISH: {err}"})

if __name__ == "__main__":
    with open(PRODUCTS_FILE, "r") as f:
        products = json.load(f)

    product = get_next_product(products)
    
    # Deteksi Sumber Gambar
    raw_img = product['image']
    image_url = clean_gdrive_link(raw_img) if raw_img.startswith("http") else REPO_BASE_URL + raw_img

    caption = generate_caption(product)
    msg_id = send_telegram_preview(product, caption, image_url)
    
    if msg_id and wait_for_approval(msg_id):
        post_to_ig(image_url, caption)
