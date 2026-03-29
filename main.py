import os
import json
import time
import requests

ACCESS_TOKEN = os.getenv('IG_ACCESS_TOKEN')
BUSINESS_ID = os.getenv('IG_BUSINESS_ID')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

REPO_BASE_URL = "https://raw.githubusercontent.com/CleviaHub/clevia-marketing-ai/main/"
PRODUCTS_FILE = "products.json"
COUNTER_FILE = "post_counter.txt"
APPROVAL_TIMEOUT = 1800 # Robot nunggu persetujuan maksimal 30 Menit (dalam detik)

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

def generate_caption(product):
    print("🤖 Generating caption with Groq...")
    prompt = f"""Kamu adalah copywriter Instagram untuk brand produk kebersihan rumah tangga premium bernama Clevia. 
Tagline brand: "Bersihnya Super, Harumnya Nempel!"
Tone: Profesional namun ramah, bersih, segar, dan penuh semangat.

Buat caption Instagram yang menarik dan persuasif dalam Bahasa Indonesia untuk produk berikut:

Nama Produk: {product['name']} – {product['variant']} ({product['size']})
Harga: {product['price']}
Keunggulan: {product['highlights']}

Aturan caption:
- Mulai dengan kalimat hook yang menarik perhatian
- Maksimal 150 kata
- Gunakan 2-3 emoji yang relevan
- Sertakan CTA: "Order via DM atau link di bio!"
- Akhiri dengan 5 hashtag relevan (#Clevia dan #CleviaEveryday wajib ada)
- Jangan gunakan tanda bintang (*) atau format markdown

Tulis hanya captionnya saja, tanpa penjelasan tambahan."""

    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    body = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.8,
        "max_tokens": 300
    }
    r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=body)
    if r.status_code != 200:
        print(f"❌ Groq error: {r.json()}")
        return None
    caption = r.json()['choices'][0]['message']['content'].strip()
    return caption

def send_telegram_preview_with_buttons(product, caption, image_url):
    print("📨 Mengirim preview dan tombol ke Telegram...")
    text = f"🔔 CLEVIA AUTO POST – PREVIEW\n\n📦 Produk: {product['name']} - {product['variant']}\n💰 Harga: {product['price']}\n📝 Caption:\n{caption}\n\n👇 Silakan pilih aksi (Waktu 30 menit):"
    
    # Bikin tombol Approve & Reject
    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "✅ Approve & Post", "callback_data": "approve"},
                {"text": "❌ Reject", "callback_data": "reject"}
            ]
        ]
    }
    
    img_request = requests.get(image_url)
    if img_request.status_code == 200:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto",
            data={"chat_id": TELEGRAM_CHAT_ID, "caption": text, "reply_markup": json.dumps(reply_markup)},
            files={"photo": img_request.content}
        )
    else:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": text + f"\n\n⚠️ INFO: Gambar tidak ditemukan di {image_url}", "reply_markup": json.dumps(reply_markup)}
        )
        
    if r.status_code == 200:
        print("✅ Preview dan Tombol berhasil terkirim!")
        return r.json().get("result", {}).get("message_id")
    else:
        print(f"❌ Telegram error: {r.status_code} | {r.json()}")
        exit(1)

