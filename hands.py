# =============================================================================
# hands.py — Publishing Actions
# Tanggung jawab: Image generation + publish ke IG, FB, Blogger, TikTok
# =============================================================================

import os
import time
import json
import requests

# ── Env vars ──────────────────────────────────────────────────────────────────
HF_API_TOKEN          = os.environ["HF_API_TOKEN"]           # Hugging Face token
IG_ACCESS_TOKEN       = os.environ["INSTAGRAM_ACCESS_TOKEN"]
IG_BUSINESS_ID        = os.environ["INSTAGRAM_BUSINESS_ACCOUNT_ID"]
FB_ACCESS_TOKEN       = os.environ.get("FB_ACCESS_TOKEN", IG_ACCESS_TOKEN)  # biasanya sama
FB_PAGE_ID            = os.environ["FB_PAGE_ID"]
BLOGGER_CLIENT_ID     = os.environ["BLOGGER_CLIENT_ID"]
BLOGGER_CLIENT_SECRET = os.environ["BLOGGER_CLIENT_SECRET"]
BLOGGER_REFRESH_TOKEN = os.environ["BLOGGER_REFRESH_TOKEN"]
BLOGGER_BLOG_ID       = os.environ["BLOGGER_BLOG_ID"]
TIKTOK_ACCESS_TOKEN   = os.environ.get("TIKTOK_ACCESS_TOKEN", "")

# ── Image generation endpoints ────────────────────────────────────────────────
FLUX_API_URL        = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
POLLINATIONS_URL    = "https://image.pollinations.ai/prompt/{prompt}?width=1024&height=1024&nologo=true"


# =============================================================================
# 1. IMAGE GENERATION
# =============================================================================

def _upload_to_imgbb(image_bytes: bytes) -> str:
    """
    Upload image bytes ke ImgBB (free, no account needed for basic use).
    Return: URL publik gambar.
    """
    import base64
    imgbb_key = os.environ.get("IMGBB_API_KEY", "")
    if not imgbb_key:
        raise ValueError("IMGBB_API_KEY tidak ada")
    
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    resp = requests.post(
        "https://api.imgbb.com/1/upload",
        data={"key": imgbb_key, "image": b64},
        timeout=30,
    )
    resp.raise_for_status()
    url = resp.json()["data"]["url"]
    print(f"[HANDS] ✅ ImgBB upload sukses: {url[:60]}...")
    return url


def generate_image(prompt: str, retries: int = 5) -> str:
    """
    Generate gambar via Flux.1 [schnell] di HF Inference API.
    Upload ke ImgBB biar dapet URL publik permanen.
    Fallback ke Pollinations jika HF atau ImgBB gagal.

    Brand mandate: lifestyle-first, subtle Clevia logo,
    NO close-up hands/face, NO product bottles.
    """
    brand_suffix = (
        ", photorealistic Bali resort lifestyle aesthetic, "
        "natural morning light, serene clean atmosphere, "
        "wide shot or medium shot preferred (NOT close-up of hands or face), "
        "if person shown: from behind or side silhouette only, fully clothed modest attire, "
        "small elegant Clevia logo subtly placed in one corner like a premium watermark, "
        "NOT centered, NOT dominant, "
        "NO close-up hands, NO detailed fingers, NO product bottles, NO product packaging"
    )
    full_prompt = prompt + brand_suffix
    print(f"[HANDS] 🎨 Generating image: {prompt[:60]}...")

    # Coba Flux.1 via HF — retry lebih agresif
    for attempt in range(retries):
        try:
            headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
            payload = {"inputs": full_prompt, "parameters": {"num_inference_steps": 4}}
            resp = requests.post(FLUX_API_URL, headers=headers, json=payload, timeout=120)

            if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image"):
                print(f"[HANDS] ✅ Flux.1 generate sukses (attempt {attempt+1})")
                # Upload ke ImgBB biar dapet URL publik
                try:
                    url = _upload_to_imgbb(resp.content)
                    return url
                except Exception as e:
                    print(f"[HANDS] ImgBB upload gagal: {e} — fallback Pollinations")
                    break  # keluar loop, pakai Pollinations

            if resp.status_code == 503:
                wait = (attempt + 1) * 15  # 15s, 30s, 45s, 60s, 75s
                print(f"[HANDS] HF model loading... tunggu {wait}s (attempt {attempt+1}/{retries})")
                time.sleep(wait)
                continue

            if resp.status_code == 429:
                print(f"[HANDS] HF rate limit — tunggu 30s (attempt {attempt+1}/{retries})")
                time.sleep(30)
                continue

            print(f"[HANDS] HF unexpected status {resp.status_code} — fallback Pollinations")
            break

        except Exception as e:
            print(f"[HANDS] HF error: {e}")
            time.sleep(10)

    # Pollinations fallback — short prompt agar URL nggak ditolak Meta API
    import re as _re
    core = _re.split(r'[,.]|\bOR\b|\bNO\b|\bEITHER\b|\bAVOID\b', prompt)[0].strip()
    core = core[:80]
    encoded_prompt = requests.utils.quote(core)
    url = POLLINATIONS_URL.format(prompt=encoded_prompt)
    print(f"[HANDS] 🔗 Pollinations fallback URL ({len(url)} chars)")
    return url


def generate_tiktok_images(prompts: list[str]) -> list[str]:
    """
    Generate 3 gambar untuk TikTok Photo Carousel.
    Dilakukan satu per satu dengan jeda 5 detik (anti-OOM).
    Return: list 3 URL gambar.
    """
    print("[HANDS] 🎬 Generating 3 TikTok carousel images (batch mode)...")
    urls = []
    for i, prompt in enumerate(prompts[:3]):
        print(f"[HANDS] Slide {i+1}/3...")
        url = generate_image(prompt)
        urls.append(url)
        if i < 2:
            print("[HANDS] Jeda 5 detik (memory management)...")
            time.sleep(5)
    print(f"[HANDS] ✅ {len(urls)} gambar TikTok siap")
    return urls


