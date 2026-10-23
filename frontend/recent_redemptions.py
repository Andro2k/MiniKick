"""Bounded, constant-time deduplication for recent reward events."""

from __future__ import annotations

from collections import deque


class RecentRedemptionCache:
    """Remember a bounded number of redemption keys with O(1) membership checks."""

    def __init__(self, maxlen: int = 100) -> None:
        if maxlen <= 0:
            raise ValueError("maxlen must be greater than zero")
        self._keys: deque[str] = deque()
        self._key_set: set[str] = set()
        self._maxlen = maxlen

    def contains_or_add(self, key: str) -> bool:
        """Return whether ``key`` was already seen, otherwise remember it."""
        if key in self._key_set:
            return True

        if len(self._keys) == self._maxlen:
            expired_key = self._keys.popleft()
            self._key_set.remove(expired_key)

        self._keys.append(key)
        self._key_set.add(key)
        return False
