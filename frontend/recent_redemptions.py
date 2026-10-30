# frontend\recent_redemptions.py\\

from __future__ import annotations
from collections import deque


class RecentRedemptionCache:
    def __init__(self, maxlen: int = 100) -> None:
        if maxlen <= 0:
            raise ValueError("maxlen must be greater than zero")
        self._keys: deque[str] = deque()
        self._key_set: set[str] = set()
        self._maxlen = maxlen

    def contains_or_add(self, key: str) -> bool:
        if key in self._key_set:
            return True

        if len(self._keys) == self._maxlen:
            expired_key = self._keys.popleft()
            self._key_set.remove(expired_key)

        self._keys.append(key)
        self._key_set.add(key)
        return False
