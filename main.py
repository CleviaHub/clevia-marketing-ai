[22.57, 3/4/2026] Ari: import os
import json
import time
import requests
import base64

# --- CONFIGURATION ---
ACCESS_TOKEN = os.getenv('IG_ACCESS_TOKEN')
BUSINESS_ID = os.getenv('IG_BUSINESS_ID')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_REPO = "CleviaHub/clevia-marketing-ai"

REPO_BASE_URL = "https://raw.githubusercontent.com/CleviaHub/clevia-marketing-ai/main/"
PRODUCTS_FILE = "products.json"
POSTED_FILE = "posted_indices.json"
APPROVAL_TIMEOUT = 1800

def github_get(filename):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}", headers=he…
[23.02, 3/4/2026] Ari: Update main.py
[23.02, 3/4/2026] Ari: import os
import json
import time
import requests
import base64

# --- CONFIGURATION ---
ACCESS_TOKEN = os.getenv('IG_ACCESS_TOKEN')
BUSINESS_ID = os.getenv('IG_BUSINESS_ID')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_REPO = "CleviaHub/clevia-marketing-ai"

REPO_BASE_URL = "https://raw.githubusercontent.com/CleviaHub/clevia-marketing-ai/main/"
PRODUCTS_FILE = "products.json"
POSTED_FILE = "posted_indices.json"
APPROVAL_TIMEOUT = 1800

def github_get(filename):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}", headers=headers)
    if r.status_code == 200:
        data = r.json()
        content = base64.b64decode(data['content']).decode().strip()
        return content, data['sha']
    return None, None

def github_put(filename, content, sha, message):
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Content-Type": "application/json"}
    encoded = base64.b64encode(content.encode()).decode()
    body = {"message": message, "content": encoded}
    if sha:
        body["sha"] = sha
    requests.put(f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}", headers=headers, json=body)

def get_posted_indices():
    content, sha = github_get(POSTED_FILE)
    if content:
        return json.loads(content), sha
    return [], None

def save_posted_indices(indices, sha):
    github_put(POSTED_FILE, json.dumps(indices), sha, f"Update posted indices")

def get_next_product(products):
    posted, sha = get_posted_indices()
    total = len(products)

    if len(posted) >= total:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": "🛑 Semua konten sudah diposting! Tambah produk baru di products.json"},
            timeout=10
        )
        return None, None, None, None

    next_index = None
    for i in range(total):
        if i not in posted:
            next_index = i
            break

    remaining = total - len(posted) - 1

    if remaining <= 3:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": f"⚠️ WARNING: Sisa konten tinggal {remaining} lagi! Segera tambah produk baru di products.json"},
            timeout=10
        )

    return products[next_index], next_index, posted, sha

def generate_caption(product):
    print("🤖 Generating caption with Groq...")
    if product.get('type') == 'lifestyle':
        prompt_detail = f"Tema: {product['name']}. Buat caption estetik tentang rumah bersih tanpa sebut nama produk."
    else:
        prompt_detail = f"Produk: {product['name']} - {product['variant']}. Harga: {product.get('price', '')}. Keunggulan: {product.get('highlights', '')}"

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
    
    reply_markup = {"inline_keyboard": [[
        {"text": "✅ Approve & Post", "callback_data": "approve"},
        {"text": "✏️ Revisi", "callback_data": "revise"},
        {"text": "❌ Reject", "callback_data": "reject"}
    ]]}
    
    r = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto",
        data={"chat_id": TELEGRAM_CHAT_ID, "photo": image_url, "caption": text, "reply_markup": json.dumps(reply_markup)},
        timeout=30
    )
    return r.json().get("result", {}).get("message_id") if r.status_code == 200 else None

def ask_for_revised_caption(message_id):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        data={"chat_id": TELEGRAM_CHAT_ID, "text": "✏️ Kirim caption baru kamu sekarang:"},
        timeout=10
    )
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
                if "message" in update and "text" in update["message"]:
                    return update["message"]["text"]
        except:
            pass
        time.sleep(2)
    return None

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
                        return action
        except:
            pass
        time.sleep(2)
    return "timeout"