def wait_for_approval(message_id):
    print("⏳ Menunggu lo ngeklik tombol di Telegram...")
    start_time = time.time()
    offset = None
    
    while time.time() - start_time < APPROVAL_TIMEOUT:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
        params = {"timeout": 10, "allowed_updates": ["callback_query"]}
        if offset:
            params["offset"] = offset
            
        try:
            r = requests.get(url, params=params)
            updates = r.json().get("result", [])
            
            for update in updates:
                offset = update["update_id"] + 1
                if "callback_query" in update:
                    cb = update["callback_query"]
                    # Cek apakah tombol yang diklik dari pesan yang benar
                    if cb.get("message", {}).get("message_id") == message_id:
                        action = cb.get("data")
                        
                        # Kasih respon ke Telegram biar loading di tombolnya berhenti
                        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery", 
                                      data={"callback_query_id": cb["id"], "text": f"Diproses: {action}"})
                        
                        # Hapus tombol setelah diklik biar ga bisa diklik 2 kali
                        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/editMessageReplyMarkup",
                                      data={"chat_id": TELEGRAM_CHAT_ID, "message_id": message_id, "reply_markup": json.dumps({"inline_keyboard": []})})
                        
                        if action == "approve":
                            print("✅ APPROVED by user!")
                            requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                                          data={"chat_id": TELEGRAM_CHAT_ID, "text": "✅ Approval diterima! Mengeksekusi postingan ke Instagram..."})
                            return True
                        elif action == "reject":
                            print("❌ REJECTED by user!")
                            requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                                          data={"chat_id": TELEGRAM_CHAT_ID, "text": "❌ Postingan dibatalkan oleh lo."})
                            return False
        except Exception as e:
            pass # Lanjut ngecek lagi
            
        time.sleep(2) # Cek tiap 2 detik
        
    print("⏳ Waktu habis! Lo ga klik tombolnya selama 30 menit.")
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/editMessageReplyMarkup",
                  data={"chat_id": TELEGRAM_CHAT_ID, "message_id": message_id, "reply_markup": json.dumps({"inline_keyboard": []})})
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                  data={"chat_id": TELEGRAM_CHAT_ID, "text": "⏳ Waktu approval habis. Post otomatis dibatalkan."})
    return False

def post_to_ig(image_url, caption):
    print("📤 Uploading media to Instagram...")
    r = requests.post(
        f"https://graph.facebook.com/v19.0/{BUSINESS_ID}/media",
        data={'image_url': image_url, 'caption': caption, 'access_token': ACCESS_TOKEN}
    )
    if r.status_code != 200:
        print(f"❌ Upload IG gagal. Response: {r.json()}")
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                      data={"chat_id": TELEGRAM_CHAT_ID, "text": f"❌ GAGAL UPLOAD IG: Cek token Instagram lo!"})
        exit(1) 

    creation_id = r.json().get('id')
    print("🚀 Publishing post...")
    r_pub = requests.post(
        f"https://graph.facebook.com/v19.0/{BUSINESS_ID}/media_publish",
        data={'creation_id': creation_id, 'access_token': ACCESS_TOKEN}
    )
    if r_pub.status_code == 200:
        print("✅ Post Clevia berhasil tayang di Instagram!")
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                      data={"chat_id": TELEGRAM_CHAT_ID, "text": "✅ SUCCESS: Konten Clevia udah tayang di Instagram!"})
    else:
        print(f"❌ Publish IG gagal. Response: {r_pub.json()}")
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                      data={"chat_id": TELEGRAM_CHAT_ID, "text": f"❌ GAGAL PUBLISH IG."})
        exit(1)

if __name__ == "__main__":
    with open(PRODUCTS_FILE, "r") as f:
        products = json.load(f)

    product = get_next_product(products)
    print(f"📦 Produk: {product['name']} – {product['variant']}")

    image_url = REPO_BASE_URL + product['image']

    caption = generate_caption(product)
    if not caption:
        print("❌ Caption gagal, post dibatalkan.")
        exit(1)

    # 1. Kirim pesan ke Telegram plus tombol Approve/Reject
    message_id = send_telegram_preview_with_buttons(product, caption, image_url)
    
    if message_id:
        # 2. Tungguin lo ngeklik tombol (Maksimal 30 menit)
        is_approved = wait_for_approval(message_id)
        
        # 3. Kalau lo klik Approve, baru posting ke IG
        if is_approved:
            post_to_ig(image_url, caption)
        else:
            print("❌ Proses dihentikan.")
            exit(0)
    else:
        exit(1)
