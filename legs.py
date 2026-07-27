# =============================================================================
# legs.py — Data Fetching & Triggers
# Tanggung jawab: RSS ingestion, Telegram gateway, GitHub keep-alive
# =============================================================================

import os
import time
import json
import requests
import feedparser

# ── Env vars ──────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID   = os.environ["TELEGRAM_CHAT_ID"]

# ── RSS Sources ───────────────────────────────────────────────────────────────
RSS_FEEDS = [
    "https://news.google.com/rss/search?q=pembersih+rumah+Indonesia&hl=id&gl=ID&ceid=ID:id",
    "https://news.google.com/rss/search?q=produk+kebersihan+rumah+tangga&hl=id&gl=ID&ceid=ID:id",
    "https://news.google.com/rss/search?q=homecare+cleaning+product+Indonesia&hl=id&gl=ID&ceid=ID:id",
]

# =============================================================================
# 1. RSS FETCHER
# =============================================================================

def fetch_rss_trends(max_articles: int = 10) -> str:
    """
    Menarik berita dari RSS feeds Google News.
    Return: raw string berisi judul + summary artikel untuk dianalisis Agent 1.
    """
    articles = []
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:max_articles // len(RSS_FEEDS) + 1]:
                title   = entry.get("title", "")
                summary = entry.get("summary", "")
                articles.append(f"- {title}: {summary}")
        except Exception as e:
            print(f"[LEGS] RSS fetch error ({url}): {e}")

    if not articles:
        # Fallback: pakai topik evergreen kalau RSS gagal
        articles = [
            "- Tren kebersihan rumah 2026: konsumen makin pilih produk ramah lingkungan",
            "- Keluhan utama ibu rumah tangga: lantai masih licin setelah dipel",
            "- Produk pembersih serbaguna makin diminati keluarga muda Indonesia",
        ]
        print("[LEGS] Menggunakan fallback topics (RSS tidak tersedia)")

    raw_text = "\n".join(articles[:max_articles])
    print(f"[LEGS] Berhasil fetch {len(articles)} artikel")
    return raw_text


# =============================================================================
# 2. TELEGRAM GATEWAY
# =============================================================================

def send_telegram_preview(image_url: str, caption_preview: str, article_title: str) -> str:
    """
    Kirim preview konten ke Telegram dengan Inline Keyboard APPROVE / REJECT.
    Return: message_id dari pesan yang dikirim.
    """
    tg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"

    short_preview = caption_preview[:300] + "..." if len(caption_preview) > 300 else caption_preview

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "photo": image_url,
        "caption": (
            f"📋 PREVIEW KONTEN CLEVIA\n\n"
            f"📰 Artikel: {article_title}\n\n"
            f"📝 Caption Preview:\n{short_preview}\n\n"
            f"Tekan tombol di bawah untuk keputusan:"
        ),
        "parse_mode": "Markdown",
        "reply_markup": json.dumps({
            "inline_keyboard": [[
                {"text": "✅ APPROVE", "callback_data": "APPROVE"},
                {"text": "❌ REJECT",  "callback_data": "REJECT"},
            ]]
        }),
    }

    resp = requests.post(tg_url, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    message_id = str(data["result"]["message_id"])
    print(f"[LEGS] Preview terkirim ke Telegram. Message ID: {message_id}")
    return message_id


def wait_for_approval(timeout_seconds: int = 300, poll_interval: int = 5) -> tuple[bool, str]:
    """
    Polling Telegram getUpdates sampai user klik APPROVE atau REJECT.
    Return: (approved: bool, feedback: str)
    - Jika APPROVE → (True, "")
    - Jika REJECT  → (True, pesan feedback dari user)
    - Jika timeout → (False, "timeout")
    """
    tg_url  = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    elapsed = 0
    offset  = None

    print(f"[LEGS] Menunggu approval Telegram (max {timeout_seconds}s)...")

    while elapsed < timeout_seconds:
        params = {"timeout": poll_interval, "allowed_updates": ["callback_query", "message"]}
        if offset:
            params["offset"] = offset

        try:
            resp    = requests.get(tg_url, params=params, timeout=poll_interval + 5)
            updates = resp.json().get("result", [])
        except Exception as e:
            print(f"[LEGS] Polling error: {e}")
            time.sleep(poll_interval)
            elapsed += poll_interval
            continue

        for update in updates:
            offset = update["update_id"] + 1  # mark as read

            # Callback dari inline keyboard
            if "callback_query" in update:
                cb   = update["callback_query"]
                data = cb.get("data", "")

                # Acknowledge callback agar tombol tidak loading
                requests.post(
                    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery",
                    json={"callback_query_id": cb["id"]},
                    timeout=10,
                )

                if data == "APPROVE":
                    print("[LEGS] ✅ User menekan APPROVE")
                    return True, ""

                if data == "REJECT":
                    print("[LEGS] ❌ User menekan REJECT — menunggu feedback...")
                    feedback = _wait_for_feedback_text(offset, timeout=60)
                    return False, feedback

        elapsed += poll_interval

    print("[LEGS] ⏰ Timeout — tidak ada respons dari Telegram")
    return False, "timeout"


def _wait_for_feedback_text(offset: int, timeout: int = 60) -> str:
    """
    Setelah REJECT, tunggu pesan teks feedback dari user.
    """
    tg_url  = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    elapsed = 0

    while elapsed < timeout:
        params = {"timeout": 5, "offset": offset, "allowed_updates": ["message"]}
        try:
            resp    = requests.get(tg_url, params=params, timeout=10)
            updates = resp.json().get("result", [])
        except Exception:
            time.sleep(5)
            elapsed += 5
            continue

        for update in updates:
            if "message" in update and "text" in update["message"]:
                feedback = update["message"]["text"]
                print(f"[LEGS] Feedback diterima: {feedback}")
                return feedback

        elapsed += 5

    return "Tidak ada feedback spesifik"


def notify_telegram(message: str) -> None:
    """Kirim notifikasi teks biasa ke Telegram (untuk log/error)."""
    tg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(tg_url, json={
        "chat_id":    TELEGRAM_CHAT_ID,
        "text":       message,
        "parse_mode": "Markdown",
    }, timeout=15)


# =============================================================================
# 3. GITHUB KEEP-ALIVE (dipanggil dari workflow yml)
# =============================================================================

def keep_repo_alive() -> None:
    """
    Dummy function — keep-alive sudah dihandle di brain_workflow.yml
    via step 'Keep Repo Active' yang melakukan git commit kosong.
    Fungsi ini ada sebagai dokumentasi saja.
    """
    print("[LEGS] Keep-alive dihandle oleh GitHub Actions workflow.")
