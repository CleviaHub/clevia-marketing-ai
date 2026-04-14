# =============================================================================
# brain.py — AI Agents
# Agent 1: Groq / Llama 3.3 70B      → The Researcher
# Agent 2: OpenRouter / GLM-5.1      → The Creative Director
# Universe: "The Quiet Strength" — Novel Blog Clevia 2026
# =============================================================================

import os
import json
import random
import requests
from datetime import datetime

# ── Env vars ──────────────────────────────────────────────────────────────────
GROQ_API_KEY       = os.environ["GROQ_API_KEY"]
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]

GROQ_BASE_URL       = "https://api.groq.com/openai/v1/chat/completions"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

# Model config + fallback chain
GROQ_MODEL          = "llama-3.3-70b-versatile"
GROQ_FALLBACK_MODEL = "mixtral-8x7b-32768"     # Groq fallback, masih gratis
GLM_MODEL           = "z-ai/glm-5.1"
FALLBACK_MODEL      = "deepseek/deepseek-chat"  # OpenRouter fallback, gratis


# =============================================================================
# "THE QUIET STRENGTH" — NOVEL UNIVERSE
# 12 arc · 48 post · 1 tahun bersama Ayu
# =============================================================================

NOVEL_UNIVERSE = {
    "character": {
        "name": "Ayu",
        "role": "Ibu rumah tangga Indonesia, usia 30-an",
        "world": (
            "Ayu tidak pernah benar-benar punya waktu untuk berhenti. "
            "Setiap hari dimulai sebelum matahari terbit dan berakhir saat semua orang sudah terlelap. "
            "Tidak ada yang istimewa dari hidupnya — dan mungkin memang tidak pernah dimaksudkan untuk terlihat istimewa. "
            "Tapi dari hal-hal yang nyaris tidak terlihat itu, sebuah rumah tetap berdiri."
        ),
        "arc": "Dari bertahan diam → menemukan suara sendiri → menerima kekuatan yang tidak terlihat",
    },
    "writing_principles": [
        "Ayu bukan customer. Ia adalah karakter. Clevia bukan hero — ia hanya ada, seperti benda-benda yang kita andalkan tanpa sadar.",
        "Produk TIDAK PERNAH disebut duluan. Setting dulu, produk menyusul secara organik. JANGAN pernah memulai dengan 'Dengan Clevia...'",
        "54% post berisi produk, 46% murni cerita. Ratio ini menjaga kepercayaan pembaca — ini bukan katalog.",
        "Setiap post bisa berdiri sendiri, tapi jika dibaca berurutan ada perjalanan. Novel dan blog sekaligus.",
        "Tidak ada semangat palsu. Tidak ada toxic positivity. Kejujuran emosional adalah kekuatan utama.",
        "Kalimat pendek. Ada jeda. Ada ruang untuk pembaca bernapas. Seperti prosa puisi.",
    ],
    "chapters": [
        {
            "month": 1, "label": "Jan", "arc": "Pembukaan",
            "theme": "Awal yang Tidak Pernah Dirayakan",
            "posts": [
                {"week": 1, "title": "Resolusi yang Tidak Pernah Ditulis", "teaser": "Semua orang punya resolusi tahun baru. Ayu tidak. Ia hanya bangun, seperti biasa, dan memulai.", "product": None, "angle": "Brand opening — memperkenalkan Ayu dan dunianya tanpa memaksa."},
                {"week": 2, "title": "Pagi Hari Miliknya Sendiri", "teaser": "Sebelum semua orang bangun, ada lima belas menit yang hanya milik Ayu. Dan dapur yang masih tenang.", "product": "Sabun Cuci Piring Premium", "angle": "Produk hadir sebagai bagian dari ritual pagi — bukan iklan, tapi detail setting."},
                {"week": 3, "title": "Bersih Bukan Berarti Rapi", "teaser": "Rumah Ayu tidak selalu rapi. Tapi ada hal-hal yang selalu ia jaga tetap bersih — dengan caranya sendiri.", "product": "Pembersih Meja Premium", "angle": "Reframing kebersihan — bukan perfeksionisme, tapi ketenangan."},
                {"week": 4, "title": "Januari yang Diam", "teaser": "Bulan pertama berlalu seperti bulan-bulan lainnya. Tidak ada yang berubah. Dan mungkin itu tidak apa-apa.", "product": None, "angle": "Chapter closing — reflektif, tenang, tidak memaksakan semangat palsu."},
            ],
        },
        {
            "month": 2, "label": "Feb", "arc": "Koneksi",
            "theme": "Tentang Mereka yang Ada di Sini",
            "posts": [
                {"week": 1, "title": "Cinta yang Tidak Berbentuk Bunga", "teaser": "Hari Valentine datang dan pergi. Ayu membersihkan meja makan yang sama seperti hari-hari biasa.", "product": None, "angle": "Anti-Valentine's Day — merayakan bentuk cinta yang tak terlihat."},
                {"week": 2, "title": "Baju yang Selalu Terlipat", "teaser": "Tidak ada yang pernah berterima kasih untuk baju yang terlipat. Tapi Ayu terus melipatnya.", "product": "Fabric Scent Signature Premium", "angle": "Labor of love — produk hadir dalam gestur kasih sayang yang sunyi."},
                {"week": 3, "title": "Anak-Anak yang Tumbuh Tanpa Disadari", "teaser": "Kapan terakhir ia benar-benar memperhatikan betapa besarnya mereka sudah?", "product": "Pel Lantai Clevia", "angle": "Parenting angle — kelembutan dan keamanan sebagai bahasa cinta."},
                {"week": 4, "title": "Hal yang Tidak Pernah Dikatakan", "teaser": "Ada banyak hal yang ingin Ayu katakan. Tapi ia pilih untuk melakukannya saja — diam-diam.", "product": None, "angle": "Emotional depth — menutup bulan dengan intimasi karakter."},
            ],
        },
        {
            "month": 3, "label": "Mar", "arc": "Pertanyaan",
            "theme": "Jarak yang Pelan-Pelan Terbentuk",
            "posts": [
                {"week": 1, "title": "Lelah yang Tidak Ada Namanya", "teaser": "Bukan sakit. Bukan marah. Hanya ada sesuatu yang terasa berat tanpa alasan yang jelas.", "product": None, "angle": "Emotional honesty — burnout ibu rumah tangga diangkat dengan hormat."},
                {"week": 2, "title": "Rumah yang Terlalu Berisik", "teaser": "Kadang Ayu berdiri di tengah keributan dan merasa sangat jauh dari semuanya.", "product": "Karbol Premium", "angle": "Produk sebagai momen grounding — wangi yang membawa pulang."},
                {"week": 3, "title": "Sebelum Pertanyaan Itu Muncul", "teaser": "Apakah ini yang ia inginkan? Pertanyaan itu datang pelan, tanpa permisi.", "product": None, "angle": "Character crisis point — titik tengah arc. Jujur dan tidak diselesaikan paksa."},
                {"week": 4, "title": "Musim Hujan di Dalam Rumah", "teaser": "Luar sedang basah dan dingin. Dalam juga, tapi dengan cara yang berbeda.", "product": "Karbol Premium", "angle": "Seasonal relevance — merawat rumah sebagai metafora merawat diri."},
            ],
        },
        {
            "month": 4, "label": "Apr", "arc": "Ruang",
            "theme": "Menemukan Sesuatu yang Hanya Miliknya",
            "posts": [
                {"week": 1, "title": "Sudut Dapur yang Menjadi Miliknya", "teaser": "Di antara semua ruang yang ia urus, ada satu sudut kecil yang terasa seperti miliknya sendiri.", "product": None, "angle": "Ownership — perempuan dan ruang pribadi dalam rumah sendiri."},
                {"week": 2, "title": "Bersih-Bersih yang Tidak Terburu-Buru", "teaser": "Hari ini tidak ada tamu. Tidak ada deadline. Ayu membersihkan dengan caranya sendiri.", "product": "Pel Lantai Clevia", "angle": "Slow living — ritual kebersihan sebagai meditasi."},
                {"week": 3, "title": "Hal-Hal yang Ia Pelajari Sendirian", "teaser": "Tidak ada yang mengajarinya cara menjaga rumah. Ia tahu karena ia terus mencoba.", "product": "Pembersih Meja Premium", "angle": "Self-taught pride — merayakan pengetahuan dari pengalaman."},
                {"week": 4, "title": "Pertama Kali Ia Membeli Sesuatu untuk Dirinya", "teaser": "Bukan untuk anak-anak. Bukan untuk rumah. Untuk Ayu.", "product": "Sabun Cuci Tangan Premium", "angle": "Self-care pivot — natural bridge ke produk body care Clevia."},
            ],
        },
        {
            "month": 5, "label": "Mei", "arc": "Tubuh",
            "theme": "Yang Sering Dilupakan",
            "posts": [
                {"week": 1, "title": "Tangan yang Tidak Pernah Berhenti", "teaser": "Ayu menatap tangannya dan baru menyadari — kapan terakhir ia merawatnya?", "product": "Sabun Cuci Tangan Premium", "angle": "Body awareness — tangan sebagai simbol kerja tanpa henti."},
                {"week": 2, "title": "Mandi yang Bukan Sekadar Mandi", "teaser": "Lima menit saja. Itu semua yang ia minta. Tapi kali ini, lima menit itu ia jaga.", "product": "Sabun Cuci Tangan Premium", "angle": "Ritual as resistance — self-care bukan kemewahan, tapi keputusan."},
                {"week": 3, "title": "Wangi yang Membawa Pulang", "teaser": "Ada wangi tertentu yang langsung membuat segalanya terasa lebih ringan.", "product": "Karbol Premium", "angle": "Sensory storytelling — scent memory dan emotional grounding."},
                {"week": 4, "title": "Bulan Ibu yang Setiap Hari", "teaser": "Satu hari dalam setahun tidak cukup. Tapi Ayu tidak menunggu perayaan untuk merasa berarti.", "product": None, "angle": "Mother's Day subversion — menolak satu hari, merayakan setiap hari."},
            ],
        },
        {
            "month": 6, "label": "Jun", "arc": "Jeda",
            "theme": "Saat Semua Orang Libur, Ayu Tetap Ada",
            "posts": [
                {"week": 1, "title": "Liburan Sekolah yang Tidak Benar-Benar Libur", "teaser": "Anak-anak di rumah berarti lebih banyak yang perlu dijaga. Tapi Ayu tetap tersenyum.", "product": "Pembersih Meja Premium", "angle": "Seasonal reality — high-traffic home life, low-drama solutions."},
                {"week": 2, "title": "Meja Makan yang Ramai", "teaser": "Semua orang ada di rumah. Dan Ayu menyadari — ini yang sebenarnya ia rindukan.", "product": "Sabun Cuci Piring Premium", "angle": "Gratitude in chaos — menemukan makna di tengah keributan."},
                {"week": 3, "title": "Tidur Siang yang Tidak Pernah Terjadi", "teaser": "Ia berencana untuk istirahat. Rencana itu tidak pernah terlaksana. Tapi entah kenapa, tidak apa-apa.", "product": None, "angle": "Honest humor — ringan, relatable, tidak menggurui."},
                {"week": 4, "title": "Pertengahan Tahun", "teaser": "Enam bulan sudah berlalu. Ayu tidak menghitungnya. Ia hanya terus berjalan.", "product": None, "angle": "Mid-year reflection — gentle, non-performative introspection."},
            ],
        },
        {
            "month": 7, "label": "Jul", "arc": "Komunitas",
            "theme": "Perempuan yang Saling Menguatkan",
            "posts": [
                {"week": 1, "title": "Tetangga yang Tidak Pernah Jauh", "teaser": "Mereka tidak selalu bicara. Tapi ada semacam pengertian di antara mereka yang tidak perlu kata-kata.", "product": None, "angle": "Community building — koneksi perempuan di lingkungan sekitar."},
                {"week": 2, "title": "Resep yang Diturunkan Tanpa Dituliskan", "teaser": "Bukan resep masakan. Resep untuk bertahan. Yang diwariskan lewat cara mereka hidup.", "product": "Deterjen Cair Premium", "angle": "Generational wisdom — nilai produk alami sebagai warisan."},
                {"week": 3, "title": "Grup WhatsApp yang Tidak Pernah Sunyi", "teaser": "Ayu tidak selalu membalas. Tapi ia selalu membaca. Dan itu sudah cukup.", "product": None, "angle": "Modern community — digital connection yang autentik."},
                {"week": 4, "title": "Mereka yang Merawat Tanpa Diketahui", "teaser": "Ada begitu banyak perempuan seperti Ayu. Dan mungkin itulah yang membuat dunia tetap berjalan.", "product": None, "angle": "Solidarity — brand statement tentang perempuan Indonesia."},
            ],
        },
        {
            "month": 8, "label": "Agu", "arc": "Akar",
            "theme": "Dari Mana Kekuatan Itu Berasal",
            "posts": [
                {"week": 1, "title": "Kemerdekaan yang Tidak Selalu Terlihat", "teaser": "Merdeka bisa berarti banyak hal. Untuk Ayu, itu adalah kemampuan untuk memilih — meski pilihannya kecil.", "product": None, "angle": "Independence Day tie-in — freedom redefined untuk perempuan Indonesia."},
                {"week": 2, "title": "Bahan-Bahan yang Ia Percaya", "teaser": "Ayu tidak mudah percaya. Tapi ada hal-hal yang sudah ia buktikan sendiri.", "product": "Pel Lantai Clevia", "angle": "Product trust — ingredient transparency sebagai nilai brand."},
                {"week": 3, "title": "Tanah dan Rumah", "teaser": "Rumah bukan sekadar tempat tinggal. Ia tumbuh dari sana — dan ia tahu itu.", "product": None, "angle": "Roots & identity — Indonesian home as sacred space."},
                {"week": 4, "title": "Yang Tersisa Setelah Semua Ini", "teaser": "Jika suatu hari semua ini selesai, apa yang akan diingat orang tentang Ayu?", "product": None, "angle": "Legacy — slow, meditative. Character at their deepest."},
            ],
        },
        {
            "month": 9, "label": "Sep", "arc": "Perubahan",
            "theme": "Sesuatu yang Pelan-Pelan Bergeser",
            "posts": [
                {"week": 1, "title": "Musim yang Berganti Tanpa Permisi", "teaser": "Tidak ada yang mengumumkan perubahan. Tapi tiba-tiba, semuanya terasa sedikit berbeda.", "product": None, "angle": "Seasonal shift — metaphor for internal change."},
                {"week": 2, "title": "Hal-Hal yang Ia Berhenti Lakukan", "teaser": "Bukan karena malas. Tapi karena ia akhirnya memilih mana yang benar-benar penting.", "product": "Deterjen Cair Premium", "angle": "Simplification — less but better, sejalan dengan eco value."},
                {"week": 3, "title": "Rutinitas yang Sedikit Berubah", "teaser": "Ia bangun sedikit lebih lambat. Dan merasa tidak ada yang runtuh karenanya.", "product": None, "angle": "Permission to slow down — anti-hustle, pro-intention."},
                {"week": 4, "title": "Percakapan yang Akhirnya Terjadi", "teaser": "Ia tidak tahu dari mana kata-kata itu datang. Tapi akhirnya, ia mengatakannya juga.", "product": None, "angle": "Turning point — karakter mulai bersuara, bukan hanya bertahan."},
            ],
        },
        {
            "month": 10, "label": "Okt", "arc": "Penemuan",
            "theme": "Apa yang Selama Ini Tidak Pernah Ia Cari",
            "posts": [
                {"week": 1, "title": "Kesenangan yang Tidak Perlu Dijelaskan", "teaser": "Ia tidak tahu kapan ini mulai terasa menyenangkan. Tapi sekarang, ia tidak ingin berhenti.", "product": "Fabric Scent Signature Premium", "angle": "Joy in the mundane — sensory delight dalam rutinitas."},
                {"week": 2, "title": "Ternyata Ia Tahu Banyak Hal", "teaser": "Tidak ada gelar. Tidak ada sertifikat. Tapi Ayu tahu bagaimana membuat segalanya berjalan.", "product": None, "angle": "Expertise without credentials — merayakan pengetahuan praktis."},
                {"week": 3, "title": "Untuk Pertama Kalinya Ia Tidak Merasa Sendirian", "teaser": "Entah dari mana datangnya — tapi tiba-tiba ada rasa bahwa ia tidak berjalan sendiri.", "product": None, "angle": "Brand as silent companion — Clevia hadir tanpa disebut."},
                {"week": 4, "title": "Hal yang Ia Temukan di Bawah Sink Dapur", "teaser": "Ia membersihkan sudut yang sudah lama tidak ia sentuh. Dan menemukan lebih dari yang ia kira.", "product": "Sabun Cuci Piring Premium", "angle": "Product discovery moment — organic dan tidak dipaksakan."},
            ],
        },
        {
            "month": 11, "label": "Nov", "arc": "Makna",
            "theme": "Kekuatan yang Tidak Selalu Terlihat",
            "posts": [
                {"week": 1, "title": "Yang Tidak Pernah Dikatakannya", "teaser": "Ada kalimat yang sudah lama ingin ia ucapkan. Hari ini, ia akhirnya menuliskannya.", "product": None, "angle": "Voice — karakter menemukan ekspresinya."},
                {"week": 2, "title": "Bukan Pahlawan. Tapi Bukan Juga Bukan.", "teaser": "Ayu tidak ingin disebut pahlawan. Tapi ia tidak mau lagi dipandang tidak ada.", "product": None, "angle": "Identity — quiet assertion of worth."},
                {"week": 3, "title": "Syukur yang Tidak Performatif", "teaser": "Ia tidak memposting tentang bersyukur. Ia hanya merasakannya — dan itu sudah cukup.", "product": "Fabric Scent Signature Premium", "angle": "Gratitude season tie-in — authentic, non-viral."},
                {"week": 4, "title": "Kekuatan yang Diam", "teaser": "Tidak ada tepuk tangan. Tidak ada sorotan lampu. Tapi kekuatan itu ada di sana — dan Ayu tahu itu.", "product": None, "angle": "Echo of opening prose — the thesis made manifest."},
            ],
        },
        {
            "month": 12, "label": "Des", "arc": "Penutupan",
            "theme": "Tetap Bertahan — Dan Itu Sudah Lebih dari Cukup",
            "posts": [
                {"week": 1, "title": "Akhir Tahun yang Tidak Dramatis", "teaser": "Tidak ada momen besar. Tidak ada keajaiban. Tapi Ayu sampai di sini — dan itu bukan hal kecil.", "product": None, "angle": "Anti-climax as climax — keindahan dalam normalitas."},
                {"week": 2, "title": "Rumah yang Masih Berdiri", "teaser": "Setahun berlalu. Rumah itu masih ada. Keluarga itu masih ada. Dan Ayu masih ada.", "product": "Semua produk Clevia", "angle": "Brand full circle — semua produk sebagai silent witnesses."},
                {"week": 3, "title": "Surat yang Tidak Pernah Dikirim", "teaser": "Kepada dirinya sendiri, setahun yang lalu. Ia tidak tahu apa yang akan ditulisnya — sampai ia mulai.", "product": None, "angle": "Year-end letter — deeply personal, shareable."},
                {"week": 4, "title": "Besok Masih Akan Datang", "teaser": "Dan Ayu akan tetap ada di sana. Bukan karena ada yang menyuruhnya. Tapi karena itu memang dirinya.", "product": None, "angle": "Series finale — open ending, tidak menutup terlalu rapi."},
            ],
        },
    ],
}


