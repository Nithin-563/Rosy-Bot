"""Modular entertainment/games subsystem."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

# A tiny built-in trivia bank so trivia works without external network calls.
_TRIVIA: list[dict[str, Any]] = [
    {"q": "What planet is known as the Red Planet?", "a": ["mars"]},
    {"q": "How many continents are there on Earth?", "a": ["7", "seven"]},
    {"q": "What gas do plants absorb from the atmosphere?", "a": ["carbon dioxide", "co2"]},
    {"q": "How many legs does a spider have?", "a": ["8", "eight"]},
    {"q": "What is the chemical symbol for water?", "a": ["h2o"]},
    {"q": "Which ocean is the largest?", "a": ["pacific"]},
    {"q": "What is the closest star to Earth?", "a": ["the sun", "sun"]},
    {"q": "How many colors are in a rainbow?", "a": ["7", "seven"]},
    {"q": "What is the capital of Japan?", "a": ["tokyo"]},
    {"q": "Which metal is liquid at room temperature?", "a": ["mercury"]},
]

_EIGHTBALL = [
    "It is certain.", "It is decidedly so.", "Without a doubt.", "Yes — definitely.",
    "You may rely on it.", "As I see it, yes.", "Most likely.", "Outlook good.", "Yes.",
    "Signs point to yes.", "Reply hazy, try again.", "Ask again later.", "Better not tell you now.",
    "Cannot predict now.", "Concentrate and ask again.", "Don't count on it.", "My reply is no.",
    "My sources say no.", "Outlook not so good.", "Very doubtful.",
]


@dataclass
class GameSession:
    question: str
    answer: set[str]
    attempts: int = 0
    players: dict[int, int] = field(default_factory=dict)  # user_id -> guesses


class GamesService:
    def __init__(self) -> None:
        self._active: dict[int, GameSession] = {}  # channel_id -> session

    def trivia_question(self) -> GameSession:
        q = random.choice(_TRIVIA)
        return GameSession(question=q["q"], answer={a.lower() for a in q["a"]})

    def start_trivia(self, channel_id: int) -> GameSession:
        sess = self.trivia_question()
        self._active[channel_id] = sess
        return sess

    def try_answer(self, channel_id: int, user_id: int, guess: str) -> str:
        sess = self._active.get(channel_id)
        if sess is None:
            return "no_game"
        sess.attempts += 1
        sess.players[user_id] = sess.players.get(user_id, 0) + 1
        if guess.strip().lower() in sess.answer:
            self._active.pop(channel_id, None)
            return "correct"
        return "wrong"

    def cancel(self, channel_id: int) -> bool:
        return self._active.pop(channel_id, None) is not None

    @staticmethod
    def eightball() -> str:
        return random.choice(_EIGHTBALL)

    @staticmethod
    def roll(dice: int = 1, sides: int = 6) -> list[int]:
        dice = max(1, min(dice, 20))
        sides = max(2, min(sides, 1000))
        return [random.randint(1, sides) for _ in range(dice)]
