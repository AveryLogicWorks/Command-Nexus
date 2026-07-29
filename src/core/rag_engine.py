# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
# Unauthorized copying, modification, or distribution is prohibited.
# --- IP Watermark ---
# ALW-CN-7F3A-2026-AVERYLOGICWORKS
# AVERY_LOGIC_WORKS_COMMAND_NEXUS_PROPRIETARY_v0.2.0

"""
RAG Engine — Document Knowledge Base for Command Nexus.

Ingests documents (PDF, TXT, MD, DOCX, CSV), chunks them, embeds the
chunks using local embedding models, stores them in a local SQLite
vector database, and retrieves relevant passages for AI missions.

All processing is local. No data leaves the machine.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import threading
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Optional

from .settings_manager import SettingsManager


# ─── Data structures ──────────────────────────────────────────────────

@dataclass
class DocumentRecord:
    """A registered document in the knowledge base."""
    doc_id: str
    filename: str
    file_path: str
    file_hash: str
    chunk_count: int
    enabled: bool = True
    date_added: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RetrievedChunk:
    """A retrieved chunk with relevance score."""
    text: str
    score: float
    source_doc: str
    chunk_index: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ─── Text chunking ────────────────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> list[str]:
    """Split text into overlapping chunks by word count."""
    words = text.split()
    if not words:
        return []
    chunks: list[str] = []
    i = 0
    while i < len(words):
        end = min(i + chunk_size, len(words))
        chunk = " ".join(words[i:end])
        chunks.append(chunk)
        if end >= len(words):
            break
        i += chunk_size - overlap
    return chunks


# ─── Document parsers ─────────────────────────────────────────────────

def parse_pdf(path: Path) -> str:
    """Extract text from a PDF file."""
    try:
        from pdfminer.high_level import extract_text
        return extract_text(str(path))
    except ImportError:
        try:
            import PyPDF2
            text_parts: list[str] = []
            with open(path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text_parts.append(page.extract_text() or "")
            return "\n".join(text_parts)
        except ImportError:
            return f"[PDF parsing requires pdfminer or PyPDF2. Install: pip install pdfminer.six]"
    except Exception as e:
        return f"[PDF parse error: {e}]"


def parse_docx(path: Path) -> str:
    """Extract text from a DOCX file."""
    try:
        from docx import Document
        doc = Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except ImportError:
        return f"[DOCX parsing requires python-docx. Install: pip install python-docx]"
    except Exception as e:
        return f"[DOCX parse error: {e}]"


def parse_csv(path: Path) -> str:
    """Extract text from a CSV file (convert rows to text)."""
    try:
        import csv
        text_parts: list[str] = []
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            for row in reader:
                text_parts.append(" | ".join(row))
        return "\n".join(text_parts)
    except Exception as e:
        return f"[CSV parse error: {e}]"


def parse_plain(path: Path) -> str:
    """Read a plain text or markdown file."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"[File read error: {e}]"


def parse_document(path: Path) -> str:
    """Parse a document based on its file extension."""
    ext = path.suffix.lower()
    if ext == ".pdf":
        return parse_pdf(path)
    elif ext == ".docx":
        return parse_docx(path)
    elif ext == ".csv":
        return parse_csv(path)
    elif ext in (".txt", ".md", ".markdown", ".rtf", ".log", ".py", ".js", ".json", ".xml", ".html", ".yaml", ".yml"):
        return parse_plain(path)
    else:
        return parse_plain(path)  # Try as plain text


# ─── Embedding ────────────────────────────────────────────────────────

def _file_hash(path: Path) -> str:
    """Compute SHA256 hash of a file."""
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for block in iter(lambda: f.read(8192), b""):
                h.update(block)
    except OSError:
        pass
    return h.hexdigest()


