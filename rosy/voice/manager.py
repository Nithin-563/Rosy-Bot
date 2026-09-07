"""Voice subsystem — join/leave/listen/speak with pluggable STT and TTS.

Optional dependencies (aiohttp etc.) are imported lazily; if unavailable, the
voice features degrade to a clear "voice support not installed" error instead
of crashing the bot.
"""
from __future__ import annotations

import logging
from typing import Awaitable, Callable, Optional

log = logging.getLogger(__name__)


class TTSProvider:
    name = "stub"

    async def synthesize(self, text: str, *, voice: str | None = None) -> bytes | None:
        """Return audio bytes, or None if this provider can't synthesize."""
        return None


class STTProvider:
    name = "stub"

    async def transcribe(self, audio_path: str, *, language: str | None = None) -> str:
        return ""


class VoiceManager:
    """Tracks voice client state and delegates STT/TTS to configured providers."""

    def __init__(self, tts: TTSProvider | None = None, stt: STTProvider | None = None) -> None:
        self.tts = tts or TTSProvider()
        self.stt = stt or STTProvider()
        self._clients: dict[int, object] = {}  # guild_id -> VoiceClient

    def track(self, guild_id: int, client: object) -> None:
        self._clients[guild_id] = client

    def untrack(self, guild_id: int) -> None:
        self._clients.pop(guild_id, None)

    def connected(self, guild_id: int) -> bool:
        return guild_id in self._clients

    async def speak(self, guild_id: int, text: str, *, voice: str | None = None) -> bool:
        audio = await self.tts.synthesize(text, voice=voice)
        if audio is None:
            log.warning("TTS provider %s returned no audio for guild %s", self.tts.name, guild_id)
            return False
        client = self._clients.get(guild_id)
        if client is None:
            return False
        try:
            # play_audio is provided by the wrapper in the cog layer.
            await client.play_audio(audio)  # type: ignore[attr-defined]
            return True
        except Exception:  # noqa: BLE001
            log.exception("Voice speak failed for guild %s", guild_id)
            return False


def make_default_tts() -> TTSProvider:
    try:
        import aiohttp  # noqa: F401
        # A concrete provider can be wired to any HTTP TTS API; the default is a
        # stub so the bot runs without external voice credentials.
        return TTSProvider()
    except ImportError:
        return TTSProvider()
