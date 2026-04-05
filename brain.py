import os
import json
import time
import requests
import base64
from datetime import datetime

# --- CONFIGURATION ---
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_REPO = "CleviaHub/clevia-marketing-ai"

KNOWLEDGE_BASE_FILE = "knowledge_base.json"

# ============================================================
# GITHUB UTILS
# ============================================================

def github_get(filename):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(
        f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}",
        headers=headers
    )
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
    requests.put(
        f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}",
        headers=headers,
        json=body
    )

def load_knowledge_base():
    content, sha = github_get(KNOWLEDGE_BASE_FILE)
    if content:
        return json.loads(content), sha
    return {"insights": [], "competitor_data": [], "reports": []}, None

def save_knowledge_base(kb, sha):
    github_put(
        KNOWLEDGE_BASE_FILE,
        json.dumps(kb, indent=2, ensure_ascii=False),
        sha,
        f"Update knowledge base - {datetime.now().strftime('%Y-%m-%d')}"
    )

# ============================================================
# TELEGRAM UTILS
# ============================================================

def send_telegram(text, parse_mode="Markdown"):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": parse_mode
        },
        timeout=30
    )

# ============================================================
# AGENT 1: GROQ RESEARCHER
# ============================================================

def groq_researcher(brand="Clevia", category="homecare"):
    print("🔍 Agent 1: Groq Researcher starting...")

    prompt = f"""Kamu adalah analis pasar senior untuk brand {brand} di kategori {category} Indonesia.

Lakukan analisis mendalam tentang:

1. *TREN PASAR* (minggu ini)
   - Tren produk homecare yang sedang naik di Indonesia
   - Keyword yang banyak dicari konsumen
   - Format konten yang paling viral di IG/TikTok

2. *ANALISIS KOMPETITOR*
   - Strategi konten kompetitor homecare (So Klin, Sunlight, Wipol, dll)
   - Harga pasaran produk sejenis
   - Keunggulan dan kelemahan kompetitor

3. *PELUANG KONTEN*
   - 5 ide konten yang relevan untuk {brand} minggu ini
   - Angle storytelling yang bisa dipakai
   - Pain point konsumen yang bisa diangkat

4. *REKOMENDASI STRATEGI*
   - 3 aksi prioritas untuk {brand} minggu ini
   - Produk yang sebaiknya dipromosikan
   - Timing posting yang optimal

Format response sebagai JSON dengan struktur:
{{
  "tanggal": "YYYY-MM-DD",
  "brand": "{brand}",
  "tren_pasar": ["tren1", "tren2", "tren3"],
  "keyword_populer": ["keyword1", "keyword2", "keyword3"],
  "kompetitor_insights": ["insight1", "insight2", "insight3"],
  "peluang_konten": ["ide1", "ide2", "ide3", "ide4", "ide5"],
  "rekomendasi_aksi": ["aksi1", "aksi2", "aksi3"],
  "produk_prioritas": "nama produk",
  "timing_optimal": "jam posting terbaik",
  "summary": "ringkasan eksekutif dalam 2 kalimat"
}}

Berikan analisis yang SPESIFIK dan ACTIONABLE untuk brand homecare premium Indonesia."""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 2000
    }

    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=body,
        timeout=60
    )

    if r.status_code != 200:
        print(f"❌ Groq error: {r.text}")
        return None

    content = r.json()['choices'][0]['message']['content'].strip()

    # Parse JSON
    try:
        # Cari JSON dalam response
        start = content.find('{')
        end = content.rfind('}') + 1
        if start != -1 and end != 0:
            json_str = content[start:end]
            return json.loads(json_str)
    except:
        pass

    return {"raw_analysis": content, "tanggal": datetime.now().strftime('%Y-%m-%d'), "brand": brand}

# ============================================================
# AGENT 2: GEMINI CREATIVE DIRECTOR
# ============================================================

