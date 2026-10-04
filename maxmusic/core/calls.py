import asyncio
import logging
from typing import Dict, Optional
from pytgcalls import PyTgCalls, types
try:
    from ntgcalls import ConnectionNotFound, TelegramServerError, RTMPStreamingUnsupported
except ImportError:
    class ConnectionNotFound(Exception): pass
    class TelegramServerError(Exception): pass
    class RTMPStreamingUnsupported(Exception): pass

from maxmusic.config import config
from maxmusic.core.database import db
from maxmusic.core.downloader import Track, downloader
from maxmusic.core.userbot import userbot
from maxmusic.helpers.queue import queue_mgr
from maxmusic.helpers.thumbnails import generate_thumbnail
from maxmusic.helpers.buttons import player_markup

logger = logging.getLogger(__name__)


class CallManager:
    def __init__(self):
        self.call_clients: Dict[int, PyTgCalls] = {}
        self.active_tracks: Dict[int, Track] = {}
        self.auto_leave_tasks: Dict[int, asyncio.Task] = {}
        self._bot = None

    def set_bot(self, bot):
        self._bot = bot

    async def boot(self):
        for idx, client in enumerate(userbot.clients, start=1):
            tg_call = PyTgCalls(client)
            self._register_handlers(tg_call)
            await tg_call.start()
            self.call_clients[idx] = tg_call
            logger.info(f"PyTgCalls initialized for Assistant {idx}")

    def get_call_instance(self, chat_id: int) -> PyTgCalls:
        asst = userbot.get_assistant(chat_id)
        return self.call_clients.get(asst.assistant_num, list(self.call_clients.values())[0])

    def _register_handlers(self, tg_call: PyTgCalls):
        @tg_call.on_update()
        async def _on_update(_, update: types.Update):
            if isinstance(update, (types.StreamEnded, getattr(types, "StreamAudioEnded", types.StreamEnded), getattr(types, "StreamVideoEnded", types.StreamEnded))):
                chat_id = getattr(update, "chat_id", None)
                if chat_id:
                    logger.info(f"Stream ended in chat {chat_id}")
                    await self.play_next(chat_id)
            elif isinstance(update, types.ChatUpdate):
                if getattr(update, "status", None) in (
                    getattr(types.ChatUpdate.Status, "KICKED", None),
                    getattr(types.ChatUpdate.Status, "LEFT_GROUP", None),
                    getattr(types.ChatUpdate.Status, "CLOSED_VOICE_CHAT", None),
                ):
                    chat_id = getattr(update, "chat_id", None)
                    if chat_id:
                        await self.stop(chat_id)

    async def play(self, chat_id: int, track: Track, video: bool = False) -> bool:
        tg_call = self.get_call_instance(chat_id)

        # Cancel any pending auto-leave timer
        if chat_id in self.auto_leave_tasks:
            self.auto_leave_tasks[chat_id].cancel()
            self.auto_leave_tasks.pop(chat_id, None)

        # Resolve media file
        file_path = await downloader.download(track)
        if not file_path:
            logger.error(f"Failed to prepare media file for track: {track.title}")
            return False

        audio_params = types.AudioQuality.HIGH
        if video or track.stream_type == "video":
            stream = types.MediaStream(
                file_path,
                audio_parameters=audio_params,
                video_parameters=types.VideoQuality.HD_720p,
            )
        else:
            stream = types.MediaStream(
                file_path,
                audio_parameters=audio_params,
            )

        try:
            if db.is_call_active(chat_id):
                await tg_call.change_stream(chat_id, stream)
            else:
                await tg_call.play(chat_id, stream)
                db.set_call_active(chat_id, {"active": True, "paused": False, "video": video})

            self.active_tracks[chat_id] = track
            queue_mgr.set_current(chat_id, track)
            await self._send_now_playing(chat_id, track)
            return True

        except (ConnectionNotFound, TelegramServerError) as e:
            logger.error(f"PyTgCalls connection error in {chat_id}: {e}")
            await self.stop(chat_id)
            return False
        except Exception as e:
            logger.error(f"Unexpected play error in {chat_id}: {e}")
            return False

    async def play_next(self, chat_id: int):
        next_track = queue_mgr.pop_next(chat_id)

        # If queue has next track
        if next_track:
            success = await self.play(chat_id, next_track, video=(next_track.stream_type == "video"))
            if not success:
                await self.play_next(chat_id)
            return

        # Queue empty, check autoplay
        if queue_mgr.is_autoplay(chat_id) and chat_id in self.active_tracks:
            last = self.active_tracks[chat_id]
            auto_track = await downloader.get_autoplay_track(last.title, last.video_id)
            if auto_track:
                logger.info(f"Autoplay triggered in {chat_id}: {auto_track.title}")
                await self.play(chat_id, auto_track, video=False)
                return

        # Nothing left to play, start auto-leave
        await self._schedule_auto_leave(chat_id)

    async def _send_now_playing(self, chat_id: int, track: Track):
        if not self._bot:
            return
        try:
            thumb_path = await generate_thumbnail(track)
            caption = (
                f"🎵 <b>Now Playing</b>\n\n"
                f"📌 <b>Title:</b> <a href=\"{track.url}\">{track.title}</a>\n"
                f"⏱ <b>Duration:</b> {track.duration}\n"
                f"👤 <b>Requested By:</b> {track.requester}\n"
            )
            markup = player_markup(chat_id, is_paused=False)
            if thumb_path and os.path.exists(thumb_path):
                await self._bot.send_photo(chat_id, photo=thumb_path, caption=caption, reply_markup=markup)
            else:
                await self._bot.send_message(chat_id, text=caption, reply_markup=markup, disable_web_page_preview=True)
        except Exception as e:
            logger.warning(f"Could not send now playing card: {e}")

    async def pause(self, chat_id: int) -> bool:
        tg_call = self.get_call_instance(chat_id)
        try:
            await tg_call.pause(chat_id)
            db.set_call_active(chat_id, {"active": True, "paused": True})
            return True
        except Exception as e:
            logger.warning(f"Pause error in {chat_id}: {e}")
            return False

    async def resume(self, chat_id: int) -> bool:
        tg_call = self.get_call_instance(chat_id)
        try:
            await tg_call.resume(chat_id)
            db.set_call_active(chat_id, {"active": True, "paused": False})
            return True
        except Exception as e:
            logger.warning(f"Resume error in {chat_id}: {e}")
            return False

    async def stop(self, chat_id: int) -> bool:
        tg_call = self.get_call_instance(chat_id)
        queue_mgr.clear(chat_id)
        db.remove_call_active(chat_id)
        self.active_tracks.pop(chat_id, None)

        if chat_id in self.auto_leave_tasks:
            self.auto_leave_tasks[chat_id].cancel()
            self.auto_leave_tasks.pop(chat_id, None)

        try:
            await tg_call.leave_call(chat_id)
            return True
        except Exception:
            return False

    async def seek(self, chat_id: int, offset_seconds: int) -> bool:
        tg_call = self.get_call_instance(chat_id)
        try:
            await tg_call.seek(chat_id, offset_seconds)
            return True
        except Exception as e:
            logger.warning(f"Seek error in {chat_id}: {e}")
            return False

    async def set_volume(self, chat_id: int, volume: int) -> bool:
        tg_call = self.get_call_instance(chat_id)
        try:
            await tg_call.change_volume_call(chat_id, volume)
            return True
        except Exception as e:
            logger.warning(f"Change volume error in {chat_id}: {e}")
            return False

    async def mute(self, chat_id: int) -> bool:
        tg_call = self.get_call_instance(chat_id)
        try:
            await tg_call.mute(chat_id)
            return True
        except Exception:
            return False

    async def unmute(self, chat_id: int) -> bool:
        tg_call = self.get_call_instance(chat_id)
        try:
            await tg_call.unmute(chat_id)
            return True
        except Exception:
            return False

    async def _schedule_auto_leave(self, chat_id: int):
        async def _leave_task():
            await asyncio.sleep(config.AUTO_LEAVE_TIME)
            logger.info(f"Auto-leave triggered for idle chat {chat_id}")
            await self.stop(chat_id)
            if self._bot:
                try:
                    await self._bot.send_message(
                        chat_id,
                        f"👋 Assistant left voice chat due to {config.AUTO_LEAVE_TIME // 60}m inactivity."
                    )
                except Exception:
                    pass

        self.auto_leave_tasks[chat_id] = asyncio.create_task(_leave_task())


calls = CallManager()
