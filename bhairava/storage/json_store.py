"""bhairava.storage.json_store -- simple JSON artifact store."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class JsonStore:
    def __init__(self, base_dir: str | Path = "data"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _stamp(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")

    def save(self, name: str, data: Any, subdir: str = "") -> Path:
        folder = self.base_dir / subdir if subdir else self.base_dir
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{name}-{self._stamp()}.json"
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def list(self, subdir: str = "") -> list[Path]:
        folder = self.base_dir / subdir if subdir else self.base_dir
        if not folder.exists():
            return []
        return sorted(folder.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)

    def load(self, path: str | Path) -> Any:
        return json.loads(Path(path).read_text(encoding="utf-8"))