# =============================================================================
# PRODUCT KNOWLEDGE BASE
# =============================================================================

PRODUCT_KB = [
    {"id": "table_cleaner",    "name": "Pembersih Meja Premium (Fresh Herbal Guard)", "core_action": "Membantu mengurangi ketertarikan serangga (lalat, semut, kecoa, nyamuk)",      "post_wash_vibe": "Fresh Herbal",                          "tip": "Aplikasikan di sudut laci/lemari gelap, lalu buka pintu/laci agar diangin-angin — mencegah jamur pada kayu"},
    {"id": "dish_soap",        "name": "Sabun Cuci Piring Premium",                   "core_action": "Angkat lemak kuat & cepat, busa melimpah (irit), bilas cepat tanpa residu",   "post_wash_vibe": "Fresh lime / clean premium",            "tip": "Bilas sekali sudah bersih total — tidak perlu berkali-kali"},
    {"id": "floor_cleaner",    "name": "Pel Lantai Clevia",                            "core_action": "Cepat kering tanpa licin, kesat maksimal, aman untuk anak",                    "post_wash_vibe": "Clean premium",                         "tip": "Low foam profesional — tidak perlu bilas ulang"},
    {"id": "carbolic",         "name": "Karbol Premium",                               "core_action": "Anti-bau, higienis, tekstur creamy merata, anti-licin",                        "post_wash_vibe": "Addictive premium — wangi nagih tahan lama", "tip": "Cepat kering, tidak meninggalkan bekas"},
    {"id": "liquid_detergent", "name": "Deterjen Cair Premium",                        "core_action": "Angkat noda kuat, busa creamy halus, bilas cepat",                             "post_wash_vibe": "Signature scent nempel kuat di kain",   "tip": "Kain tetap lembut, tidak kaku setelah dicuci"},
    {"id": "hand_soap",        "name": "Sabun Cuci Tangan Premium",                    "core_action": "Bersih maksimal tapi lembut untuk pemakaian intensif",                         "post_wash_vibe": "Clean nagih",                           "tip": "Busa halus, cocok dipakai berkali-kali tanpa kulit kering"},
    {"id": "fabric_scent",     "name": "Fabric Scent Signature Premium",               "core_action": "Parfum laundry — wangi langsung naik saat kain kering",                        "post_wash_vibe": "Premium clean tahan lama",              "tip": "Wangi signature Clevia yang paling khas — scent blooms saat dijemur"},
]


