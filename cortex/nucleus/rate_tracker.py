"""Tracker de rate limit por provider.

Quando um provider retorna 429, marcamos ele como 'em cooldown' por N segundos.
O roteador consulta o tracker e pula providers em cooldown, evitando tentar
e falhar toda hora.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field


DEFAULT_COOLDOWN_SECONDS = 65


@dataclass
class RateTracker:
    cooldowns: dict[str, float] = field(default_factory=dict)
    hits: dict[str, int] = field(default_factory=dict)

    def mark_cooldown(self, provider: str, seconds: int = DEFAULT_COOLDOWN_SECONDS) -> None:
        self.cooldowns[provider] = time.monotonic() + seconds
        self.hits[provider] = self.hits.get(provider, 0) + 1

    def is_in_cooldown(self, provider: str) -> bool:
        until = self.cooldowns.get(provider)
        if until is None:
            return False
        if time.monotonic() >= until:
            # expirou
            self.cooldowns.pop(provider, None)
            return False
        return True

    def remaining(self, provider: str) -> int:
        until = self.cooldowns.get(provider)
        if until is None:
            return 0
        rem = until - time.monotonic()
        return max(0, int(rem))

    def snapshot(self) -> dict[str, dict]:
        return {
            p: {"cooldown_remaining_s": self.remaining(p), "hits": self.hits.get(p, 0)}
            for p in set(list(self.cooldowns.keys()) + list(self.hits.keys()))
            if self.is_in_cooldown(p)
        }


_global_tracker = RateTracker()


def get_rate_tracker() -> RateTracker:
    return _global_tracker
