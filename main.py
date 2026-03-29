import os
import json
import time
import requests

ACCESS_TOKEN = os.getenv('IG_ACCESS_TOKEN')
BUSINESS_ID = os.getenv('IG_BUSINESS_ID')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

REPO_BASE_URL = "https://raw.githubusercontent.com/CleviaHub/clevia-marketing-ai/main/"
PRODUCTS_FILE = "products.json"
COUNTER_FILE = "post_counter.txt"

WAIT_MINUTES = 30

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
        "model": "llama3-8b-8192",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.8,
        "max_tokens": 300
    }
    r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=body)
    if r.status_code != 200:
        print(f"❌ Groq error: {r.json()}")
        return None
    caption = r.json()['choices'][0]['message']['content'].strip()
    print(f"✅ Caption generated:\n{caption}\n")
    return caption

def send_discord_preview(product, caption, image_url):
    print("📨 Sending preview to Discord...")
    message = {
        "content": f"""🔔 *CLEVIA AUTO POST – PREVIEW*

📦 Produk: {product['name']} – {product['variant']} ({product['size']})
💰 Harga: {product['price']}
🖼️ Image: {image_url}

📝 *Caption:*
{caption}

⏳ Post akan otomatis tayang dalam *{WAIT_MINUTES} menit*.
❌ Batalkan workflow di GitHub Actions jika tidak ingin dipost."""
    }
    r = requests.post(DISCORD_WEBHOOK_URL, json=message)
    if r.status_code in [200, 204]:
        print("✅ Preview terkirim ke Discord!")
    else:
        print(f"❌ Discord error: {r.status_code}")

def post_to_ig(image_url, caption):
    print("📤 Uploading media to Instagram...")
    r = requests.post(
        f"https://graph.facebook.com/v19.0/{BUSINESS_ID}/media",
        data={'image_url': image_url, 'caption': caption, 'access_token': ACCESS_TOKEN}
    )
    print(f"Upload Status: {r.status_code} | Response: {r.json()}")
    if r.status_code != 200:
        print("❌ Upload gagal.")
        return
    creation_id = r.json().get('id')
    print("🚀 Publishing post...")
    r_pub = requests.post(
        f"https://graph.facebook.com/v19.0/{BUSINESS_ID}/media_publish",
        data={'creation_id': creation_id, 'access_token': ACCESS_TOKEN}
    )
    print(f"Publish Status: {r_pub.status_code} | Response: {r_pub.json()}")
    if r_pub.status_code == 200:
        print("✅ Post Clevia berhasil tayang di Instagram!")
    else:
        print("❌ Publish gagal.")

if __name__ == "_main_":
    with open(PRODUCTS_FILE, "r") as f:
        products = json.load(f)

    product = get_next_product(products)
    print(f"📦 Produk: {product['name']} – {product['variant']}")

    image_filename = requests.utils.quote(product['image'])
    image_url = REPO_BASE_URL + image_filename

    caption = generate_caption(product)
    if not caption:
        print("❌ Caption gagal, post dibatalkan.")
        exit(1)

    send_discord_preview(product, caption, image_url)

    print(f"⏳ Menunggu {WAIT_MINUTES} menit sebelum posting...")
    time.sleep(WAIT_MINUTES * 60)

    post_to_ig(image_url, caption)
