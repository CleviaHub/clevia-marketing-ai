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
APPROVAL_TIMEOUT = 1800

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
    
    r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=body, timeout=30)
    return r.json()['choices'][0]['message']['content'].strip() if r.status_code == 200 else None

def send_telegram_preview(product, caption, image_url):
    print("📨 Kirim preview ke Telegram...")
    display_name = product.get('name', 'Clevia Post')
    text = f"🔔 CLEVIA PREVIEW\n\n📦 {display_name}\n📝 Caption:\n{caption}\n\n👇 Approve?"
    
    reply_markup = {"inline_keyboard": [[{"text": "✅ Approve & Post", "callback_data": "approve"}, {"text": "❌ Reject", "callback_data": "reject"}]]}
    
    r = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto",
        data={"chat_id": TELEGRAM_CHAT_ID, "photo": image_url, "caption": text, "reply_markup": json.dumps(reply_markup)},
        timeout=30
    )
    return r.json().get("result", {}).get("message_id") if r.status_code == 200 else None

def wait_for_approval(message_id):
    print("⏳ Menunggu klik di Telegram...")
    start_time = time.time()
    offset = None
    while time.time() - start_time < APPROVAL_TIMEOUT:
        try:
            r = requests.get(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates",
                params={"timeout": 10, "offset": offset},
                timeout=20
            )
            updates = r.json().get("result", [])
            for update in updates:
                offset = update["update_id"] + 1
                if "callback_query" in update:
                    cb = update["callback_query"]
                    if cb.get("message", {}).get("message_id") == message_id:
                        action = cb.get("data")
                        requests.post(
                            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery",
                            data={"callback_query_id": cb["id"]},
                            timeout=10
                        )
                        requests.post(
                            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/editMessageReplyMarkup",
                            data={"chat_id": TELEGRAM_CHAT_ID, "message_id": message_id, "reply_markup": json.dumps({"inline_keyboard": []})},
                            timeout=10
                        )
                        return action == "approve"
        except:
            pass
        time.sleep(2)
    return False

def post_to_ig(image_url, caption):
    print("📤 Step 1: Upload Container...")
    r = requests.post(
        f"https://graph.facebook.com/v21.0/{BUSINESS_ID}/media",
        data={'image_url': image_url, 'caption': caption, 'access_token': ACCESS_TOKEN},
        timeout=30
    )
    
    response_json = r.json()
    print(f"📋 Full response Step 1: {response_json}")

    if r.status_code != 200:
        err = response_json.get('error', {}).get('message', 'Unknown Error')
        print(f"❌ Upload gagal: {err}")
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": f"❌ GAGAL UPLOAD: {err}"},
            timeout=10
        )
        return

    creation_id = response_json.get('id')
    
    if not creation_id:
        print(f"❌ Container ID None! Response: {response_json}")
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": f"❌ CONTAINER GAGAL (ID None): {response_json}"},
            timeout=10
        )
        return

    print(f"✅ Container ID: {creation_id}. Jeda 5 detik...")
    time.sleep(5)

    print("🚀 Step 2: Publishing...")
    r_pub = requests.post(
        f"https://graph.facebook.com/v21.0/{BUSINESS_ID}/media_publish",
        data={'creation_id': creation_id, 'access_token': ACCESS_TOKEN},
        timeout=30
    )
    
    response_pub = r_pub.json()
    print(f"📋 Full response Step 2: {response_pub}")

    if r_pub.status_code == 200:
        print("✅ Post berhasil!")
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": "✅ SUCCESS! Konten Clevia sudah LIVE di Instagram!"},
            timeout=10
        )
    else:
        err = response_pub.get('error', {}).get('message', 'Publish Failed')
        print(f"❌ Publish gagal: {err}")
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": f"❌ GAGAL PUBLISH: {err}"},
            timeout=10
        )

if __name__ == "__main__":
    with open(PRODUCTS_FILE, "r") as f:
        products = json.load(f)

    product = get_next_product(products)
    print(f"📦 Produk: {product.get('name')} - {product.get('variant', '')}")

    raw_img = product['image']
    image_url = clean_gdrive_link(raw_img) if raw_img.startswith("http") else REPO_BASE_URL + requests.utils.quote(raw_img)

    print(f"🖼️ Image URL: {image_url}")

    caption = generate_caption(product)
    if not caption:
        print("❌ Caption gagal.")
        exit(1)

    msg_id = send_telegram_preview(product, caption, image_url)
    if not msg_id:
        print("❌ Telegram preview gagal.")
        exit(1)

    if wait_for_approval(msg_id):
        post_to_ig(image_url, caption)
    else:
        print("❌ Ditolak atau timeout.")
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": "⏰ Post dibatalkan (timeout/reject)."},
            timeout=10
        )