def post_to_ig(image_url, caption, max_retries=3, retry_delay=20):
    for attempt in range(1, max_retries + 1):
        print(f"📤 Step 1: Upload Container... (attempt {attempt}/{max_retries})")
        r = requests.post(
            f"https://graph.facebook.com/v21.0/{BUSINESS_ID}/media",
            data={'image_url': image_url, 'caption': caption, 'access_token': ACCESS_TOKEN},
            timeout=30
        )

        response_json = r.json()
        print(f"📋 Full response Step 1: {response_json}")

        # Cek error di step 1
        if r.status_code != 200 or 'error' in response_json:
            error = response_json.get('error', {})
            err_msg = error.get('message', 'Unknown Error')
            is_transient = error.get('is_transient', False)

            if is_transient and attempt < max_retries:
                print(f"⚠️ Transient error, retry dalam {retry_delay} detik... ({attempt}/{max_retries})")
                time.sleep(retry_delay)
                continue
            else:
                print(f"❌ Upload gagal: {err_msg}")
                requests.post(
                    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                    data={"chat_id": TELEGRAM_CHAT_ID, "text": f"❌ GAGAL UPLOAD (attempt {attempt}): {err_msg}"},
                    timeout=10
                )
                return False

        creation_id = response_json.get('id')
        if not creation_id:
            print(f"❌ Container ID None! Response: {response_json}")
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                data={"chat_id": TELEGRAM_CHAT_ID, "text": f"❌ CONTAINER GAGAL (ID None): {response_json}"},
                timeout=10
            )
            return False

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
            return True
        else:
            error_pub = response_pub.get('error', {})
            err_msg = error_pub.get('message', 'Publish Failed')
            is_transient = error_pub.get('is_transient', False)

            if is_transient and attempt < max_retries:
                print(f"⚠️ Transient error di publish, retry dalam {retry_delay} detik... ({attempt}/{max_retries})")
                time.sleep(retry_delay)
                continue
            else:
                print(f"❌ Publish gagal: {err_msg}")
                requests.post(
                    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                    data={"chat_id": TELEGRAM_CHAT_ID, "text": f"❌ GAGAL PUBLISH (attempt {attempt}): {err_msg}"},
                    timeout=10
                )
                return False

    return False

if __name__ == "__main__":
    with open(PRODUCTS_FILE, "r") as f:
        products = json.load(f)

    product, next_index, posted, sha = get_next_product(products)
    if not product:
        exit(0)

    print(f"📦 Produk: {product.get('name')} - {product.get('variant', '')}")

    raw_img = product['image']
    image_url = raw_img if raw_img.startswith("http") else REPO_BASE_URL + requests.utils.quote(raw_img)
    print(f"🖼️ Image URL: {image_url}")

    caption = generate_caption(product)
    if not caption:
        print("❌ Caption gagal.")
        exit(1)

    msg_id = send_telegram_preview(product, caption, image_url)
    if not msg_id:
        print("❌ Telegram preview gagal.")
        exit(1)

    action = wait_for_approval(msg_id)

    if action == "approve":
        success = post_to_ig(image_url, caption)
        if success:
            posted.append(next_index)
            save_posted_indices(posted, sha)
    elif action == "revise":
        new_caption = ask_for_revised_caption(msg_id)
        if new_caption:
            print(f"✏️ Caption baru: {new_caption}")
            success = post_to_ig(image_url, new_caption)
            if success:
                posted.append(next_index)
                save_posted_indices(posted, sha)
        else:
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                data={"chat_id": TELEGRAM_CHAT_ID, "text": "⏰ Timeout nunggu revisi caption."},
                timeout=10
            )
    else:
        print("❌ Ditolak atau timeout.")
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": "⏰ Post dibatalkan (timeout/reject). Konten ini akan dipost di jadwal berikutnya."},
            timeout=10
        )