def gemini_creative(research_data, brand="Clevia"):
    print("🎨 Agent 2: Gemini Creative Director starting...")

    prompt = f"""Kamu adalah Creative Director untuk brand {brand} — produk homecare premium Indonesia.

Berdasarkan riset ini:
{json.dumps(research_data, ensure_ascii=False, indent=2)}

Buat rencana konten untuk minggu ini:

1. *DRAFT KONTEN IG* (3 caption siap posting)
   - Setiap caption: hook kuat, maks 150 kata, 2-3 emoji, CTA order via DM
   - Hashtag: #Clevia #CleviaEveryday + 3 hashtag relevan
   - Sebutkan produk mana yang dipromo

2. *IMAGE PROMPTS* (untuk setiap caption)
   - Prompt dalam bahasa Inggris untuk generate gambar AI
   - Style: clean, lifestyle, Bali resort aesthetic
   - DILARANG tampilkan botol/kemasan produk — fokus pada hasil bersih/feeling

3. *ARTIKEL BLOGGER* (outline)
   - Judul artikel storytelling (bukan sales)
   - 5 poin cerita dalam gaya novel ringan kehidupan ibu rumah tangga
   - Sisipkan solusi {brand} secara natural

Format response sebagai JSON:
{{
  "konten_ig": [
    {{
      "produk": "nama produk",
      "caption": "teks caption lengkap",
      "image_prompt": "prompt bahasa Inggris untuk AI image"
    }}
  ],
  "artikel_blogger": {{
    "judul": "judul artikel",
    "outline": ["poin1", "poin2", "poin3", "poin4", "poin5"]
  }}
}}"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.8, "maxOutputTokens": 3000}
    }

    r = requests.post(url, json=body, timeout=60)

    if r.status_code != 200:
        print(f"❌ Gemini error: {r.text}")
        return None

    content = r.json()['candidates'][0]['content']['parts'][0]['text']

    try:
        start = content.find('{')
        end = content.rfind('}') + 1
        if start != -1 and end != 0:
            return json.loads(content[start:end])
    except:
        pass

    return {"raw_creative": content}

# ============================================================
# AGENT 3: CLAUDE STRATEGIST
# ============================================================

def claude_strategist(research_data, creative_data, brand="Clevia"):
    print("🧠 Agent 3: Claude Strategist starting...")

    prompt = f"""Kamu adalah Chief Strategy Officer untuk {brand} dan Magic Space (brand incubator Indonesia).

Data riset minggu ini:
{json.dumps(research_data, ensure_ascii=False, indent=2)}

Rencana kreatif minggu ini:
{json.dumps(creative_data, ensure_ascii=False, indent=2)}

Berikan analisis strategis:

1. *KEPUTUSAN PRIORITAS* — apa yang HARUS dilakukan minggu ini
2. *PERINGATAN RISIKO* — ada ancaman atau peluang yang terlewat?
3. *FORECAST 4 MINGGU* — prediksi pertumbuhan berdasarkan tren
4. *REKOMENDASI PRICING* — apakah harga produk masih kompetitif?
5. *R&D INSIGHT* — produk baru apa yang perlu dikembangkan?

Format response sebagai JSON:
{{
  "keputusan_prioritas": ["aksi1", "aksi2", "aksi3"],
  "peringatan_risiko": ["risiko1", "risiko2"],
  "forecast_4_minggu": "prediksi narasi",
  "rekomendasi_pricing": "analisis harga",
  "rd_insight": "ide produk baru",
  "skor_kesehatan_brand": 85,
  "executive_summary": "ringkasan untuk founder dalam 3 kalimat"
}}"""

    headers = {
        "x-api-key": CLAUDE_API_KEY,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }
    body = {
        "model": "claude-3-5-haiku-20241022",
        "max_tokens": 2000,
        "messages": [{"role": "user", "content": prompt}]
    }

    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers=headers,
        json=body,
        timeout=60
    )

    if r.status_code != 200:
        print(f"❌ Claude error: {r.text}")
        return None

    content = r.json()['content'][0]['text']

    try:
        start = content.find('{')
        end = content.rfind('}') + 1
        if start != -1 and end != 0:
            return json.loads(content[start:end])
    except:
        pass

    return {"raw_strategy": content}

# ============================================================
# WEEKLY REPORT FORMATTER
# ============================================================

def format_weekly_report(research, creative, strategy, brand="Clevia"):
    today = datetime.now().strftime('%d %B %Y')
    
    report = f"""🧠 MAGIC SPACE AI BRAIN
📅 Laporan Mingguan — {today}
🏷️ Brand: {brand}

━━━━━━━━━━━━━━━━━━━━━━
📊 RISET PASAR (Groq)
━━━━━━━━━━━━━━━━━━━━━━