# =============================================================================
# HELPERS
# =============================================================================

def get_current_chapter_context() -> dict:
    """
    Deteksi bulan & minggu saat ini.
    Return chapter + post yang relevan dari universe The Quiet Strength.
    """
    now           = datetime.now()
    month_idx     = now.month - 1
    week_of_month = min((now.day - 1) // 7, 3)

    chapter = NOVEL_UNIVERSE["chapters"][month_idx]
    post    = chapter["posts"][week_of_month]

    print(f"[BRAIN] 📅 Konteks: {chapter['label']} — Arc '{chapter['arc']}' — Week {week_of_month + 1}")
    return {
        "month_label":  chapter["label"],
        "arc":          chapter["arc"],
        "arc_theme":    chapter["theme"],
        "post_title":   post["title"],
        "post_teaser":  post["teaser"],
        "post_angle":   post["angle"],
        "post_product": post["product"],
        "week":         week_of_month + 1,
    }


def select_product(chapter_ctx: dict) -> dict:
    """
    Pilih produk berdasarkan chapter context.
    Jika chapter context rekomendasikan produk → match ke PRODUCT_KB.
    Jika tidak ada → random.
    """
    suggested = chapter_ctx.get("post_product")
    if suggested:
        for p in PRODUCT_KB:
            if any(kw in suggested.lower() for kw in p["name"].lower().split()):
                print(f"[BRAIN] Produk dari chapter context: {p['name']}")
                return p
    product = random.choice(PRODUCT_KB)
    print(f"[BRAIN] Produk random: {product['name']}")
    return product


def _parse_json(raw: str, agent_name: str) -> dict:
    """Safely parse JSON, strip markdown fences."""
    clean = raw.strip().replace("json", "").replace("", "").strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError as e:
        raise ValueError(f"[{agent_name}] JSON parse gagal: {e}\nOutput:\n{raw[:600]}")


# =============================================================================
# API CALLERS
# =============================================================================

def _call_groq(messages: list, temperature: float = 0.7, use_fallback: bool = False) -> str:
    """Groq API. Fallback: Llama 3.3 → Mixtral → DeepSeek (OpenRouter)."""
    model   = GROQ_FALLBACK_MODEL if use_fallback else GROQ_MODEL
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": 2000}

    resp = requests.post(GROQ_BASE_URL, headers=headers, json=payload, timeout=60)

    if resp.status_code == 429:
        if not use_fallback:
            print(f"[BRAIN] ⚠️  {model} rate limit → Mixtral (Groq)")
            return _call_groq(messages, temperature=temperature, use_fallback=True)
        print("[BRAIN] ⚠️  Mixtral rate limit → DeepSeek (OpenRouter)")
        return _call_openrouter(messages, model=FALLBACK_MODEL, temperature=temperature)

    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _call_openrouter(messages: list, model: str = GLM_MODEL, temperature: float = 0.85) -> str:
    """OpenRouter API. Fallback: GLM-5.1 → DeepSeek."""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type":  "application/json",
        "HTTP-Referer":  "https://liveclevia.com",
        "X-Title":       "Clevia AI Content Factory",
    }
    payload = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": 4000}

    resp = requests.post(OPENROUTER_BASE_URL, headers=headers, json=payload, timeout=90)

    if resp.status_code == 429:
        print(f"[BRAIN] ⚠️  {model} rate limit → DeepSeek")
        if model != FALLBACK_MODEL:
            return _call_openrouter(messages, model=FALLBACK_MODEL, temperature=temperature)

    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


