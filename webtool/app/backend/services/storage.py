from __future__ import annotations

import os
import json
from typing import Any, Optional


class LocalJSONStore:
    def __init__(self, base_dir: Optional[str] = None) -> None:
        self.base_dir = base_dir or os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "..", "data")
        self.base_dir = os.path.abspath(self.base_dir)
        os.makedirs(self.base_dir, exist_ok=True)

    def _path(self, key: str) -> str:
        filename = f"{key}.json"
        return os.path.join(self.base_dir, filename)

    def save(self, key: str, data: Any) -> None:
        path = self._path(key)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh)

    def load(self, key: str) -> Optional[Any]:
        path = self._path(key)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
