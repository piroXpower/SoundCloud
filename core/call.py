import os
import asyncio
from typing import Dict, Any, Optional
from pyrogram.types import InputMediaPhoto

from core.assistant import userbot
from core.bot import app
from utils.queue import queue_mgr
from utils.inline import player_keyboard
from utils.thumbnail import thumbnail_gen
from utils.formatters import format_duration, clean_html

# Import PyTgCalls with multi-version fallback
try:
    from pytgcalls import PyTgCalls
    from pytgcalls.types import MediaStream, AudioQuality
    MODERN_PYTGCALLS = True
except ImportError:
    try:
        from pytgcalls import PyTgCalls
        from pytgcalls.types.input_stream import AudioPiped
        from pytgcalls.types.input_stream.quality import HighQualityAudio
        MODERN_PYTGCALLS = False
    except ImportError:
        PyTgCalls = None
        MODERN_PYTGCALLS = False

class SoundCloudCallManager:
    def __init__(self):
        self.call: Optional[PyTgCalls] = None
        if PyTgCalls and userbot:
            try:
                self.call = PyTgCalls(userbot)
            except Exception as e:
                print(f"[PyTgCalls Init Error] {e}")

    async def start(self):
        if self.call:
            await self.call.start()
            self._register_handlers()
            print("🔊 [PyTgCalls]: Voice Call Client Active")

    def _get_stream(self, stream_url: str):
        if MODERN_PYTGCALLS:
            return MediaStream(
                media_path=stream_url,
                audio_parameters=AudioQuality.HIGH,
                video_flags=MediaStream.Flags.IGNORE,
            )
        else:
            return AudioPiped(stream_url)

    async def play_or_change(self, chat_id: int, stream_url: str):
        stream = self._get_stream(stream_url)
        try:
            # Try to play (joins call if not joined)
            if MODERN_PYTGCALLS:
                await self.call.play(chat_id, stream)
            else:
                await self.call.join_group_call(chat_id, stream)
        except Exception:
            # If already joined in group call, change stream
            try:
                if MODERN_PYTGCALLS:
                    await self.call.play(chat_id, stream)
                else:
                    await self.call.change_stream(chat_id, stream)
            except Exception as e:
                print(f"[Play Error {chat_id}]: {e}")
                raise e

    async def pause(self, chat_id: int):
        if MODERN_PYTGCALLS:
            await self.call.pause(chat_id)
        else:
            await self.call.pause_stream(chat_id)
        queue_mgr.set_paused(chat_id, True)

    async def resume(self, chat_id: int):
        if MODERN_PYTGCALLS:
            await self.call.resume(chat_id)
        else:
            await self.call.resume_stream(chat_id)
        queue_mgr.set_paused(chat_id, False)

    async def stop(self, chat_id: int):
        queue_mgr.clear(chat_id)
        try:
            if MODERN_PYTGCALLS:
                await self.call.leave_call(chat_id)
            else:
                await self.call.leave_group_call(chat_id)
        except Exception as e:
            print(f"[Stop/Leave Error {chat_id}]: {e}")

    async def mute(self, chat_id: int):
        if MODERN_PYTGCALLS:
            await self.call.mute(chat_id)
        else:
            await self.call.mute_stream(chat_id)

    async def unmute(self, chat_id: int):
        if MODERN_PYTGCALLS:
            await self.call.unmute(chat_id)
        else:
            await self.call.unmute_stream(chat_id)

    async def set_volume(self, chat_id: int, volume: int):
        volume = max(1, min(200, volume))
        if MODERN_PYTGCALLS:
            await self.call.change_volume_call(chat_id, volume)
        else:
            await self.call.change_volume_call(chat_id, volume)
        queue_mgr.set_volume(chat_id, volume)

    def _register_handlers(self):
        if not self.call:
            return

        try:
            from pytgcalls.types import StreamEnded
            @self.call.on_update()
            async def stream_update_handler(client, update):
                if isinstance(update, StreamEnded):
                    await self._on_stream_end(update.chat_id)
        except Exception:
            # Older pytgcalls decorators
            try:
                @self.call.on_stream_end()
                async def old_stream_end_handler(client, update):
                    chat_id = update.chat_id if hasattr(update, "chat_id") else update
                    await self._on_stream_end(chat_id)
            except Exception as e:
                print(f"[PyTgCalls Handler Register Warning] {e}")

    async def _on_stream_end(self, chat_id: int):
        """Called automatically when current track ends."""
        next_track = queue_mgr.pop_next(chat_id)
        if not next_track:
            await self.stop(chat_id)
            try:
                await app.send_message(
                    chat_id=chat_id,
                    text="✨ **SoundCloud Queue Finished!**\nNo more tracks left in queue. Leaving voice chat.",
                )
            except Exception:
                pass
            return

        # Play next track
        try:
            await self.play_or_change(chat_id, next_track["stream_url"])
            
            # Generate awesome thumbnail
            thumb_path = await thumbnail_gen.create_thumbnail(
                cover_url=next_track.get("thumbnail"),
                title=next_track.get("title", "Unknown"),
                artist=next_track.get("uploader", "SoundCloud Artist"),
                duration_sec=next_track.get("duration_sec", 0),
                track_id=str(next_track.get("id", "track")),
            )

            # Attractive Now Playing Service Message
            duration = format_duration(next_track.get("duration_sec", 0))
            caption = (
                f"☁️ <b>Now Streaming on SoundCloud:</b>\n"
                f"🎵 <b>Title:</b> <code>{clean_html(next_track['title'])}</code>\n"
                f"👤 <b>Artist:</b> <code>{clean_html(next_track['uploader'])}</code>\n"
                f"⏱ <b>Duration:</b> <code>{duration}</code>\n"
                f"🎧 <b>Requested by:</b> {next_track.get('requester_mention', 'Listener')}\n\n"
                f"<blockquote>⚡ <i>Pure Hi-Res Audio streamed directly via PyTgCalls</i></blockquote>"
            )

            keyboard = player_keyboard(
                chat_id=chat_id,
                is_paused=False,
                loop_mode=queue_mgr.get_loop(chat_id),
                sc_url=next_track.get("url", ""),
            )

            if os.path.exists(thumb_path):
                await app.send_photo(
                    chat_id=chat_id,
                    photo=thumb_path,
                    caption=caption,
                    reply_markup=keyboard,
                )
            else:
                await app.send_message(
                    chat_id=chat_id,
                    text=caption,
                    reply_markup=keyboard,
                )
        except Exception as e:
            print(f"[Stream End Handler Error]: {e}")
            await self._on_stream_end(chat_id)

call_manager = SoundCloudCallManager()
