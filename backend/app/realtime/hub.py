"""In-process pub/sub, one channel per team. Fits a single backend instance; with several,
publish through Postgres LISTEN/NOTIFY or Redis and keep this as the local fan-out.

publish() is thread-safe: sync route handlers run in a worker pool, each subscriber
lives on its own event loop, so messages are handed over with call_soon_threadsafe.
"""
import asyncio
import json
import threading
from collections import defaultdict
from typing import Any

QUEUE_MAX = 256


class Subscriber:
    def __init__(self, team_id: str) -> None:
        self.team_id = team_id
        self.loop = asyncio.get_running_loop()
        self.queue: asyncio.Queue[str] = asyncio.Queue(QUEUE_MAX)
        self.overflow = asyncio.Event()  # too slow: the socket is closed and the client resyncs

    def offer(self, text: str) -> None:
        try:
            self.queue.put_nowait(text)
        except asyncio.QueueFull:
            self.overflow.set()


class Hub:
    def __init__(self) -> None:
        self._subs: dict[str, set[Subscriber]] = defaultdict(set)
        self._lock = threading.Lock()

    def subscribe(self, team_id: str) -> Subscriber:
        sub = Subscriber(team_id)
        with self._lock:
            self._subs[team_id].add(sub)
        return sub

    def unsubscribe(self, sub: Subscriber) -> None:
        with self._lock:
            self._subs[sub.team_id].discard(sub)

    def publish(self, team_id: str, message: dict[str, Any]) -> None:
        text = json.dumps(message, default=str)
        with self._lock:
            subs = list(self._subs[team_id])
        for sub in subs:
            try:
                sub.loop.call_soon_threadsafe(sub.offer, text)
            except RuntimeError:  # its loop is gone
                self.unsubscribe(sub)


hub = Hub()