🔥 Tren Minggu Ini:
"""
    if research:
        for tren in research.get('tren_pasar', [])[:3]:
            report += f"• {tren}\n"
        
        report += f"\n🎯 Produk Prioritas: {research.get('produk_prioritas', '-')}"
        report += f"\n⏰ Timing Optimal: {research.get('timing_optimal', '-')}"
        report += f"\n\n💡 Summary: {research.get('summary', '-')}"

    report += f"""

━━━━━━━━━━━━━━━━━━━━━━
🎨 RENCANA KONTEN (Gemini)
━━━━━━━━━━━━━━━━━━━━━━
"""
    if creative:
        konten = creative.get('konten_ig', [])
        for i, k in enumerate(konten[:3], 1):
            report += f"\n📌 Konten {i} — {k.get('produk', '')}\n"
            caption = k.get('caption', '')[:200]
            report += f"{caption}...\n"

        artikel = creative.get('artikel_blogger', {})
        if artikel:
            report += f"\n📝 Artikel Blogger:\n_{artikel.get('judul', '-')}_\n"

    report += f"""
━━━━━━━━━━━━━━━━━━━━━━
🧠 STRATEGI (Claude)
━━━━━━━━━━━━━━━━━━━━━━
"""
    if strategy:
        report += f"\n📈 Skor Kesehatan Brand: {strategy.get('skor_kesehatan_brand', '-')}/100\n"
        report += f"\n🎯 Prioritas Minggu Ini:\n"
        for aksi in strategy.get('keputusan_prioritas', [])[:3]:
            report += f"• {aksi}\n"
        
        report += f"\n⚠️ Risiko:\n"
        for risiko in strategy.get('peringatan_risiko', [])[:2]:
            report += f"• {risiko}\n"

        report += f"\n📊 Forecast 4 Minggu:\n_{strategy.get('forecast_4_minggu', '-')}_"
        report += f"\n\n💼 Executive Summary:\n_{strategy.get('executive_summary', '-')}_"

    report += f"\n\n━━━━━━━━━━━━━━━━━━━━━━\n✅ Laporan disimpan ke knowledge base"
    
    return report

# ============================================================
# MAIN ORCHESTRATOR
# ============================================================

if __name__ == "__main__":
    print("🚀 MagicSpace AI Brain starting...")
    brand = "Clevia"

    send_telegram(f"🧠 MagicSpace AI Brain sedang menganalisis pasar untuk {brand}...\n⏳ Mohon tunggu ~2 menit", "Markdown")

    # Load knowledge base
    kb, kb_sha = load_knowledge_base()

    # Agent 1: Research
    print("\n--- AGENT 1: GROQ RESEARCHER ---")
    research = groq_researcher(brand=brand, category="homecare")
    if research:
        print("✅ Research complete")
    else:
        print("❌ Research failed")
        send_telegram("❌ Groq Researcher gagal. Cek API key.")
        exit(1)

    time.sleep(3)

    # Agent 2: Creative
    print("\n--- AGENT 2: GEMINI CREATIVE ---")
    creative = gemini_creative(research, brand=brand)
    if creative:
        print("✅ Creative complete")
    else:
        print("⚠️ Gemini failed, continuing without creative data")
        creative = {}

    time.sleep(3)

    # Agent 3: Strategy
    print("\n--- AGENT 3: CLAUDE STRATEGIST ---")
    strategy = claude_strategist(research, creative, brand=brand)
    if strategy:
        print("✅ Strategy complete")
    else:
        print("⚠️ Claude failed, continuing without strategy data")
        strategy = {}

    # Save to knowledge base
    kb["reports"].append({
        "tanggal": datetime.now().strftime('%Y-%m-%d'),
        "brand": brand,
        "research": research,
        "creative": creative,
        "strategy": strategy
    })

    # Keep only last 12 reports (3 months)
    if len(kb["reports"]) > 12:
        kb["reports"] = kb["reports"][-12:]

    save_knowledge_base(kb, kb_sha)
    print("✅ Knowledge base updated")

    # Format and send report
    report = format_weekly_report(research, creative, strategy, brand=brand)
    send_telegram(report, "Markdown")
    print("✅ Weekly report sent to Telegram!")
    print("\n🎉 MagicSpace AI Brain completed successfully!")