# =============================================================================
# AGENT 1 — THE RESEARCHER (Groq / Llama 3.3 70B)
# =============================================================================

def agent1_researcher(raw_rss_text: str) -> dict:
    """
    Input:  raw text dari RSS feeds (legs.fetch_rss_trends)
    Output: dict { trend, sentiment, pain_points, keywords, source, content_angle }
    """
    print("[BRAIN] 🔍 Agent 1 (Researcher / Groq) mulai bekerja...")

    system_prompt = (
        "Kamu adalah analis tren pasar produk rumah tangga Indonesia. "
        "Analisis berita yang diberikan, ekstrak insight relevan untuk "
        "brand produk kebersihan rumah tangga premium. "
        "Output HARUS berupa JSON valid. Tidak ada teks lain di luar JSON."
    )

    user_prompt = f"""
Analisis artikel berikut:
{raw_rss_text}

Kembalikan JSON dengan format PERSIS:
{{
  "trend": "deskripsi tren utama yang relevan (max 2 kalimat)",
  "sentiment": "Positive / Negative / Neutral",
  "pain_points": ["keluhan 1", "keluhan 2", "keluhan 3"],
  "keywords": ["kata kunci 1", "kata kunci 2", "kata kunci 3"],
  "source": "Local / Trend / Mixed",
  "content_angle": "sudut cerita paling menarik untuk konten Clevia (1 kalimat)"
}}
"""

    raw = _call_groq([
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_prompt},
    ], temperature=0.3)

    try:
        result = _parse_json(raw, "Agent 1")
        print(f"[BRAIN] ✅ Agent 1 selesai. Tren: {result.get('trend', '')[:70]}...")
        return result
    except ValueError:
        print("[BRAIN] ⚠️  Fallback ke default trend data")
        return {
            "trend": "Konsumen Indonesia makin sadar akan produk kebersihan yang aman dan ramah lingkungan",
            "sentiment": "Positive",
            "pain_points": ["lantai masih licin setelah dipel", "produk berbau menyengat", "residu sabun cuci piring"],
            "keywords": ["bersih", "aman", "keluarga", "higienis", "alami"],
            "source": "Fallback",
            "content_angle": "Kebersihan rumah sebagai bentuk cinta kepada keluarga",
        }


