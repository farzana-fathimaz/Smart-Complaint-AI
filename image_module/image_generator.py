"""
image_generator.py
──────────────────
Sends complaint text to MonsterAPI and generates a
representative image. Saves the image locally.
"""

import requests
import os
import time
from datetime import datetime
from decouple import config

# ── Load API key from .env ────────────────────────────────
MONSTER_API_KEY = config("MONSTER_API_KEY", default="")

# ── API endpoints ─────────────────────────────────────────
GENERATE_URL = "https://api.monsterapi.ai/v1/generate/txt2img"

# ── Output folder for saved images ───────────────────────
OUTPUT_DIR = "generated_images"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def build_prompt(complaint_text: str) -> str:
    """
    Converts a raw complaint description into a detailed
    image generation prompt for better visual output.

    Args:
        complaint_text: Raw complaint from user speech

    Returns:
        Enhanced prompt string for MonsterAPI
    """
    # Detect complaint type from keywords and tailor prompt
    text_lower = complaint_text.lower()

    if any(w in text_lower for w in ["water", "pipe", "leak", "flood", "plumb"]):
        style = "water damage, flooded room, broken pipe, photorealistic"
    elif any(w in text_lower for w in ["electric", "power", "light", "switch", "wire"]):
        style = "electrical problem, dark room, broken wires, photorealistic"
    elif any(w in text_lower for w in ["road", "pothole", "street", "pavement"]):
        style = "damaged road, pothole, broken pavement, urban photography"
    elif any(w in text_lower for w in ["garbage", "waste", "trash", "dirty", "clean"]):
        style = "garbage pile, dirty area, urban waste, photorealistic"
    elif any(w in text_lower for w in ["lift", "elevator", "stairs"]):
        style = "broken elevator, maintenance sign, photorealistic"
    else:
        style = "infrastructure problem, building issue, photorealistic"

    prompt = (
        f"A photorealistic image showing: {complaint_text}. "
        f"Style: {style}. "
        f"High quality, detailed, professional photography, 4K resolution. "
        f"No people, no text overlays."
    )

    return prompt


def generate_image(complaint_text: str) -> str | None:
    """
    Generates an image from complaint text using MonsterAPI.

    Args:
        complaint_text: The complaint description

    Returns:
        Local file path of saved image, or None if failed.
    """
    if not MONSTER_API_KEY:
        print("❌ MONSTER_API_KEY not found in .env file.")
        print("   Get a free key at: https://monsterapi.ai/")
        return None

    # Build an enhanced prompt
    prompt = build_prompt(complaint_text)
    print(f"\n📝 Generated Prompt:\n   {prompt[:120]}...")

    # ── API Request ───────────────────────────────────────
    headers = {
        "Authorization": f"Bearer {MONSTER_API_KEY}",
        "Content-Type" : "application/json",
    }

    payload = {
        "prompt"         : prompt,
        "negprompt"      : "blurry, low quality, cartoon, anime, text, watermark, people, faces",
        "samples"        : 1,
        "steps"          : 30,
        "aspect_ratio"   : "landscape",
        "guidance_scale" : 7.5,
        "seed"           : 42,
    }

    print("\n⏳ Sending request to MonsterAPI...")

    try:
        response = requests.post(GENERATE_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        # ── Poll for result if async ──────────────────────
        process_id = data.get("process_id")
        if process_id:
            return _poll_for_result(process_id, headers, complaint_text)

        # ── Direct response with image URL ────────────────
        image_url = _extract_image_url(data)
        if image_url:
            return _download_image(image_url, complaint_text)

        print(f"❌ Unexpected API response: {data}")
        return None

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to MonsterAPI. Check your internet connection.")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"❌ API Error {response.status_code}: {e}")
        if response.status_code == 401:
            print("   Invalid API key. Check your .env file.")
        return None
    except requests.exceptions.Timeout:
        print("❌ Request timed out. MonsterAPI may be slow. Try again.")
        return None


def _poll_for_result(process_id: str, headers: dict, complaint_text: str,
                     max_attempts: int = 20) -> str | None:
    """
    Polls MonsterAPI for async image generation result.
    MonsterAPI uses a process ID for async jobs.
    """
    status_url = f"https://api.monsterapi.ai/v1/status/{process_id}"

    print(f"⏳ Waiting for image generation (process: {process_id})...")

    for attempt in range(1, max_attempts + 1):
        time.sleep(5)  # Wait 5 seconds between polls
        print(f"   Checking... attempt {attempt}/{max_attempts}")

        try:
            res  = requests.get(status_url, headers=headers, timeout=15)
            data = res.json()

            status = data.get("status", "").lower()

            if status in ("completed", "success", "complete"):
                image_url = _extract_image_url(data)
                if image_url:
                    return _download_image(image_url, complaint_text)

            elif status in ("failed", "error"):
                print(f"❌ Generation failed: {data.get('message', 'Unknown error')}")
                return None

            # Still processing — continue polling
            print(f"   Status: {status}. Still processing...")

        except requests.exceptions.RequestException as e:
            print(f"   Poll error: {e}")

    print("❌ Image generation timed out after maximum attempts.")
    return None


def _extract_image_url(data: dict) -> str | None:
    """Extracts image URL from various possible response structures."""
    # Try common key patterns
    for key in ["output", "result", "image_url", "url", "images"]:
        val = data.get(key)
        if isinstance(val, str) and val.startswith("http"):
            return val
        if isinstance(val, list) and val:
            first = val[0]
            if isinstance(first, str) and first.startswith("http"):
                return first
            if isinstance(first, dict):
                for sub_key in ["url", "image", "image_url"]:
                    if first.get(sub_key, "").startswith("http"):
                        return first[sub_key]
    return None


def _download_image(url: str, complaint_text: str) -> str | None:
    """
    Downloads an image from URL and saves it locally.

    Returns:
        Local file path, or None if download failed.
    """
    print(f"\n📥 Downloading generated image...")

    try:
        res = requests.get(url, timeout=30, stream=True)
        res.raise_for_status()

        # Create a descriptive filename
        timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
        short_desc  = "_".join(complaint_text.lower().split()[:4])
        short_desc  = "".join(c for c in short_desc if c.isalnum() or c == "_")
        filename    = f"{timestamp}_{short_desc}.png"
        filepath    = os.path.join(OUTPUT_DIR, filename)

        with open(filepath, "wb") as f:
            for chunk in res.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"✅ Image saved: {filepath}")
        return filepath

    except Exception as e:
        print(f"❌ Failed to download image: {e}")
        return None