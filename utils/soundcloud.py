import asyncio
import re
from typing import Dict, Any, Optional
import yt_dlp

SOUNDCLOUD_REGEX = re.compile(
    r"^https?://(www\.)?soundcloud\.com/([\w\d_-]+)/([\w\d_-]+)/?.*$"
)

class SoundCloudAPI:
    def __init__(self):
        self.ydl_opts = {
            "format": "bestaudio/best",
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "noplaylist": True,
            "skip_download": True,
            "geo_bypass": True,
        }

    @staticmethod
    def is_soundcloud_url(url: str) -> bool:
        return bool(SOUNDCLOUD_REGEX.match(url.strip()))

    def _extract(self, query: str) -> Optional[Dict[str, Any]]:
        query = query.strip()
        is_url = self.is_soundcloud_url(query)
        
        # If not a direct soundcloud URL, perform soundcloud search
        target = query if is_url else f"scsearch1:{query}"
        
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            try:
                info = ydl.extract_info(target, download=False)
                if not info:
                    return None
                
                # If search result, get first entry
                if "entries" in info:
                    entries = info.get("entries")
                    if not entries:
                        return None
                    info = entries[0]

                # Extract audio stream url
                stream_url = info.get("url")
                # Sometimes yt-dlp gives formats list
                if not stream_url and "formats" in info:
                    formats = [f for f in info["formats"] if f.get("acodec") != "none"]
                    if formats:
                        stream_url = formats[-1].get("url")

                # Best thumbnail
                thumbnail = info.get("thumbnail")
                if not thumbnail and "thumbnails" in info and info["thumbnails"]:
                    thumbnail = info["thumbnails"][-1].get("url")

                return {
                    "id": info.get("id"),
                    "title": info.get("title", "Unknown Title"),
                    "uploader": info.get("uploader") or info.get("artist") or "SoundCloud Artist",
                    "duration_sec": int(info.get("duration") or 0),
                    "url": info.get("webpage_url") or query,
                    "stream_url": stream_url,
                    "thumbnail": thumbnail,
                    "likes": info.get("like_count", 0),
                    "plays": info.get("view_count", 0),
                }
            except Exception as e:
                print(f"[SoundCloud Error] {e}")
                return None

    async def get_track(self, query: str) -> Optional[Dict[str, Any]]:
        return await asyncio.to_thread(self._extract, query)

# Global singleton
soundcloud = SoundCloudAPI()