# =============================================================================
# AGENT 2 — THE CREATIVE DIRECTOR (OpenRouter / GLM-5.1)
# =============================================================================

def agent2_creative_director(trend_data: dict, product: dict, chapter_ctx: dict) -> dict:
    """
    Input:
      - trend_data   : output Agent 1
      - product      : dari PRODUCT_KB
      - chapter_ctx  : dari get_current_chapter_context()

    Output: dict siap publish {
        article_title, article_html,
        caption_ig, caption_fb,
        hero_image_prompt,
        tiktok_image_prompts: [slide1, slide2, slide3]
    }
    """
    print("[BRAIN] 🎨 Agent 2 (Creative Director / GLM-5.1) mulai bekerja...")

    char       = NOVEL_UNIVERSE["character"]
    principles = "\n".join(f"- {p}" for p in NOVEL_UNIVERSE["writing_principles"])

    system_prompt = f"""
Kamu adalah penulis dan Creative Director untuk brand Clevia Indonesia.
Kamu sedang menulis satu babak dari novel blog berseri berjudul "The Quiet Strength".

══════════════════════════════════════════
KARAKTER UTAMA
══════════════════════════════════════════
Nama  : {char['name']}
Latar : {char['role']}
Dunia : {char['world']}
Arc   : {char['arc']}

══════════════════════════════════════════
PRINSIP PENULISAN — WAJIB DIIKUTI
══════════════════════════════════════════
{principles}

══════════════════════════════════════════
VISUAL BRAND
══════════════════════════════════════════
- Estetika: Bali Resort — serene, natural light, tropical, warm tones
- DILARANG: botol produk, kemasan, teks merek, objek komersial di visual
- Gaya foto: photorealistic lifestyle, NO product shots
- Sapaan wajib di semua teks: "Kakak"

Output HARUS berupa JSON valid. Tidak ada teks di luar JSON.
""".strip()

    user_prompt = f"""
══════════════════════════════════════════
KONTEKS BULAN INI
══════════════════════════════════════════
Bulan  : {chapter_ctx['month_label']} — Arc: {chapter_ctx['arc']}
Tema   : "{chapter_ctx['arc_theme']}"
Minggu : {chapter_ctx['week']}
  Judul referensi : "{chapter_ctx['post_title']}"
  Teaser          : "{chapter_ctx['post_teaser']}"
  Angle           : {chapter_ctx['post_angle']}

══════════════════════════════════════════
DATA TREN HARI INI (dari Researcher)
══════════════════════════════════════════
{json.dumps(trend_data, ensure_ascii=False, indent=2)}

══════════════════════════════════════════
PRODUK YANG DISISIPKAN (SECARA ORGANIK)
══════════════════════════════════════════
Nama    : {product['name']}
Manfaat : {product['core_action']}
Vibe    : {product['post_wash_vibe']}
Tip     : {product['tip']}

INGAT:
- Produk hadir sebagai detail latar dalam cerita Ayu, BUKAN sebagai hero
- JANGAN memulai kalimat dengan nama produk
- Produk muncul paling cepat di paragraf ketiga artikel

══════════════════════════════════════════
OUTPUT — FORMAT JSON PERSIS INI
(Bahasa Indonesia semua, kecuali image prompts WAJIB Bahasa Inggris)
══════════════════════════════════════════
{{
  "article_title": "Judul sastra ringan, max 70 karakter. Bukan clickbait. Bukan judul iklan.",
  "article_html": "Min 400 kata. Prosa puitis, kalimat pendek, ada jeda. Cerita Ayu dalam rutinitas hariannya. Produk muncul natural sebagai bagian setting, bukan solusi yang diiklankan. Format HTML dengan <p> <h2> <em> <strong>.",
  "caption_ig": "Max 2200 karakter. Mulai 'Kakak,'. Reflektif, hangat, tidak menggurui. Akhiri dengan 5 hashtag (#Clevia dan #TheQuietStrength wajib ada).",
  "caption_fb": "Lebih panjang dari IG, full storytelling. Mulai 'Kakak,'. Akhiri 3 hashtag.",
  "hero_image_prompt": "Bahasa Inggris. Photorealistic. Indonesian woman in quiet morning ritual at home, Bali resort aesthetic, soft natural light, tropical plants, linen textures, warm tones. NO bottles, NO labels, NO text, NO packaging. Evoke: serenity, quiet strength.",
  "tiktok_image_prompts": [
    "Slide 1 (Bahasa Inggris): Before / pain point. Relatable tired home interior, slightly messy, overcast soft light, Indonesian home, no product visible, moody but not dark.",
    "Slide 2 (Bahasa Inggris): Vibe / lifestyle. Serene Bali resort home interior, airy morning light, tropical plants, clean linen, Indonesian woman at peace, no product visible.",
    "Slide 3 (Bahasa Inggris): After / result. Pristine clean Indonesian home, sparkling surfaces, warm golden light, fresh flowers, family warmth, no product packaging visible."
  ]
}}
"""

    raw = _call_openrouter([
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_prompt},
    ], model=GLM_MODEL, temperature=0.85)

    result = _parse_json(raw, "Agent 2")
    print(f"[BRAIN] ✅ Agent 2 selesai. Judul: {result.get('article_title', '')}")
    return result
