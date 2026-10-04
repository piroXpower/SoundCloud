import asyncio
import itertools
import os
import re
import time
from dataclasses import dataclass
from typing import List, Optional, Union
import aiohttp
import yt_dlp
from py_yt import VideosSearch, Playlist

from maxmusic.config import config

logger = logging.getLogger(__name__)

DOWNLOAD_DIR = "downloads"
CACHE_DIR = "cache"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

API_URL = os.environ.get(
    "SHRUTI_API_URL",
    "https://api.shrutibots.site",
)

# Pool of API keys
API_KEYS = [
    "ShrutiBotsJhHL3aUrpEitMoWFoO6a",
    "ShrutiBotsvDVzZ8JpGhZFFpYNLJ6a", 
    "ShrutiBotsD7fjwbowNar0bBQLeLQM", 
    "ShrutiBots0Go885F57juetyNYFS15", 
    "ShrutiBotstXsAgTyYe5Ud66aQYEwU",
    "ShrutiBotsUCNTR8rAnLswvyVLXI7v",
]

ACTIVE_API_KEYS = [k for k in API_KEYS if k]
_api_key_cycle = itertools.cycle(ACTIVE_API_KEYS) if ACTIVE_API_KEYS else None


def get_next_api_key() -> str | None:
    """Rotate and return the next API key in round-robin order."""
    if not _api_key_cycle:
        return None
    return next(_api_key_cycle)


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
    id: Optional[str] = None
    video: bool = False
    channel_name: Optional[str] = None
    user: Optional[str] = None


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
    return query if len(query) >= 3 else None


async def _api_download(link: str, media_type: str, timeout: int) -> str | None:
    """Download media from the configured API with key rotation and retries."""
    video_id = extract_video_id(link)
    if not video_id:
        return None

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    ext = "mp4" if media_type == "video" else "mp3"
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.{ext}")

    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return file_path

    current_key = get_next_api_key()
    params = {"url": video_id, "type": media_type}
    if current_key:
        params["api_key"] = current_key

    client_timeout = aiohttp.ClientTimeout(
        total=timeout,
        connect=4,
        sock_connect=4,
        sock_read=90,
    )

    for attempt in range(3):
        try:
            async with aiohttp.ClientSession(timeout=client_timeout) as session:
                async with session.get(
                    f"{API_URL.rstrip('/')}/download",
                    params=params,
                    headers={"User-Agent": "Mozilla/5.0"},
                ) as resp:
                    if resp.status != 200:
                        logger.warning(
                            "Download API returned HTTP %s for %s (attempt %s/3)",
                            resp.status,
                            video_id,
                            attempt + 1,
                        )
                        if resp.status not in (408, 429) and resp.status < 500:
                            break
                    else:
                        ctype = (resp.headers.get("Content-Type") or "").lower()
                        if "application/json" in ctype or "text/html" in ctype:
                            logger.warning(
                                "Download API returned %s instead of media for %s",
                                ctype,
                                video_id,
                            )
                        else:
                            tmp_path = f"{file_path}.part"
                            try:
                                with open(tmp_path, "wb") as output:
                                    async for chunk in resp.content.iter_chunked(1024 * 1024):
                                        if chunk:
                                            output.write(chunk)

                                if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
                                    os.replace(tmp_path, file_path)
                                    return file_path
                            finally:
                                try:
                                    if os.path.exists(tmp_path):
                                        os.remove(tmp_path)
                                except OSError:
                                    pass

        except Exception as exc:
            logger.warning("Download API failed for %s (attempt %s/3): %s", video_id, attempt + 1, exc)

        if attempt < 2:
            current_key = get_next_api_key()
            if current_key:
                params["api_key"] = current_key
            await asyncio.sleep(0.2)

    return None


