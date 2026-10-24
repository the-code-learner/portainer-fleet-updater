from __future__ import annotations

import json
import os
from pathlib import Path
from threading import RLock

_LOCK = RLock()


class SettingsStore:
    def __init__(self, data_dir: str | None = None) -> None:
        root = Path(data_dir or os.environ.get("PFU_DATA_DIR", "/data"))
        root.mkdir(parents=True, exist_ok=True)
        self.path = root / "settings.json"

    def _read(self) -> dict:
        if not self.path.exists():
            return {"managed_stack_ids": []}
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"managed_stack_ids": []}
        if not isinstance(value, dict):
            return {"managed_stack_ids": []}
        ids = value.get("managed_stack_ids", [])
        if not isinstance(ids, list):
            ids = []
        normalized = []
        for item in ids:
            try:
                normalized.append(int(item))
            except (TypeError, ValueError):
                pass
        return {"managed_stack_ids": sorted(set(normalized))}

    def managed_stack_ids(self) -> set[int]:
        with _LOCK:
            return set(self._read()["managed_stack_ids"])

    def set_managed_stack_ids(self, ids: list[int]) -> list[int]:
        normalized = sorted(set(int(item) for item in ids))
        payload = {"managed_stack_ids": normalized}
        temporary = self.path.with_suffix(".tmp")
        with _LOCK:
            temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            temporary.replace(self.path)
        return normalized
