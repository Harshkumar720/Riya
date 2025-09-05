# Backend/ImageGeneration.py
import os
import requests
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
import time

# ---------- Load .env from project root ----------
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENV_PATH = os.path.join(ROOT_DIR, ".env")
load_dotenv(ENV_PATH)

IDEOGRAM_API_KEY = os.getenv("IDEOGRAM_API_KEY")
if not IDEOGRAM_API_KEY:
    raise ValueError("❌ No Ideogram API key found. Add IDEOGRAM_API_KEY=... to your .env")

# ---------- Defaults ----------
ALLOWED_RATIOS = {
    "1x3","3x1","1x2","2x1","9x16","16x9","10x16","16x10",
    "2x3","3x2","3x4","4x3","4x5","5x4","1x1"
}
ASPECT_RATIO   = "1x1"         # default square
RENDERING      = "TURBO"       # TURBO | DEFAULT | QUALITY
DEFAULT_IMAGES = 5
TIMEOUT        = 90
SAVE_DIR       = "GeneratedImages"

os.makedirs(SAVE_DIR, exist_ok=True)

V3_ENDPOINT = "https://api.ideogram.ai/v1/ideogram-v3/generate"
HEADERS = {
    "Api-Key": IDEOGRAM_API_KEY,
    "Content-Type": "application/json",
}

def _normalize_ratio(r: str) -> str:
    """Convert '1:1' -> '1x1', and validate."""
    if not r:
        return "1x1"
    r = r.replace(":", "x").lower()
    return r if r in ALLOWED_RATIOS else "1x1"

def _download_image(url: str) -> Image.Image:
    r = requests.get(url, timeout=TIMEOUT)
    r.raise_for_status()
    return Image.open(BytesIO(r.content))

def _ideogram_v3_generate(prompt: str, num_images: int):
    """Call Ideogram v3 generate with JSON body."""
    payload = {
        "prompt": prompt,
        "rendering_speed": RENDERING,
        "aspect_ratio": _normalize_ratio(ASPECT_RATIO),
        "num_images": max(1, min(int(num_images), 8)),  # clamp 1..8
    }

    resp = requests.post(V3_ENDPOINT, headers=HEADERS, json=payload, timeout=TIMEOUT)
    if resp.status_code != 200:
        raise RuntimeError(f"❌ Ideogram API error {resp.status_code}: {resp.text[:300]}")
    return resp.json()

def _extract_urls(result_json):
    """Find image URLs in API response."""
    urls = []
    data = result_json.get("data")
    if isinstance(data, list):
        for item in data:
            url = item.get("url")
            if isinstance(url, str) and url.startswith("http"):
                urls.append(url)
    return urls

def generate_one(prompt: str, out_dir: str, idx: int) -> str | None:
    try:
        result = _ideogram_v3_generate(prompt, num_images=1)
        urls = _extract_urls(result)
        if not urls:
            print(f"⚠️ API returned no image URLs. Raw: {str(result)[:200]}")
            return None

        img = _download_image(urls[0])

        # ✅ Save image
        safe_prefix = (prompt[:10].strip().replace(" ", "_") or "img")
        fname = f"{safe_prefix}_{idx+1}.png"
        path = os.path.join(out_dir, fname)
        img.save(path)

        # ✅ Show image on screen
        img.show(title=f"{prompt} #{idx+1}")

        print(f"✅ Saved and displayed: {path}")
        return path
    except Exception as e:
        print(f"⚠️ Error generating image: {e}")
        return None

def generate_images(prompt: str, num_images: int = DEFAULT_IMAGES):
    safe_dir = prompt[:30].strip().replace(" ", "_") or "images"
    out_dir = os.path.join(SAVE_DIR, safe_dir)
    os.makedirs(out_dir, exist_ok=True)

    saved = []
    for i in range(num_images):
        path = generate_one(prompt, out_dir, i)
        if path:
            saved.append(path)
        else:
            print("⚠️ Failed to generate this image, moving on…")
        time.sleep(0.3)
    return saved

# -------------- CLI (simple) --------------
if __name__ == "__main__":
    print("🖼  Ideogram v3 Image Generator")
    prompt = input("Prompt: ").strip()
    if not prompt:
        print("❌ Empty prompt.")
        raise SystemExit(1)

    try:
        n = input(f"How many images? (default {DEFAULT_IMAGES}): ").strip()
        n = int(n) if n else DEFAULT_IMAGES
    except ValueError:
        n = DEFAULT_IMAGES

    paths = generate_images(prompt, num_images=n)
    if paths:
        print(f"✅ Done. Files saved in {os.path.join(SAVE_DIR, prompt[:30].strip().replace(' ', '_'))}")
    else:
        print("❌ No images generated.")

