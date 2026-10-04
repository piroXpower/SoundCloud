import asyncio
import logging
import os
import re
import time
from dataclasses import dataclass
from typing import List, Optional
import yt_dlp
from py_yt import VideosSearch, Playlist

from maxmusic.config import config

logger = logging.getLogger(__name__)

DOWNLOAD_DIR = "downloads"
CACHE_DIR = "cache"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)


@dataclass
class Track:
    title: str
    duration: str
    duration_sec: int
    url: str
    video_id: str
    thumbnail: str
    requester: str
    stream_type: str = "audio"  # "audio" or "video"
    file_path: Optional[str] = None
    message_id: Optional[int] = None
    chat_id: Optional[int] = None


def time_to_seconds(time_str: str) -> int:
    if not time_str:
        return 0
    try:
        parts = list(map(int, str(time_str).split(":")))
        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
        if len(parts) == 1:
            return parts[0]
    except Exception:
        return 0
    return 0


def seconds_to_time(seconds: int) -> str:
    seconds = int(seconds or 0)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def extract_video_id(query: str) -> str | None:
    if not query:
        return None
    query = str(query).strip()
    if "youtu.be/" in query:
        return query.split("youtu.be/", 1)[1].split("?", 1)[0].split("&", 1)[0]
    if "v=" in query:
        return query.split("v=", 1)[1].split("&", 1)[0]
    if len(query) == 11 and re.match(r"^[a-zA-Z0-9_-]{11}$", query):
        return query
    return None


class Downloader:
    def __init__(self):
        self.download_dir = DOWNLOAD_DIR
        self.cookies_file = config.YOUTUBE_COOKIES_FILE

    def _get_ydl_opts(self, stream_type: str = "audio", out_path: str = "") -> dict:
        opts = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "retries": 3,
            "socket_timeout": 30,
            "geo_bypass": True,
            "nocheckcertificate": True,
            "outtmpl": out_path or os.path.join(self.download_dir, "%(id)s.%(ext)s"),
        }
        if os.path.exists(self.cookies_file):
            opts["cookiefile"] = self.cookies_file

        if stream_type == "video":
            opts.update({
                "format": "best[ext=mp4][height<=720]/best[height<=720]/best",
                "merge_output_format": "mp4",
            })
        else:
            opts.update({
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            })
        return opts

    async def search(self, query: str, requester: str = "", video: bool = False) -> Track | None:
        video_id = extract_video_id(query)
        if video_id:
            query = f"https://www.youtube.com/watch?v={video_id}"

        def _search():
            try:
                search = VideosSearch(query, limit=1)
                res = search.result()
                if not res or not res.get("result"):
                    return None
                item = res["result"][0]
                dur_str = item.get("duration", "0:00")
                return Track(
                    title=item.get("title", "Unknown Title"),
                    duration=dur_str,
                    duration_sec=time_to_seconds(dur_str),
                    url=item.get("link", ""),
                    video_id=item.get("id", ""),
                    thumbnail=item.get("thumbnails", [{}])[0].get("url", config.DEFAULT_THUMB),
                    requester=requester,
                    stream_type="video" if video else "audio",
                )
            except Exception as e:
                logger.error(f"Search failed for '{query}': {e}")
                return None

        return await asyncio.to_thread(_search)

    async def playlist(self, url: str, limit: int, requester: str = "", video: bool = False) -> List[Track]:
        def _get_playlist():
            tracks: List[Track] = []
            try:
                plist = Playlist(url)
                videos = plist.videos or []
                for item in videos[:limit]:
                    dur_str = item.get("duration", "0:00")
                    tracks.append(
                        Track(
                            title=item.get("title", "Unknown Title"),
                            duration=dur_str,
                            duration_sec=time_to_seconds(dur_str),
                            url=item.get("link", ""),
                            video_id=item.get("id", ""),
                            thumbnail=item.get("thumbnails", [{}])[0].get("url", config.DEFAULT_THUMB),
                            requester=requester,
                            stream_type="video" if video else "audio",
                        )
                    )
            except Exception as e:
                logger.error(f"Playlist extraction failed for '{url}': {e}")
            return tracks

        return await asyncio.to_thread(_get_playlist)

    async def download(self, track: Track) -> str | None:
        if track.file_path and os.path.exists(track.file_path):
            return track.file_path

        ext = "mp4" if track.stream_type == "video" else "mp3"
        target_file = os.path.join(self.download_dir, f"{track.video_id}.{ext}")

        if os.path.exists(target_file) and os.path.getsize(target_file) > 1024:
            track.file_path = target_file
            return target_file

        def _do_download():
            opts = self._get_ydl_opts(track.stream_type, target_file)
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([track.url])
                if os.path.exists(target_file):
                    return target_file
                # Check with possible extension
                for f in os.listdir(self.download_dir):
                    if f.startswith(track.video_id) and not f.endswith(".part"):
                        return os.path.join(self.download_dir, f)
            except Exception as e:
                logger.error(f"yt-dlp download error for {track.url}: {e}")
            return None

        file_path = await asyncio.to_thread(_do_download)
        track.file_path = file_path
        return file_path

    async def get_stream_url(self, track: Track) -> str | None:
        """Extract direct audio/video streaming URL when direct piping is desired."""
        def _extract():
            opts = {
                "quiet": True,
                "no_warnings": True,
                "format": "bestaudio/best" if track.stream_type == "audio" else "best[ext=mp4][height<=720]/best",
                "noplaylist": True,
            }
            if os.path.exists(self.cookies_file):
                opts["cookiefile"] = self.cookies_file
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(track.url, download=False)
                    return info.get("url")
            except Exception as e:
                logger.warning(f"Could not extract direct stream URL for {track.url}: {e}")
                return None

        return await asyncio.to_thread(_extract)

    async def get_autoplay_track(self, current_title: str, current_id: str, requester: str = "Autoplay") -> Track | None:
        """Discover next related track for autoplay."""
        clean_title = re.sub(r"[\(\[].*?[\)\]]", "", current_title).strip()
        search_query = f"{clean_title} songs"

        def _suggest():
            try:
                search = VideosSearch(search_query, limit=10)
                res = search.result()
                if not res or not res.get("result"):
                    return None
                for item in res["result"]:
                    vid = item.get("id")
                    if vid and vid != current_id:
                        dur_str = item.get("duration", "0:00")
                        return Track(
                            title=item.get("title", "Autoplay Song"),
                            duration=dur_str,
                            duration_sec=time_to_seconds(dur_str),
                            url=item.get("link", ""),
                            video_id=vid,
                            thumbnail=item.get("thumbnails", [{}])[0].get("url", config.DEFAULT_THUMB),
                            requester=requester,
                            stream_type="audio",
                        )
            except Exception as e:
                logger.error(f"Autoplay query failed: {e}")
            return None

        return await asyncio.to_thread(_suggest)

    def cleanup_cache(self, max_age_seconds: int = 1800):
        """Purge older downloaded media to avoid filling up disk."""
        now = time.time()
        for folder in [self.download_dir, CACHE_DIR]:
            if not os.path.exists(folder):
                continue
            for fname in os.listdir(folder):
                fpath = os.path.join(folder, fname)
                try:
                    if os.path.isfile(fpath) and (now - os.path.getmtime(fpath) > max_age_seconds):
                        os.remove(fpath)
                except OSError:
                    pass


downloader = Downloader()