def _text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class EmbeddingEngine:
    """
    Local embedding engine using sentence-transformers or ONNX runtime.
    Falls back to a simple hash-based pseudo-embedding if no library is available.
    """

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        self._model_name = model_name
        self._model = None
        self._tokenizer = None
        self._dim = 384
        self._backend = "none"
        self._lock = threading.Lock()

    def _load_model(self):
        """Lazily load the embedding model."""
        if self._model is not None:
            return
        with self._lock:
            if self._model is not None:
                return
            # Try sentence-transformers first
            try:
                from sentence_transformers import SentenceTransformer
                # Try local model path first
                local_paths = [
                    Path("b:/local_models/bge-small-en-v1.5"),
                    Path.home() / "local_models" / "bge-small-en-v1.5",
                ]
                model_path = None
                for p in local_paths:
                    if p.exists():
                        model_path = str(p)
                        break
                if model_path:
                    self._model = SentenceTransformer(model_path)
                else:
                    self._model = SentenceTransformer(self._model_name)
                self._dim = self._model.get_sentence_embedding_dimension()
                self._backend = "sentence-transformers"
                return
            except ImportError:
                pass
            # Try ONNX runtime with tokenizers
            try:
                import numpy as np
                import onnxruntime as ort
                from tokenizers import Tokenizer
                onnx_paths = [
                    Path("b:/local_models/bge-small-en-v1.5/onnx/model.onnx"),
                    Path.home() / "local_models" / "bge-small-en-v1.5" / "onnx" / "model.onnx",
                ]
                tokenizer_paths = [
                    Path("b:/local_models/bge-small-en-v1.5/tokenizer.json"),
                    Path.home() / "local_models" / "bge-small-en-v1.5" / "tokenizer.json",
                ]
                onnx_path = None
                tokenizer_path = None
                for p in onnx_paths:
                    if p.exists():
                        onnx_path = str(p)
                        break
                for p in tokenizer_paths:
                    if p.exists():
                        tokenizer_path = str(p)
                        break
                if onnx_path and tokenizer_path:
                    self._model = ort.InferenceSession(onnx_path)
                    self._tokenizer = Tokenizer.from_file(tokenizer_path)
                    self._tokenizer.enable_truncation(max_length=512)
                    self._tokenizer.enable_padding(pad_id=0, pad_token="[PAD]", pad_type="batch")
                    self._backend = "onnx"
                    return
            except ImportError:
                pass
            # Fallback: pseudo-embedding (hash-based, deterministic)
            self._backend = "hash"
            self._dim = 256

    def embed(self, text: str) -> list[float]:
        """Generate an embedding vector for the given text."""
        self._load_model()
        text = (text or "").strip()[:2000]
        if not text:
            return [0.0] * self._dim

        if self._backend == "sentence-transformers":
            vec = self._model.encode(text, normalize_embeddings=True)
            return [float(x) for x in vec]
        elif self._backend == "onnx":
            # ONNX inference with proper tokenization
            try:
                import numpy as np
                encoding = self._tokenizer.encode(text)
                input_ids = np.array([encoding.ids], dtype=np.int64)
                attention_mask = np.array([encoding.attention_mask], dtype=np.int64)
                token_type_ids = np.zeros_like(input_ids, dtype=np.int64)
                outputs = self._model.run(None, {
                    "input_ids": input_ids,
                    "attention_mask": attention_mask,
                    "token_type_ids": token_type_ids,
                })
                # Mean pooling over token embeddings
                token_embeddings = outputs[0]  # (1, seq_len, hidden_dim)
                mask = attention_mask[..., None].astype(np.float32)
                summed = (token_embeddings * mask).sum(axis=1)
                counts = mask.sum(axis=1).clip(min=1e-9)
                pooled = summed / counts  # (1, hidden_dim)
                # Normalize
                norm = float(np.linalg.norm(pooled)) or 1.0
                vec = (pooled / norm).flatten()
                self._dim = len(vec)
                return [float(x) for x in vec]
            except Exception:
                return self._pseudo_embed(text)
        else:
            return self._pseudo_embed(text)

    def _pseudo_embed(self, text: str) -> list[float]:
        """Deterministic hash-based pseudo-embedding (fallback only)."""
        import hashlib
        import struct
        vec = [0.0] * self._dim
        words = text.lower().split()
        for word in words:
            h = hashlib.md5(word.encode("utf-8")).digest()
            for i in range(0, min(len(h), self._dim // 8)):
                val = struct.unpack("f", h[i*4:i*4+4])[0] if i*4+4 <= len(h) else 0.0
                vec[i] += val
        # Normalize
        import math
        magnitude = math.sqrt(sum(v*v for v in vec)) or 1.0
        return [v / magnitude for v in vec]

    @property
    def backend(self) -> str:
        return self._backend

    @property
    def dimension(self) -> int:
        return self._dim


# ─── Vector store (SQLite) ────────────────────────────────────────────

class VectorStore:
    """
    SQLite-backed vector storage for document chunks.
    Uses cosine similarity for retrieval.
    """

    def __init__(self, db_path: Path):
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        with self._lock, sqlite3.connect(str(self._db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    doc_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_hash TEXT NOT NULL,
                    chunk_count INTEGER DEFAULT 0,
                    enabled INTEGER DEFAULT 1,
                    date_added TEXT DEFAULT ''
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    chunk_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doc_id TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    embedding TEXT NOT NULL,
                    text_hash TEXT NOT NULL,
                    FOREIGN KEY (doc_id) REFERENCES documents(doc_id) ON DELETE CASCADE
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(doc_id)")
            conn.commit()

    def add_document(self, doc: DocumentRecord, chunks: list[tuple[str, list[float]]]) -> bool:
        """Add a document and its chunks to the store. Returns True on success."""
        with self._lock, sqlite3.connect(str(self._db_path)) as conn:
            try:
                # Remove existing doc if present (re-indexing)
                conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc.doc_id,))
                conn.execute("DELETE FROM documents WHERE doc_id = ?", (doc.doc_id,))
                # Insert document
                conn.execute(
                    "INSERT INTO documents (doc_id, filename, file_path, file_hash, chunk_count, enabled, date_added) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (doc.doc_id, doc.filename, doc.file_path, doc.file_hash, len(chunks), 1, doc.date_added)
                )
                # Insert chunks
                for i, (text, embedding) in enumerate(chunks):
                    conn.execute(
                        "INSERT INTO chunks (doc_id, chunk_index, text, embedding, text_hash) VALUES (?, ?, ?, ?, ?)",
                        (doc.doc_id, i, text, json.dumps(embedding), _text_hash(text))
                    )
                conn.commit()
                return True
            except Exception as e:
                conn.rollback()
                raise e

    def remove_document(self, doc_id: str) -> bool:
        """Remove a document and all its chunks."""
        with self._lock, sqlite3.connect(str(self._db_path)) as conn:
            conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
            cursor = conn.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
            conn.commit()
            return cursor.rowcount > 0

    def set_enabled(self, doc_id: str, enabled: bool) -> None:
        """Enable or disable a document."""
        with self._lock, sqlite3.connect(str(self._db_path)) as conn:
            conn.execute("UPDATE documents SET enabled = ? WHERE doc_id = ?", (1 if enabled else 0, doc_id))
            conn.commit()

    def list_documents(self) -> list[DocumentRecord]:
        """List all documents in the store."""
        with self._lock, sqlite3.connect(str(self._db_path)) as conn:
            cursor = conn.execute("SELECT doc_id, filename, file_path, file_hash, chunk_count, enabled, date_added FROM documents")
            rows = cursor.fetchall()
            return [DocumentRecord(
                doc_id=r[0], filename=r[1], file_path=r[2], file_hash=r[3],
                chunk_count=r[4], enabled=bool(r[5]), date_added=r[6]
            ) for r in rows]

    def get_document(self, doc_id: str) -> DocumentRecord | None:
        """Get a single document by ID."""
        with self._lock, sqlite3.connect(str(self._db_path)) as conn:
            cursor = conn.execute(
                "SELECT doc_id, filename, file_path, file_hash, chunk_count, enabled, date_added FROM documents WHERE doc_id = ?",
                (doc_id,)
            )
            r = cursor.fetchone()
            if not r:
                return None
            return DocumentRecord(
                doc_id=r[0], filename=r[1], file_path=r[2], file_hash=r[3],
                chunk_count=r[4], enabled=bool(r[5]), date_added=r[6]
            )

    def search(self, query_embedding: list[float], top_k: int = 5, enabled_only: bool = True) -> list[tuple[str, float, str, str, int]]:
        """
        Search for similar chunks. Returns list of (text, score, doc_id, filename, chunk_index).
        Uses cosine similarity.
        """
        import math
        results: list[tuple[float, str, str, str, int]] = []
        query_mag = math.sqrt(sum(v*v for v in query_embedding)) or 1.0
        query_norm = [v / query_mag for v in query_embedding]

        with self._lock, sqlite3.connect(str(self._db_path)) as conn:
            if enabled_only:
                cursor = conn.execute("""
                    SELECT c.text, c.embedding, c.doc_id, d.filename, c.chunk_index
                    FROM chunks c
                    JOIN documents d ON c.doc_id = d.doc_id
                    WHERE d.enabled = 1
                """)
            else:
                cursor = conn.execute("""
                    SELECT c.text, c.embedding, c.doc_id, d.filename, c.chunk_index
                    FROM chunks c
                    JOIN documents d ON c.doc_id = d.doc_id
                """)
            for text, emb_json, doc_id, filename, chunk_idx in cursor.fetchall():
                try:
                    emb = json.loads(emb_json)
                    # Cosine similarity
                    emb_mag = math.sqrt(sum(v*v for v in emb)) or 1.0
                    emb_norm = [v / emb_mag for v in emb]
                    dot = sum(a*b for a, b in zip(query_norm, emb_norm))
                    results.append((dot, text, doc_id, filename, chunk_idx))
                except Exception:
                    continue

        # Sort by score descending, return top_k
        results.sort(key=lambda x: x[0], reverse=True)
        return [(text, score, doc_id, filename, chunk_idx) for score, text, doc_id, filename, chunk_idx in results[:top_k]]

    def get_chunk_count(self, doc_id: str | None = None) -> int:
        """Get total chunk count, or count for a specific document."""
        with self._lock, sqlite3.connect(str(self._db_path)) as conn:
            if doc_id:
                cursor = conn.execute("SELECT COUNT(*) FROM chunks WHERE doc_id = ?", (doc_id,))
            else:
                cursor = conn.execute("SELECT COUNT(*) FROM chunks")
            return cursor.fetchone()[0]

    def get_storage_size(self) -> int:
        """Get the SQLite database file size in bytes."""
        try:
            return self._db_path.stat().st_size
        except OSError:
            return 0


# ─── Main RAG engine ──────────────────────────────────────────────────

class RAGEngine:
    """
    Main RAG engine. Coordinates document ingestion, embedding, storage,
    and retrieval.
    """

    SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".markdown", ".docx", ".csv", ".rtf", ".log", ".py", ".js", ".json", ".xml", ".html", ".yaml", ".yml"}

    def __init__(self, settings: SettingsManager | None = None):
        self._settings = settings or SettingsManager()
        # Store RAG database in the memory path
        base = Path(self._settings.get().memory_path or "~/CommandNexusWorkspace/memory").expanduser()
        base.mkdir(parents=True, exist_ok=True)
        self._db_path = base / "rag_vector_db.sqlite"
        self._vector_store = VectorStore(self._db_path)
        self._embedder = EmbeddingEngine()
        self._chunk_size = 512
        self._chunk_overlap = 64
        self._top_k = 5

    @property
    def embedder_backend(self) -> str:
        """Return the current embedding backend name."""
        return self._embedder.backend

    @property
    def chunk_count(self) -> int:
        """Total number of chunks in the knowledge base."""
        return self._vector_store.get_chunk_count()

    @property
    def storage_size_mb(self) -> float:
        """Database file size in MB."""
        return round(self._vector_store.get_storage_size() / (1024 * 1024), 2)

    # ─── Document ingestion ───────────────────────────────────────────

    def ingest_file(self, file_path: str | Path) -> DocumentRecord | None:
        """
        Ingest a single file into the knowledge base.
        Returns the DocumentRecord on success, None on failure.
        """
        path = Path(file_path)
        if not path.exists():
            return None
        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            return None

        # Parse document
        text = parse_document(path)
        if not text or text.startswith("[") and "error" in text.lower():
            return None

        # Chunk the text
        chunks = chunk_text(text, self._chunk_size, self._chunk_overlap)
        if not chunks:
            return None

        # Embed each chunk
        embedded_chunks: list[tuple[str, list[float]]] = []
        for chunk in chunks:
            emb = self._embedder.embed(chunk)
            embedded_chunks.append((chunk, emb))

        # Create document record
        file_hash = _file_hash(path)
        doc_id = file_hash[:16]  # Use first 16 chars of hash as doc ID
        from datetime import datetime
        doc = DocumentRecord(
            doc_id=doc_id,
            filename=path.name,
            file_path=str(path),
            file_hash=file_hash,
            chunk_count=len(chunks),
            enabled=True,
            date_added=datetime.now().isoformat(),
        )

        # Store
        self._vector_store.add_document(doc, embedded_chunks)
        return doc

    def remove_document(self, doc_id: str) -> bool:
        """Remove a document from the knowledge base."""
        return self._vector_store.remove_document(doc_id)

    def set_document_enabled(self, doc_id: str, enabled: bool) -> None:
        """Enable or disable a document for retrieval."""
        self._vector_store.set_enabled(doc_id, enabled)

    def list_documents(self) -> list[DocumentRecord]:
        """List all documents in the knowledge base."""
        return self._vector_store.list_documents()

    def get_document(self, doc_id: str) -> DocumentRecord | None:
        """Get a document by ID."""
        return self._vector_store.get_document(doc_id)

    # ─── Retrieval ────────────────────────────────────────────────────

    def retrieve(self, query: str, top_k: int | None = None) -> list[RetrievedChunk]:
        """
        Retrieve relevant chunks for a query.
        Returns a list of RetrievedChunk objects sorted by relevance.
        """
        top_k = top_k or self._top_k
        query = (query or "").strip()
        if not query:
            return []

        query_embedding = self._embedder.embed(query)
        results = self._vector_store.search(query_embedding, top_k=top_k, enabled_only=True)

        return [
            RetrievedChunk(
                text=text,
                score=score,
                source_doc=filename,
                chunk_index=chunk_idx,
            )
            for text, score, doc_id, filename, chunk_idx in results
            if score > 0.01  # Filter out irrelevant results
        ]

    def retrieve_for_prompt(self, query: str, top_k: int | None = None) -> str:
        """
        Retrieve relevant chunks and format them as a context string
        suitable for injection into an AI prompt.
        """
        chunks = self.retrieve(query, top_k)
        if not chunks:
            return ""

        context_parts: list[str] = ["[Knowledge Context from your documents]"]
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(f"[{i}] From '{chunk.source_doc}' (relevance: {chunk.score:.2f}):")
            context_parts.append(chunk.text)
            context_parts.append("")  # Blank line separator

        return "\n".join(context_parts)

    # ─── Configuration ────────────────────────────────────────────────

    def set_chunk_size(self, size: int) -> None:
        """Set the chunk size (in words). Must be between 64 and 2048."""
        self._chunk_size = max(64, min(2048, size))

    def set_chunk_overlap(self, overlap: int) -> None:
        """Set the chunk overlap (in words). Must be between 0 and chunk_size/2."""
        self._chunk_overlap = max(0, min(self._chunk_size // 2, overlap))

    def set_top_k(self, k: int) -> None:
        """Set the default number of chunks to retrieve."""
        self._top_k = max(1, min(20, k))

    def get_config(self) -> dict[str, Any]:
        """Return current configuration."""
        return {
            "chunk_size": self._chunk_size,
            "chunk_overlap": self._chunk_overlap,
            "top_k": self._top_k,
            "embedder_backend": self._embedder.backend,
            "embedding_dim": self._embedder.dimension,
            "total_chunks": self.chunk_count,
            "storage_mb": self.storage_size_mb,
        }