async def _ytdlp_download(link: str, media_type: str) -> str | None:
    """Fallback downloader using yt-dlp."""
    video_id = extract_video_id(link)
    if not video_id:
        return None

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    output_template = os.path.join(DOWNLOAD_DIR, f"{video_id}.%(ext)s")

    def _download() -> str | None:
        opts = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "retries": 2,
            "socket_timeout": 20,
            "geo_bypass": True,
            "nocheckcertificate": True,
            "outtmpl": output_template,
        }
        if media_type == "video":
            opts.update({
                "format": "best[ext=mp4]/best",
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

        if os.path.exists(config.YOUTUBE_COOKIES_FILE):
            opts["cookiefile"] = config.YOUTUBE_COOKIES_FILE

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([link])
        except Exception as exc:
            logger.warning("yt-dlp fallback failed for %s: %s", video_id, exc)
            return None

        prefix = os.path.join(DOWNLOAD_DIR, f"{video_id}.")
        candidates = [
            path for path in (
                os.path.join(DOWNLOAD_DIR, name)
                for name in os.listdir(DOWNLOAD_DIR)
            )
            if path.startswith(prefix)
            and not path.endswith(".part")
            and os.path.isfile(path)
            and os.path.getsize(path) > 0
        ]
        if not candidates:
            return None
        return max(candidates, key=os.path.getmtime)

    return await asyncio.to_thread(_download)


async def download_song(link: str) -> str | None:
    file_path = await _api_download(link, "audio", 60)
    if file_path:
        return file_path
    return await _ytdlp_download(link, "audio")


async def download_video(link: str) -> str | None:
    file_path = await _api_download(link, "video", 90)
    if file_path:
        return file_path
    return await _ytdlp_download(link, "video")


class YouTubeAPI:
    def __init__(self):
        self.download_dir = DOWNLOAD_DIR
        self.cookies_file = config.YOUTUBE_COOKIES_FILE
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.listbase = "https://youtube.com/playlist?list="

    async def search(self, query: str, requester: str = "", video: bool = False, message_id: int = 0) -> Track | None:
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
                vid = item.get("id", "")
                thumbnails = item.get("thumbnails", [{}])
                thumbnail = thumbnails[0].get("url", config.DEFAULT_THUMB).split("?")[0] if thumbnails else config.DEFAULT_THUMB
                
                return Track(
                    title=item.get("title", "Unknown Title"),
                    duration=dur_str,
                    duration_sec=time_to_seconds(dur_str),
                    url=item.get("link", f"https://www.youtube.com/watch?v={vid}"),
                    video_id=vid,
                    thumbnail=thumbnail,
                    requester=requester,
                    stream_type="video" if video else "audio",
                    id=vid,
                    video=video,
                    channel_name=(item.get("channel") or {}).get("name"),
                    message_id=message_id,
                )
            except Exception as e:
                logger.error(f"Search failed for '{query}': {e}")
                return None

        return await asyncio.to_thread(_search)

    async def playlist(self, url: str, limit: int, requester: str = "", video: bool = False, videoid: Union[bool, str] = None, user_id=None) -> List[Track] | List[str]:
        if videoid:
            url = self.listbase + url
        url = url.split("&")[0]

        def _get_playlist():
            tracks: List[Track] = []
            try:
                plist = Playlist(url)
                videos = plist.videos or []
                for item in videos[:limit]:
                    dur_str = item.get("duration", "0:00")
                    vid = item.get("id", "")
                    thumbnails = item.get("thumbnails", [{}])
                    thumbnail = thumbnails[0].get("url", config.DEFAULT_THUMB).split("?")[0] if thumbnails else config.DEFAULT_THUMB
                    tracks.append(
                        Track(
                            title=item.get("title", "Unknown Title"),
                            duration=dur_str,
                            duration_sec=time_to_seconds(dur_str),
                            url=item.get("link", f"https://www.youtube.com/watch?v={vid}"),
                            video_id=vid,
                            thumbnail=thumbnail,
                            requester=requester,
                            stream_type="video" if video else "audio",
                            id=vid,
                            video=video,
                        )
                    )
            except Exception as e:
                logger.error(f"Playlist extraction failed for '{url}': {e}")
            return tracks

        return await asyncio.to_thread(_get_playlist)

    async def download(self, link: str, mystic=None, video: Union[bool, str] = None, videoid: Union[bool, str] = None, **kwargs):
        if videoid:
            link = self.base + link

        try:
            file_path = await download_video(link) if video else await download_song(link)
            if file_path:
                return file_path, True
            return None, False
        except Exception as exc:
            logger.error("YouTube download error: %s", exc)
            return None, False

    async def get_stream_url(self, track: Track) -> str | None:
        video_id = extract_video_id(track.url or track.video_id)
        if not video_id:
            return None

        current_key = get_next_api_key()
        params = f"url={video_id}&type={track.stream_type}"
        if current_key:
            params += f"&api_key={current_key}"

        url = f"{API_URL.rstrip('/')}/download?{params}"
        if await self._url_has_media(url):
            return url
        return None

    @staticmethod
    async def _url_has_media(url: str) -> bool:
        try:
            timeout = aiohttp.ClientTimeout(total=15, connect=5)
            headers = {"User-Agent": "Mozilla/5.0"}
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as resp:
                    if resp.status >= 400:
                        return False
                    ctype = (resp.headers.get("Content-Type") or "").lower()
                    if "text/html" in ctype or "application/json" in ctype:
                        return False
                    return True
        except Exception as exc:
            logger.warning("stream_url validation failed for %s: %s", url, exc)
            return False

    async def autoplay_track(
        self,
        video_id: str,
        video: Union[bool, str] = None,
        exclude: set | None = None,
        title: str | None = None,
    ) -> Track | None:
        exclude = exclude or set()
        stop_words = {
            "official", "video", "audio", "lyric", "lyrics", "song", "songs", 
            "full", "status", "remix", "version", "original", "cover", "slowed", 
            "reverb", "title", "track", "hd", "4k", "8k", "mp3", "film", "movie"
        }

        clean_raw = re.sub(r"[\(\[\{\)\}\]\-_|/:]|feat\.|ft\.", " ", (title or "").lower())
        base_words = [w for w in clean_raw.split() if len(w) > 2 and w not in stop_words]
        clean_title_str = " ".join(base_words[:3]) if base_words else (title or "Bollywood")

        raw_candidates = []
        alt_queries = [
            f"songs like {clean_title_str}",
            "superhit romantic hindi songs",
            "best bollywood love songs evergreen",
            "90s 2000s hit bollywood songs"
        ]
        
        for q in alt_queries:
            if len(raw_candidates) >= 20:
                break
            try:
                vs = VideosSearch(q, limit=10)
                res = (await vs.next()).get("result", [])
                for item in res:
                    eid = item.get("id")
                    if eid and eid != video_id and eid not in exclude:
                        raw_candidates.append({
                            "id": eid,
                            "title": item.get("title"),
                            "duration": item.get("duration", "0:00"),
                            "channel": item.get("channel"),
                            "thumbnails": item.get("thumbnails"),
                            "link": item.get("link") or f"https://www.youtube.com/watch?v={eid}",
                        })
            except Exception:
                continue

        filtered_pool = []
        for entry in raw_candidates:
            if not entry:
                continue
            entry_id = entry.get("id")
            if not entry_id or entry_id == video_id or entry_id in exclude:
                continue
            
            entry_title = (entry.get("title") or "").strip()
            if not entry_title:
                continue
            
            entry_clean = re.sub(r"[\(\[\{\)\}\]\-_|/:]|feat\.|ft\.", " ", entry_title.lower())
            entry_words = [w for w in entry_clean.split() if len(w) > 2 and w not in stop_words]

            if base_words and entry_words:
                overlap = sum(1 for w in base_words if w in entry_words)
                if overlap >= 2 or (len(base_words) > 0 and (overlap / len(base_words)) >= 0.5):
                    continue
            
            filtered_pool.append(entry)

        if not filtered_pool:
            return None

        chosen = filtered_pool[0]
        dur_str = chosen.get("duration", "0:00")
        duration_sec = time_to_seconds(dur_str)
        thumbs = chosen.get("thumbnails") or []
        thumbnail = thumbs[-1].get("url", "").split("?")[0] if thumbs else config.DEFAULT_THUMB
        link = chosen.get("link") or f"https://www.youtube.com/watch?v={chosen.get('id')}"

        return Track(
            title=chosen.get("title", "Autoplay Song"),
            duration=dur_str,
            duration_sec=duration_sec,
            url=link,
            video_id=chosen.get("id"),
            thumbnail=thumbnail,
            requester="Autoplay",
            stream_type="video" if video else "audio",
            id=chosen.get("id"),
            video=bool(video),
            channel_name=(chosen.get("channel") or {}).get("name"),
            user="Autoplay",
        )

    def cleanup_cache(self, max_age_seconds: int = 1800):
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


YouTube = YouTubeAPI()
        
