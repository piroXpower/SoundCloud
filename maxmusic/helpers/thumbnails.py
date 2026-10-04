import asyncio
import io
import os
import aiohttp
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
from maxmusic.config import config
from maxmusic.core.downloader import Track

FONT_DIR = "/root/MaxMusicV2/maxmusic/assets/fonts"
FONT_BOLD = os.path.join(FONT_DIR, "Raleway-Bold.ttf")
FONT_TITLE = os.path.join(FONT_DIR, "Poppins-ExtraBold.ttf")
FONT_LIGHT = os.path.join(FONT_DIR, "Inter-Light.ttf")


def _get_font(font_path: str, size: int):
    try:
        if os.path.exists(font_path):
            return ImageFont.truetype(font_path, size)
    except Exception:
        pass
    return ImageFont.load_default()


def _draw_rounded_rect(draw, box, radius, fill):
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def _generate_thumb_sync(track: Track, cover_bytes: bytes | None) -> str:
    width, height = 1280, 720
    # Create dark base canvas
    base = Image.new("RGBA", (width, height), (15, 17, 26, 255))

    # Background art blur effect
    if cover_bytes:
        try:
            bg_art = Image.open(io.BytesIO(cover_bytes)).convert("RGBA")
            bg_art = bg_art.resize((width, height))
            bg_art = bg_art.filter(ImageFilter.GaussianBlur(40))
            # Darken blurred background
            dark_overlay = Image.new("RGBA", (width, height), (10, 12, 20, 190))
            base.paste(bg_art, (0, 0))
            base.alpha_composite(dark_overlay)
        except Exception:
            pass

    draw = ImageDraw.Draw(base)

    # Left: Album Cover Art (Card)
    card_size = 460
    card_x, card_y = 90, (height - card_size) // 2

    # Draw card shadow
    shadow = Image.new("RGBA", (card_size + 20, card_size + 20), (0, 0, 0, 100))
    base.paste(shadow, (card_x - 10, card_y - 5), mask=shadow)

    if cover_bytes:
        try:
            cover = Image.open(io.BytesIO(cover_bytes)).convert("RGBA")
            cover = cover.resize((card_size, card_size))
            # Round corners mask
            mask = Image.new("L", (card_size, card_size), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.rounded_rectangle((0, 0, card_size, card_size), radius=28, fill=255)
            base.paste(cover, (card_x, card_y), mask=mask)
        except Exception:
            _draw_rounded_rect(draw, (card_x, card_y, card_x + card_size, card_y + card_size), 28, (35, 40, 60))
    else:
        _draw_rounded_rect(draw, (card_x, card_y, card_x + card_size, card_y + card_size), 28, (35, 40, 60))

    # Right Content Area
    right_x = 600
    content_y = 150

    # Brand Pill
    pill_font = _get_font(FONT_BOLD, 22)
    _draw_rounded_rect(draw, (right_x, content_y, right_x + 190, content_y + 42), 12, (230, 57, 70, 220))
    draw.text((right_x + 20, content_y + 9), config.BOT_NAME.upper(), font=pill_font, fill=(255, 255, 255))

    # Track Title
    title_font = _get_font(FONT_TITLE, 44)
    raw_title = track.title or "Unknown Track"
    if len(raw_title) > 32:
        title_line1 = raw_title[:32]
        title_line2 = raw_title[32:62] + ("..." if len(raw_title) > 62 else "")
    else:
        title_line1 = raw_title
        title_line2 = ""

    draw.text((right_x, content_y + 70), title_line1, font=title_font, fill=(255, 255, 255))
    if title_line2:
        draw.text((right_x, content_y + 130), title_line2, font=title_font, fill=(210, 215, 230))

    # Requester & Duration info
    info_font = _get_font(FONT_LIGHT, 26)
    meta_y = content_y + (195 if title_line2 else 150)
    req_text = f"Requested By: {track.requester or 'User'}"
    draw.text((right_x, meta_y), req_text, font=info_font, fill=(180, 190, 210))

    # Progress Bar
    bar_y = meta_y + 70
    bar_w = 560
    bar_h = 10
    _draw_rounded_rect(draw, (right_x, bar_y, right_x + bar_w, bar_y + bar_h), 5, (60, 68, 90))
    # Played portion (aesthetic 35% default on start)
    played_w = int(bar_w * 0.35)
    _draw_rounded_rect(draw, (right_x, bar_y, right_x + played_w, bar_y + bar_h), 5, (230, 57, 70))
    # Glowing dot
    draw.ellipse((right_x + played_w - 9, bar_y - 4, right_x + played_w + 9, bar_y + bar_h + 4), fill=(255, 255, 255))

    # Time labels below bar
    time_font = _get_font(FONT_BOLD, 22)
    draw.text((right_x, bar_y + 22), "0:00", font=time_font, fill=(150, 160, 180))
    draw.text((right_x + bar_w - 70, bar_y + 22), track.duration or "Live", font=time_font, fill=(150, 160, 180))

    # Save to cache
    output_path = os.path.join("cache", f"thumb_{track.video_id or 'temp'}.png")
    base.convert("RGB").save(output_path, "PNG", quality=95)
    return output_path


async def generate_thumbnail(track: Track) -> str:
    cover_bytes = None
    if track.thumbnail and track.thumbnail.startswith("http"):
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(track.thumbnail) as resp:
                    if resp.status == 200:
                        cover_bytes = await resp.read()
        except Exception:
            pass

    return await asyncio.to_thread(_generate_thumb_sync, track, cover_bytes)
