from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any
import json
import math
import threading
import urllib.request
import uuid

from .settings_manager import SettingsManager


@dataclass
class MemoryEntry:
    """A single local adaptive memory entry."""
    id: str
    ai_uuid: str
    content: str
    tags: list[str]
    source: str
    importance: float
    created_at: str
    embedding: list[float] | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        # Embeddings are large; omit them from JSON if absent to keep files small.
        if data.get("embedding") is None:
            data.pop("embedding", None)
        return data

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "MemoryEntry":
        return cls(
            id=d.get("id", ""),
            ai_uuid=d.get("ai_uuid", ""),
            content=d.get("content", ""),
            tags=list(d.get("tags", [])),
            source=d.get("source", "unknown"),
            importance=float(d.get("importance", 0.5)),
            created_at=d.get("created_at", ""),
            embedding=d.get("embedding"),
        )


class AdaptiveMemoryStore:
    """
    Local-first, per-AI long-term memory store.

    Memories are stored as plain JSON files under the configured memory_path
    (default: ~/CommandNexusWorkspace/memory). Each AI gets its own file so
    privacy is scoped to the AI unit. No cloud or external API is required.

    This is step 1 of the adaptive learning layer: persist, retrieve, and
    search memories offline.
    """

    def __init__(self, settings: SettingsManager | None = None):
        self._settings = settings or SettingsManager()
        s = self._settings.get()
        self._memory_dir = Path(s.memory_path)
        self._memory_dir.mkdir(parents=True, exist_ok=True)
        self._ollama_url = (s.ollama_url or "http://127.0.0.1:11434").rstrip("/")
        self._ollama_model = s.ollama_model or "llama3.1"
        self._lock = threading.Lock()
        self._embedding_available: bool | None = None

    def _ai_file(self, ai_uuid: str) -> Path:
        return self._memory_dir / f"{ai_uuid}.json"

    def _load(self, ai_uuid: str) -> list[MemoryEntry]:
        path = self._ai_file(ai_uuid)
        if not path.exists():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return [MemoryEntry.from_dict(e) for e in data if isinstance(e, dict)]
        except Exception:
            return []

    def _save(self, ai_uuid: str, entries: list[MemoryEntry]) -> None:
        path = self._ai_file(ai_uuid)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps([e.to_dict() for e in entries], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        tmp.replace(path)

    def _embed(self, text: str) -> list[float] | None:
        """Compute a local embedding vector via Ollama. Returns None if unavailable."""
        text = (text or "").strip()[:2000]
        if not text:
            return None
        try:
            payload = json.dumps({"model": self._ollama_model, "prompt": text}).encode("utf-8")
            req = urllib.request.Request(
                self._ollama_url + "/api/embeddings",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
            vec = data.get("embedding")
            if isinstance(vec, list) and len(vec) > 0 and all(isinstance(x, (int, float)) for x in vec):
                return [float(x) for x in vec]
        except Exception:
            pass
        return None

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def add(
        self,
        ai_uuid: str,
        content: str,
        tags: list[str] | None = None,
        source: str = "manual",
        importance: float = 0.5,
    ) -> MemoryEntry:
        """Add a memory entry for the given AI."""
        content = (content or "").strip()
        if not content:
            raise ValueError("Memory content cannot be empty")
        if not ai_uuid:
            raise ValueError("ai_uuid is required")

        entry = MemoryEntry(
            id=str(uuid.uuid4()),
            ai_uuid=ai_uuid,
            content=content,
            tags=[t.strip().lower() for t in (tags or []) if t.strip()],
            source=source,
            importance=max(0.0, min(1.0, float(importance))),
            created_at=datetime.now().isoformat(),
        )

        with self._lock:
            entries = self._load(ai_uuid)
            entries.append(entry)
            self._save(ai_uuid, entries)

        return entry

    def get_for_ai(self, ai_uuid: str) -> list[MemoryEntry]:
        """Return all stored memories for an AI, newest first."""
        with self._lock:
            entries = self._load(ai_uuid)
        return sorted(entries, key=lambda e: e.created_at, reverse=True)

    def get_recent(self, ai_uuid: str, count: int = 10) -> list[MemoryEntry]:
        """Return the most recent N memories for an AI."""
        return self.get_for_ai(ai_uuid)[:count]

    def search(self, ai_uuid: str, query: str) -> list[MemoryEntry]:
        """Hybrid search: semantic if Ollama embeddings are available, else keyword."""
        semantic = self.search_semantic(ai_uuid, query)
        if semantic:
            return semantic
        return self.search_keyword(ai_uuid, query)

    def search_keyword(self, ai_uuid: str, query: str) -> list[MemoryEntry]:
        """Keyword search across memory content and tags for an AI."""
        query = (query or "").strip().lower()
        if not query:
            return self.get_for_ai(ai_uuid)

        terms = query.split()
        entries = self.get_for_ai(ai_uuid)
        scored: list[tuple[float, MemoryEntry]] = []
        for e in entries:
            haystack = (e.content + " " + " ".join(e.tags)).lower()
            score = sum(1 for term in terms if term in haystack)
            if score > 0:
                scored.append((score, e))
        scored.sort(key=lambda x: (x[0], x[1].importance), reverse=True)
        return [e for _, e in scored]

    def search_semantic(self, ai_uuid: str, query: str, top_k: int = 12) -> list[MemoryEntry]:
        """Semantic search using local Ollama embeddings. Falls back silently to keyword."""
        query = (query or "").strip()
        if not query:
            return self.get_for_ai(ai_uuid)[:top_k]

        entries = self.get_for_ai(ai_uuid)
        if not entries:
            return []

        q_vec = self._embed(query)
        if q_vec is None:
            return []

        # Lazily index any memories that are missing embeddings.
        needs_save = False
        for e in entries:
            if e.embedding is None:
                e.embedding = self._embed(e.content)
                if e.embedding is not None:
                    needs_save = True

        if needs_save:
            self._save(ai_uuid, entries)

        ranked = sorted(
            ((self._cosine_similarity(q_vec, e.embedding or []), e) for e in entries),
            key=lambda x: (x[0], x[1].importance),
            reverse=True,
        )
        return [e for score, e in ranked if score > 0][:top_k]

    def get_by_tag(self, ai_uuid: str, tag: str) -> list[MemoryEntry]:
        """Return memories that include a specific tag."""
        tag = tag.strip().lower()
        return [e for e in self.get_for_ai(ai_uuid) if tag in e.tags]

    def delete(self, ai_uuid: str, entry_id: str) -> bool:
        """Delete a memory entry by id. Returns True if removed."""
        with self._lock:
            entries = self._load(ai_uuid)
            before = len(entries)
            entries = [e for e in entries if e.id != entry_id]
            if len(entries) == before:
                return False
            self._save(ai_uuid, entries)
            return True

    def delete_all_for_ai(self, ai_uuid: str) -> bool:
        """Remove all memory for an AI. Returns True if a file was removed."""
        path = self._ai_file(ai_uuid)
        with self._lock:
            if path.exists():
                path.unlink()
                return True
            return False

    def list_ai_uuids(self) -> list[str]:
        """Return all AI UUIDs that have stored memories."""
        return [p.stem for p in self._memory_dir.glob("*.json")]