# =============================================================================
# 2. INSTAGRAM
# =============================================================================

def post_instagram(image_url: str, caption: str) -> bool:
    """
    Publish 1 foto ke Instagram Business Account via Meta Graph API.
    Flow: create media container → publish.
    """
    print("[HANDS] 📸 Posting ke Instagram...")
    base = f"https://graph.facebook.com/v19.0/{IG_BUSINESS_ID}"

    # Step 1: Create container
    create_resp = requests.post(
        f"{base}/media",
        params={
            "image_url":     image_url,
            "caption":       caption,
            "access_token":  IG_ACCESS_TOKEN,
        },
        timeout=30,
    )
    create_resp.raise_for_status()
    container_id = create_resp.json().get("id")
    if not container_id:
        print(f"[HANDS] ❌ IG container creation gagal: {create_resp.text}")
        return False

    time.sleep(3)  # tunggu container ready

    # Step 2: Publish
    publish_resp = requests.post(
        f"{base}/media_publish",
        params={
            "creation_id": container_id,
            "access_token": IG_ACCESS_TOKEN,
        },
        timeout=30,
    )
    publish_resp.raise_for_status()
    post_id = publish_resp.json().get("id")
    print(f"[HANDS] ✅ Instagram posted. Post ID: {post_id}")
    return True


# =============================================================================
# 3. FACEBOOK PAGE
# =============================================================================

def post_facebook(image_url: str, caption: str) -> bool:
    """
    Publish foto ke Facebook Page via Graph API.
    """
    print("[HANDS] 📘 Posting ke Facebook Page...")
    url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photos"

    resp = requests.post(url, params={
        "url":          image_url,
        "caption":      caption,
        "access_token": FB_ACCESS_TOKEN,
    }, timeout=30)

    resp.raise_for_status()
    post_id = resp.json().get("id")
    print(f"[HANDS] ✅ Facebook posted. Post ID: {post_id}")
    return True


# =============================================================================
# 4. GOOGLE BLOGGER
# =============================================================================

def _get_blogger_access_token() -> str:
    """
    Tukar refresh_token jadi access_token baru (berlaku 1 jam).
    Dipanggil setiap kali sebelum posting ke Blogger, jadi token selalu fresh.
    """
    print("[HANDS] 🔑 Refreshing Blogger access token...")
    resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id":     BLOGGER_CLIENT_ID,
            "client_secret": BLOGGER_CLIENT_SECRET,
            "refresh_token": BLOGGER_REFRESH_TOKEN,
            "grant_type":    "refresh_token",
        },
        timeout=30,
    )
    resp.raise_for_status()
    access_token = resp.json()["access_token"]
    print("[HANDS] ✅ Blogger access token refreshed")
    return access_token


def post_blogger(title: str, html_content: str, image_url: str) -> bool:
    """
    Publish artikel ke Google Blogger via Blogger API v3.
    HTML content dari Agent 2 langsung dipublish.
    """
    print("[HANDS] 📝 Posting ke Google Blogger...")
    access_token = _get_blogger_access_token()
    url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOGGER_BLOG_ID}/posts/"

    # Sisipkan gambar hero di awal artikel
    full_html = (
        f'<div style="text-align:center;margin-bottom:20px;">'
        f'<img src="{image_url}" alt="{title}" style="max-width:100%;border-radius:8px;"/>'
        f'</div>\n{html_content}'
    )

    payload = {
        "kind":    "blogger#post",
        "title":   title,
        "content": full_html,
        "labels":  ["Clevia", "Kebersihan", "Lifestyle", "Tips Rumah"],
    }

    resp = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type":  "application/json",
        },
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    post_url = resp.json().get("url", "")
    print(f"[HANDS] ✅ Blogger posted: {post_url}")
    return True


# =============================================================================
# 5. TIKTOK (Photo Carousel Mode)
# =============================================================================

def post_tiktok_carousel(image_urls: list[str], caption: str) -> bool:
    """
    Publish TikTok Photo Carousel (3 slides) via TikTok Content Posting API.
    Requires: TIKTOK_ACCESS_TOKEN dengan scope video.publish.
    """
    if not TIKTOK_ACCESS_TOKEN:
        print("[HANDS] ⚠️  TikTok access token tidak ada — skip TikTok posting")
        return False

    print("[HANDS] 🎵 Posting ke TikTok Photo Carousel...")

    # Step 1: Initialize photo post
    init_url = "https://open.tiktokapis.com/v2/post/publish/content/init/"
    init_payload = {
        "post_info": {
            "title":           caption[:2200],
            "privacy_level":   "PUBLIC_TO_EVERYONE",
            "disable_duet":    False,
            "disable_comment": False,
            "disable_stitch":  False,
        },
        "source_info": {
            "source":     "PULL_FROM_URL",
            "photo_urls": image_urls[:3],
        },
        "post_mode":    "DIRECT_POST",
        "media_type":   "PHOTO",
    }

    headers = {
        "Authorization": f"Bearer {TIKTOK_ACCESS_TOKEN}",
        "Content-Type":  "application/json; charset=UTF-8",
    }

    resp = requests.post(init_url, headers=headers, json=init_payload, timeout=60)

    if resp.status_code != 200:
        print(f"[HANDS] ❌ TikTok posting gagal: {resp.status_code} — {resp.text[:200]}")
        return False

    publish_id = resp.json().get("data", {}).get("publish_id")
    print(f"[HANDS] ✅ TikTok carousel submitted. Publish ID: {publish_id}")
    return True
