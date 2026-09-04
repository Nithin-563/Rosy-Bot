"""Music player — play/pause/resume/skip/stop/queue/volume/loop/now-playing.

Uses discord.py's audio source API. Requires ffmpeg (system binary) and, for
YouTube playback, the optional `yt-dlp` extra. Playback is driven by the
Discord cog via the `play_source` callback, keeping this layer dependency-free.
"""
from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

log = logging.getLogger(__name__)


@dataclass
class Track:
    title: str
    url: str
    requested_by: int
    duration_seconds: Optional[int] = None
    source: str = "local"


@dataclass
class PlayerState:
    is_playing: bool = False
    is_paused: bool = False
    loop: bool = False
    volume: float = 1.0
    queue: deque[Track] = field(default_factory=deque)
    current: Optional[Track] = None


class MusicPlayer:
    """Per-guild music queue and transport control."""

    def __init__(self) -> None:
        self._states: dict[int, PlayerState] = {}

    def state(self, guild_id: int) -> PlayerState:
        return self._states.setdefault(guild_id, PlayerState())

    def enqueue(self, guild_id: int, track: Track) -> int:
        st = self.state(guild_id)
        st.queue.append(track)
        return len(st.queue)

    def next(self, guild_id: int) -> Optional[Track]:
        st = self.state(guild_id)
        if st.loop and st.current is not None:
            return st.current
        if st.queue:
            st.current = st.queue.popleft()
            return st.current
        st.current = None
        return None

    def now(self, guild_id: int) -> Optional[Track]:
        return self.state(guild_id).current

    def clear(self, guild_id: int) -> int:
        st = self.state(guild_id)
        n = len(st.queue)
        st.queue.clear()
        return n

    def queue_length(self, guild_id: int) -> int:
        return len(self.state(guild_id).queue)

    def set_volume(self, guild_id: int, volume: float) -> float:
        st = self.state(guild_id)
        st.volume = max(0.0, min(volume, 2.0))
        return st.volume

    def set_loop(self, guild_id: int, enabled: bool) -> bool:
        st = self.state(guild_id)
        st.loop = enabled
        return st.loop

    def mark_playing(self, guild_id: int, playing: bool, paused: bool = False) -> None:
        st = self.state(guild_id)
        st.is_playing = playing
        st.is_paused = paused
