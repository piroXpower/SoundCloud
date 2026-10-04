import random
from typing import Dict, List, Optional
from maxmusic.core.downloader import Track
from maxmusic.config import config


class QueueManager:
    def __init__(self):
        # chat_id -> list of Track objects
        self._queues: Dict[int, List[Track]] = {}
        # chat_id -> current playing Track
        self._current: Dict[int, Track] = {}
        # chat_id -> loop mode: 0 = Off, 1 = Current Track, 2 = Queue
        self._loop: Dict[int, int] = {}
        # chat_id -> bool
        self._autoplay: Dict[int, bool] = {}

    def get_queue(self, chat_id: int) -> List[Track]:
        return list(self._queues.get(chat_id, []))

    def current(self, chat_id: int) -> Optional[Track]:
        return self._current.get(chat_id)

    def set_current(self, chat_id: int, track: Optional[Track]):
        if track:
            self._current[chat_id] = track
        else:
            self._current.pop(chat_id, None)

    def add(self, chat_id: int, track: Track) -> int:
        if chat_id not in self._queues:
            self._queues[chat_id] = []
        if len(self._queues[chat_id]) >= config.QUEUE_LIMIT:
            return -1
        self._queues[chat_id].append(track)
        return len(self._queues[chat_id])

    def force_add(self, chat_id: int, track: Track):
        if chat_id not in self._queues:
            self._queues[chat_id] = []
        self._queues[chat_id].insert(0, track)

    def pop_next(self, chat_id: int) -> Optional[Track]:
        loop_mode = self.get_loop(chat_id)
        current_track = self._current.get(chat_id)

        # Mode 1: Repeat Single Track
        if loop_mode == 1 and current_track:
            return current_track

        # Mode 2: Repeat Queue
        if loop_mode == 2 and current_track:
            if chat_id not in self._queues:
                self._queues[chat_id] = []
            self._queues[chat_id].append(current_track)

        queue = self._queues.get(chat_id, [])
        if not queue:
            self._current.pop(chat_id, None)
            return None

        next_track = queue.pop(0)
        self._current[chat_id] = next_track
        return next_track

    def clear(self, chat_id: int):
        self._queues.pop(chat_id, None)
        self._current.pop(chat_id, None)
        self._loop.pop(chat_id, None)

    def shuffle(self, chat_id: int) -> bool:
        queue = self._queues.get(chat_id, [])
        if len(queue) <= 1:
            return False
        random.shuffle(queue)
        self._queues[chat_id] = queue
        return True

    def get_loop(self, chat_id: int) -> int:
        return self._loop.get(chat_id, 0)

    def set_loop(self, chat_id: int, mode: int):
        self._loop[chat_id] = mode

    def is_autoplay(self, chat_id: int) -> bool:
        return self._autoplay.get(chat_id, True)

    def set_autoplay(self, chat_id: int, enable: bool):
        self._autoplay[chat_id] = enable


queue_mgr = QueueManager()
