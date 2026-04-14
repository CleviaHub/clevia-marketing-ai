# =============================================================================
# main.py — Conductor / Orchestrator
# Alur: LEGS (fetch) → BRAIN (think) → LEGS (approve) → HANDS (publish)
# =============================================================================

import sys
import json
import traceback
from datetime import datetime

# ── Import modul ──────────────────────────────────────────────────────────────
from legs  import (fetch_rss_trends, send_telegram_preview,
                   wait_for_approval, notify_telegram)
from brain import (agent1_researcher, agent2_creative_director,
                   get_current_chapter_context, select_product)
from hands import (generate_image, generate_tiktok_images,
                   post_instagram, post_facebook,
                   post_blogger, post_tiktok_carousel)

MAX_RETRY_CYCLES = 2  # max re-generate setelah REJECT


# =============================================================================
# MAIN PIPELINE
# =============================================================================

def run():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M WIB")
    print(f"\n{'='*60}")
    print(f"  🏭 CLEVIA CONTENT FACTORY — {timestamp}")
    print(f"{'='*60}\n")

    notify_telegram(f"🏭 Clevia Content Factory dimulai\n🕐 {timestamp}")

    try:
        # ── LEGS: Fetch data ───────────────────────────────────────────────
        print("📡 [FASE 1] LEGS — Fetching RSS trends...")
        rss_raw = fetch_rss_trends(max_articles=10)

        # ── BRAIN: Agent 1 ─────────────────────────────────────────────────
        print("\n🔍 [FASE 2] BRAIN — Agent 1: Researcher (Groq)...")
        trend_data = agent1_researcher(rss_raw)

        # Deteksi chapter context + pilih produk
        chapter_ctx = get_current_chapter_context()
        product     = select_product(chapter_ctx)

        # ── BRAIN: Agent 2 + HANDS: Image Gen (loop jika REJECT) ──────────
        for attempt in range(MAX_RETRY_CYCLES + 1):
            if attempt > 0:
                print(f"\n🔄 Regenerating konten (attempt {attempt + 1})...")
                notify_telegram(f"🔄 Regenerating konten — attempt {attempt + 1}")

            print(f"\n🎨 [FASE 3] BRAIN — Agent 2: Creative Director (GLM-5.1)...")
            content = agent2_creative_director(trend_data, product, chapter_ctx)

            print("\n🖼️  [FASE 4] HANDS — Generating hero image...")
            hero_image_url = generate_image(content["hero_image_prompt"])

            # ── LEGS: Kirim ke Telegram untuk approval ─────────────────────
            print("\n📱 [FASE 5] LEGS — Kirim preview ke Telegram...")
            send_telegram_preview(
                image_url     = hero_image_url,
                caption_preview = content["caption_ig"],
                article_title   = content["article_title"],
            )

            approved, feedback = wait_for_approval(timeout_seconds=300)

            if approved:
                print("\n✅ Konten APPROVED — lanjut ke publishing...")
                break
            elif feedback == "timeout":
                print("\n⏰ Timeout — auto-skip posting hari ini")
                notify_telegram("⏰ Tidak ada respons 5 menit — posting dibatalkan hari ini.")
                sys.exit(0)
            else:
                print(f"\n❌ REJECTED. Feedback: {feedback}")
                notify_telegram(f"❌ Rejected. Feedback: {feedback}\n🔄 Regenerating...")
                if attempt == MAX_RETRY_CYCLES:
                    notify_telegram("⛔ Max retry tercapai — posting dibatalkan.")
                    sys.exit(0)
                # Sertakan feedback ke agent 2 di iterasi berikutnya
                trend_data["editor_feedback"] = feedback
                continue

        # ── HANDS: Generate TikTok images (batch, 5s delay antar slide) ────
        print("\n🎬 [FASE 6] HANDS — Generating TikTok carousel images...")
        tiktok_urls = generate_tiktok_images(content["tiktok_image_prompts"])

        # ── HANDS: Multichannel publish ────────────────────────────────────
        print("\n🚀 [FASE 7] HANDS — Multichannel publishing...")
        results = {}

        print("  📸 Instagram...")
        results["instagram"] = post_instagram(hero_image_url, content["caption_ig"])

        print("  📘 Facebook...")
        results["facebook"] = post_facebook(hero_image_url, content["caption_fb"])

        print("  📝 Blogger...")
        results["blogger"] = post_blogger(
            title        = content["article_title"],
            html_content = content["article_html"],
            image_url    = hero_image_url,
        )

        print("  🎵 TikTok...")
        results["tiktok"] = post_tiktok_carousel(tiktok_urls, content["caption_ig"])

        # ── Summary ────────────────────────────────────────────────────────
        success_count = sum(1 for v in results.values() if v)
        total         = len(results)

        summary = (
            f"✅ Clevia Content Factory selesai!\n\n"
            f"📊 Hasil Publishing ({success_count}/{total}):\n"
            f"{'✅' if results['instagram'] else '❌'} Instagram\n"
            f"{'✅' if results['facebook']  else '❌'} Facebook\n"
            f"{'✅' if results['blogger']   else '❌'} Blogger\n"
            f"{'✅' if results['tiktok']    else '❌'} TikTok\n\n"
            f"📰 Artikel: {content['article_title']}\n"
            f"🕐 {timestamp}"
        )
        print(f"\n{summary}")
        notify_telegram(summary)

    except Exception as e:
        error_msg = f"❌ ERROR pada Content Factory\n\n`{type(e)._name_}: {str(e)[:300]}`"
        print(f"\n[MAIN] FATAL ERROR: {e}")
        traceback.print_exc()
        notify_telegram(error_msg)
        sys.exit(1)


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    run()
