import os
import io
import aiohttp
import asyncio
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

CACHE_DIR = "/tmp/sc_thumbnails"
os.makedirs(CACHE_DIR, exist_ok=True)

def _format_duration(seconds: int) -> str:
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

def _truncate_text(text: str, max_chars: int) -> str:
    if len(text) > max_chars:
        return text[:max_chars - 3] + "..."
    return text

def _generate_thumbnail_sync(
    cover_bytes: bytes,
    title: str,
    artist: str,
    duration_sec: int,
    output_path: str,
) -> str:
    # Canvas dimensions
    width, height = 1280, 720
    
    # Base Cover
    if cover_bytes:
        try:
            original_cover = Image.open(io.BytesIO(cover_bytes)).convert("RGBA")
        except Exception:
            original_cover = Image.new("RGBA", (500, 500), color=(30, 30, 30, 255))
    else:
        original_cover = Image.new("RGBA", (500, 500), color=(30, 30, 30, 255))

    # 1. Background: Blurred & Darkened Album Art
    bg = original_cover.resize((width, height), Image.Resampling.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(35))
    
    # Dark gradient overlay
    overlay = Image.new("RGBA", (width, height), (10, 10, 15, 195))
    canvas = Image.alpha_composite(bg, overlay)
    draw = ImageDraw.Draw(canvas)

    # 2. Modern Accent Gradients & Borders
    # Glowing corner glow
    accent_orange = (255, 85, 0) # SoundCloud Signature Orange
    accent_purple = (147, 51, 234)

    # Top-left accent strip
    draw.rectangle([(0, 0), (1280, 8)], fill=accent_orange)

    # 3. Album Cover Card (Left side)
    card_size = 460
    card_x, card_y = 100, 130
    
    cover_resized = original_cover.resize((card_size, card_size), Image.Resampling.LANCZOS)
    
    # Create rounded corners mask
    mask = Image.new("L", (card_size, card_size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([(0, 0), (card_size, card_size)], radius=36, fill=255)

    # Shadow for card
    shadow_offset = 12
    shadow_box = Image.new("RGBA", (card_size + 24, card_size + 24), (0, 0, 0, 140))
    shadow_mask = Image.new("L", (card_size + 24, card_size + 24), 0)
    ImageDraw.Draw(shadow_mask).rounded_rectangle([(0, 0), (card_size + 24, card_size + 24)], radius=42, fill=255)
    canvas.paste(shadow_box, (card_x - 12 + shadow_offset, card_y - 12 + shadow_offset), shadow_mask)

    # Paste rounded album cover
    canvas.paste(cover_resized, (card_x, card_y), mask)

    # Outline border around card
    draw.rounded_rectangle(
        [(card_x - 2, card_y - 2), (card_x + card_size + 2, card_y + card_size + 2)],
        radius=38,
        outline=(255, 102, 0, 220),
        width=4
    )

    # 4. Typography & Details (Right side)
    text_x = 610
    
    # Fonts loading (fallback to default if system font not found)
    try:
        font_badge = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 46)
        font_artist = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
        font_meta = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
    except Exception:
        font_badge = ImageFont.load_default()
        font_title = ImageFont.load_default()
        font_artist = ImageFont.load_default()
        font_meta = ImageFont.load_default()

    # Pill Badge: "SOUNDCLOUD MUSIC"
    badge_text = "  ☁ SOUNDCLOUD STREAMING  "
    badge_y = 150
    draw.rounded_rectangle(
        [(text_x, badge_y), (text_x + 360, badge_y + 44)],
        radius=22,
        fill=(255, 85, 0, 230)
    )
    draw.text((text_x + 18, badge_y + 8), badge_text, fill=(255, 255, 255), font=font_badge)

    # Track Title
    title_y = 230
    clean_title = _truncate_text(title, 26)
    draw.text((text_x, title_y), clean_title, fill=(255, 255, 255), font=font_title)

    # Artist Name
    artist_y = 310
    clean_artist = _truncate_text(f"by {artist}", 34)
    draw.text((text_x, artist_y), clean_artist, fill=(200, 200, 215), font=font_artist)

    # Visual Music Progress Bar
    bar_y = 410
    bar_width = 540
    bar_height = 10
    
    # Progress bar track background
    draw.rounded_rectangle(
        [(text_x, bar_y), (text_x + bar_width, bar_y + bar_height)],
        radius=5,
        fill=(60, 60, 80, 220)
    )
    
    # Progress fill (e.g. 40%)
    filled_width = int(bar_width * 0.42)
    draw.rounded_rectangle(
        [(text_x, bar_y), (text_x + filled_width, bar_y + bar_height)],
        radius=5,
        fill=(255, 102, 0)
    )
    
    # Progress indicator circle
    circle_x = text_x + filled_width
    draw.ellipse([(circle_x - 10, bar_y - 5), (circle_x + 10, bar_y + 15)], fill=(255, 255, 255))

    # Duration timestamps
    duration_str = _format_duration(duration_sec)
    time_label = f"01:15  /  {duration_str}"
    draw.text((text_x, bar_y + 24), time_label, fill=(180, 180, 195), font=font_meta)

    # Quality Badges
    badge2_y = 505
    # High-Res Audio Badge
    draw.rounded_rectangle([(text_x, badge2_y), (text_x + 140, badge2_y + 36)], radius=12, fill=(40, 40, 55, 220), outline=(80, 80, 100))
    draw.text((text_x + 22, badge2_y + 6), "320 KBPS", fill=(255, 255, 255), font=font_badge)

    # Lossless / Stereo Badge
    draw.rounded_rectangle([(text_x + 160, badge2_y), (text_x + 280, badge2_y + 36)], radius=12, fill=(40, 40, 55, 220), outline=(80, 80, 100))
    draw.text((text_x + 182, badge2_y + 6), "STEREO", fill=(255, 255, 255), font=font_badge)

    # Save to disk
    final_image = canvas.convert("RGB")
    final_image.save(output_path, "JPEG", quality=95)
    return output_path

class ThumbnailGenerator:
    @staticmethod
    async def create_thumbnail(
        cover_url: str,
        title: str,
        artist: str,
        duration_sec: int,
        track_id: str,
    ) -> str:
        output_file = os.path.join(CACHE_DIR, f"thumb_{track_id}.jpg")
        if os.path.exists(output_file):
            return output_file

        cover_bytes = b""
        if cover_url:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(cover_url, timeout=10) as resp:
                        if resp.status == 200:
                            cover_bytes = await resp.read()
            except Exception as e:
                print(f"[Thumbnail Download Error] {e}")

        return await asyncio.to_thread(
            _generate_thumbnail_sync,
            cover_bytes,
            title,
            artist,
            duration_sec,
            output_file,
        )

thumbnail_gen = ThumbnailGenerator()
