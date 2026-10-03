from typing import Dict, List, Optional, Any

class QueueManager:
    def __init__(self):
        # chat_id -> list of track dicts
        self._queues: Dict[int, List[Dict[str, Any]]] = {}
        # chat_id -> current playing track dict
        self._current: Dict[int, Dict[str, Any]] = {}
        # chat_id -> "none" | "track" | "queue"
        self._loop: Dict[int, str] = {}
        # chat_id -> volume level (0-200)
        self._volume: Dict[int, int] = {}
        # chat_id -> is_paused (bool)
        self._paused: Dict[int, bool] = {}
        # chat_id -> list of recently played tracks
        self._history: Dict[int, List[Dict[str, Any]]] = {}

    def get_queue(self, chat_id: int) -> List[Dict[str, Any]]:
        return self._queues.setdefault(chat_id, [])

    def add_history(self, chat_id: int, track: Dict[str, Any]):
        hist = self._history.setdefault(chat_id, [])
        # Avoid duplicate consecutive
        if not hist or hist[-1].get("url") != track.get("url"):
            hist.append(track)
            if len(hist) > 15:
                hist.pop(0)

    def get_history(self, chat_id: int) -> List[Dict[str, Any]]:
        return list(reversed(self._history.get(chat_id, [])))

    def add(self, chat_id: int, track: Dict[str, Any]) -> int:
        """Add a track to the queue and return its 1-indexed position."""
        q = self.get_queue(chat_id)
        q.append(track)
        return len(q)

    def set_current(self, chat_id: int, track: Optional[Dict[str, Any]]):
        if track:
            self._current[chat_id] = track
            self.add_history(chat_id, track)
        else:
            self._current.pop(chat_id, None)

    def get_current(self, chat_id: int) -> Optional[Dict[str, Any]]:
        return self._current.get(chat_id)

    def pop_next(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """Pops next track respecting loop configuration."""
        loop = self._loop.get(chat_id, "none")
        curr = self._current.get(chat_id)

        # Loop single track
        if loop == "track" and curr:
            return curr

        q = self.get_queue(chat_id)
        if not q:
            self.set_current(chat_id, None)
            return None

        # Loop entire queue: push played track to end
        if loop == "queue" and curr:
            q.append(curr)

        next_track = q.pop(0)
        self.set_current(chat_id, next_track)
        return next_track

    def clear(self, chat_id: int):
        self._queues[chat_id] = []
        self._current.pop(chat_id, None)
        self._loop[chat_id] = "none"
        self._paused[chat_id] = False

    def remove(self, chat_id: int, index: int) -> Optional[Dict[str, Any]]:
        q = self.get_queue(chat_id)
        if 0 <= index < len(q):
            return q.pop(index)
        return None

    def toggle_loop(self, chat_id: int) -> str:
        current_mode = self._loop.get(chat_id, "none")
        if current_mode == "none":
            new_mode = "track"
        elif current_mode == "track":
            new_mode = "queue"
        else:
            new_mode = "none"
        self._loop[chat_id] = new_mode
        return new_mode

    def get_loop(self, chat_id: int) -> str:
        return self._loop.get(chat_id, "none")

    def set_volume(self, chat_id: int, vol: int):
        self._volume[chat_id] = vol

    def get_volume(self, chat_id: int) -> int:
        return self._volume.get(chat_id, 100)

    def set_paused(self, chat_id: int, paused: bool):
        self._paused[chat_id] = paused

    def is_paused(self, chat_id: int) -> bool:
        return self._paused.get(chat_id, False)

queue_mgr = QueueManager()
