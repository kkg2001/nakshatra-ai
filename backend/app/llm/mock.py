"""Offline client for unit tests and dry runs. Uses no quota."""
from __future__ import annotations

from collections.abc import Callable


class MockClient:
    name = "mock"

    def __init__(self, reply: str | Callable[[str, str], str] = "The stars look favourable."):
        self._reply = reply

    def generate(self, system: str, user: str, temperature: float | None = None) -> str:
        return self._reply(system, user) if callable(self._reply) else self._reply
