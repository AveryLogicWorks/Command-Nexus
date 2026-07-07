# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
"""
Prototyper LLM Bridge — SECONDARY intelligence only.
Used exclusively for web research, online lookups, and external data gathering.
The core engineering intelligence is handled by PrototyperIntelligence (no LLM needed).
"""
from __future__ import annotations
import json
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal


class PrototyperLLM(QObject):
    """
    Secondary LLM bridge for research tasks only.
    Connects to local GGUF models via llama-cpp-python or Ollama.
    Only invoked when the intelligence engine routes a RESEARCH intent.
    """
    research_complete = pyqtSignal(str)
    research_error = pyqtSignal(str)

    # Available local models found on disk
    AVAILABLE_MODELS = [
        "Qwen2.5-0.5B-Instruct",
        "Qwen2.5-7B-Instruct",
        "Qwen2.5-Coder-3B-Instruct",
        "Qwen2.5-Coder-7B-Instruct",
        "Qwen3-8B-Q4_K_M",
        "Qwen2.5-Coder-14B-Instruct-Q4_K_M",
        "Qwen2.5-Coder-32B-Instruct-Q4_K_M",
        "Qwen2.5-VL-3B-Instruct-Q4_K_M",
        "Qwen3-14B-Q4_K_M",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._llm = None
        self._model_path = ""
        self._selected_model = "Qwen2.5-7B-Instruct"
        self._ollama_url = "http://127.0.0.1:11434"

    def set_model(self, model_name: str):
        self._selected_model = model_name
        self._llm = None  # force reload
        self._model_path = ""

    def get_selected_model(self) -> str:
        return self._selected_model

    @staticmethod
    def list_available_models() -> list[str]:
        """Scan b:\\local_models for .gguf files."""
        models = []
        search_dirs = [Path("b:/local_models"), Path.home() / "local_models"]
        for base in search_dirs:
            if base.exists():
                for f in base.rglob("*.gguf"):
                    models.append(f.stem)
        return sorted(set(models)) if models else PrototyperLLM.AVAILABLE_MODELS

    def _find_gguf(self, model_name: str) -> str:
        """Find GGUF file for a model name."""
        search_dirs = [Path("b:/local_models"), Path.home() / "local_models"]
        for base in search_dirs:
            if not base.exists():
                continue
            model_dir = base / model_name
            if model_dir.exists():
                for f in model_dir.glob("*.gguf"):
                    return str(f)
            for f in base.rglob("*.gguf"):
                if model_name.lower() in f.stem.lower():
                    return str(f)
        for base in search_dirs:
            if base.exists():
                for f in base.rglob("*.gguf"):
                    return str(f)
        return ""

    def _load_llm(self):
        """Lazily load the GGUF model via llama-cpp-python."""
        if self._llm is not None:
            return
        gguf_path = self._find_gguf(self._selected_model)
        if not gguf_path:
            raise RuntimeError(
                f"No .gguf model found for '{self._selected_model}'. "
                f"Place GGUF files in b:\\local_models\\"
            )
        try:
            from llama_cpp import Llama
        except ImportError:
            raise RuntimeError(
                "llama-cpp-python not installed. Run: pip install llama-cpp-python"
            )
        import multiprocessing
        self._llm = Llama(
            model_path=gguf_path,
            n_ctx=4096,
            n_threads=min(multiprocessing.cpu_count(), 4),
            n_gpu_layers=0,
            verbose=False,
            use_mlock=False,
            use_mmap=True,
        )
        self._model_path = gguf_path

    def research(self, query: str) -> str:
        """
        Use the LLM for research/web lookup tasks.
        This is the ONLY method that calls the LLM.
        Returns research findings as text.
        """
        system = (
            "You are a research assistant for a 3D prototyping tool. "
            "Search your knowledge for engineering, materials, aerodynamics, "
            "and manufacturing information. Be concise and factual. "
            "If you don't know, say so. Do not make up specifications."
        )
        try:
            self._load_llm()
            response = self._llm.create_chat_completion(
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": query},
                ],
                max_tokens=512,
                temperature=0.3,
                top_p=0.9,
                stop=[],
            )
            text = (response["choices"][0]["message"]["content"] or "").strip()
            self.research_complete.emit(text)
            return text
        except Exception as e:
            msg = f"Research model unavailable: {e}"
            self.research_error.emit(msg)
            return msg

    def research_via_ollama(self, query: str) -> str:
        """Alternative: use Ollama if running locally."""
        payload = {
            "model": self._selected_model,
            "prompt": f"Research query: {query}\nProvide concise factual findings.",
            "stream": False,
        }
        try:
            req = urllib.request.Request(
                self._ollama_url + "/api/generate",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
            text = (data.get("response") or "").strip()
            self.research_complete.emit(text)
            return text
        except Exception as e:
            msg = f"Ollama unavailable: {e}"
            self.research_error.emit(msg)
            return msg
