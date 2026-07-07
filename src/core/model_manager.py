# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
# Unauthorized copying, modification, or distribution is prohibited.
# --- IP Watermark ---
# ALW-CN-7F3A-2026-AVERYLOGICWORKS
# AVERY_LOGIC_WORKS_COMMAND_NEXUS_PROPRIETARY_v0.2.0

"""
Model Manager — Core engine for discovering, categorizing, and managing
local GGUF models on disk.

Basic tier: up to 3 concurrent models.
Advanced tier: unlimited concurrent models + custom routing + benchmarking.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from .settings_manager import SettingsManager


class ModelCategory(str, Enum):
    CHAT = "chat"
    CODER = "coder"
    PLANNER = "planner"
    VISION = "vision"
    SMALL = "small"
    UNKNOWN = "unknown"


@dataclass
class LocalModelInfo:
    name: str
    path: str
    size_mb: float
    category: ModelCategory
    recommended_for: list[str] = field(default_factory=list)
    min_ram_mb: int = 0
    quantization: str = ""
    parameter_count: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["category"] = self.category.value
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "LocalModelInfo":
        return cls(
            name=d.get("name", ""),
            path=d.get("path", ""),
            size_mb=float(d.get("size_mb", 0)),
            category=ModelCategory(d.get("category", "unknown")),
            recommended_for=d.get("recommended_for", []),
            min_ram_mb=int(d.get("min_ram_mb", 0)),
            quantization=d.get("quantization", ""),
            parameter_count=d.get("parameter_count", ""),
        )


_MODEL_PATTERNS: list[tuple[str, ModelCategory, list[str], int]] = [
    (r"coder", ModelCategory.CODER, ["Code Generation", "Code Review", "API Integration"], 4096),
    (r"code", ModelCategory.CODER, ["Code Generation", "Code Review"], 4096),
    (r"planner", ModelCategory.PLANNER, ["Planning", "Task Management", "Orchestration"], 8192),
    (r"qwen3", ModelCategory.PLANNER, ["Planning", "Task Management", "Reasoning"], 8192),
    (r"vl|vision|ocr", ModelCategory.VISION, ["Image Analysis", "OCR", "Scene Understanding"], 4096),
    (r"0\.5b|0_5b", ModelCategory.SMALL, ["Chat", "Light Tasks", "Quick Responses"], 1024),
    (r"1\.5b|1_5b", ModelCategory.SMALL, ["Chat", "Light Tasks"], 2048),
    (r"3b", ModelCategory.CHAT, ["Chat", "Writing", "Summarization"], 3072),
    (r"7b", ModelCategory.CHAT, ["Chat", "Writing", "Research", "Creative"], 6144),
    (r"8b", ModelCategory.CHAT, ["Chat", "Writing", "Research", "Creative"], 8192),
    (r"14b", ModelCategory.CHAT, ["Chat", "Research", "Analysis", "Business"], 12288),
    (r"32b", ModelCategory.CHAT, ["Advanced Research", "Legal", "Enterprise"], 24576),
]

_QUANT_RE = re.compile(r"(Q[0-9]_[KM]+|q[0-9]_[km]+|f16|fp16|f32|fp32)", re.IGNORECASE)
_PARAM_RE = re.compile(r"(\d+\.?\d*[bB])")


def _categorize_model(filename: str) -> tuple[ModelCategory, list[str], int]:
    name_lower = filename.lower()
    for pattern, category, recommended, min_ram in _MODEL_PATTERNS:
        if re.search(pattern, name_lower):
            return category, recommended, min_ram
    return ModelCategory.UNKNOWN, ["General"], 4096


def _extract_quantization(filename: str) -> str:
    m = _QUANT_RE.search(filename)
    return m.group(1).upper() if m else ""


def _extract_param_count(filename: str) -> str:
    m = _PARAM_RE.search(filename)
    return m.group(1).upper() if m else ""


def _file_size_mb(path: Path) -> float:
    try:
        return round(path.stat().st_size / (1024 * 1024), 1)
    except OSError:
        return 0.0


class ModelManager:
    """Core model manager engine. Scans local dirs for .gguf models."""

    SEARCH_DIRS: list[Path] = [
        Path("b:/local_models"),
        Path.home() / "local_models",
    ]
    BASIC_MAX_CONCURRENT = 3

    def __init__(self, settings: SettingsManager | None = None):
        self._settings = settings or SettingsManager()
        self._models: list[LocalModelInfo] = []
        self._active_model: str = ""
        self._concurrent_models: list[str] = []
        self._advanced_mode: bool = False
        self._load_state()
        self.scan_models()

    def _state_path(self) -> Path:
        base = Path(self._settings.get().memory_path or "~/CommandNexusWorkspace/memory").expanduser()
        base.mkdir(parents=True, exist_ok=True)
        return base / "model_manager_state.json"

    def _load_state(self) -> None:
        p = self._state_path()
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                self._active_model = data.get("active_model", "")
                self._concurrent_models = data.get("concurrent_models", [])
                self._advanced_mode = data.get("advanced_mode", False)
            except Exception:
                pass

    def _save_state(self) -> None:
        p = self._state_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({
            "active_model": self._active_model,
            "concurrent_models": self._concurrent_models,
            "advanced_mode": self._advanced_mode,
        }, indent=2), encoding="utf-8")

    def scan_models(self) -> list[LocalModelInfo]:
        """Scan all search directories for .gguf files."""
        found: dict[str, LocalModelInfo] = {}
        for base in self.SEARCH_DIRS:
            if not base.exists():
                continue
            try:
                for gguf in base.rglob("*.gguf"):
                    name = gguf.stem
                    if name in found:
                        continue
                    category, recommended, min_ram = _categorize_model(name)
                    found[name] = LocalModelInfo(
                        name=name, path=str(gguf), size_mb=_file_size_mb(gguf),
                        category=category, recommended_for=recommended,
                        min_ram_mb=min_ram, quantization=_extract_quantization(name),
                        parameter_count=_extract_param_count(name),
                    )
            except (OSError, PermissionError):
                continue
        self._models = sorted(found.values(), key=lambda m: (m.category.value, m.name))
        valid_names = {m.name for m in self._models}
        if self._active_model and self._active_model not in valid_names:
            self._active_model = ""
        self._concurrent_models = [n for n in self._concurrent_models if n in valid_names]
        self._save_state()
        return self._models

    def list_models(self) -> list[LocalModelInfo]:
        return list(self._models)

    def get_model(self, name: str) -> LocalModelInfo | None:
        for m in self._models:
            if m.name == name:
                return m
        return None

    def get_active_model(self) -> str:
        return self._active_model

    def get_concurrent_models(self) -> list[str]:
        return list(self._concurrent_models)

    def get_max_concurrent(self) -> int:
        return 999 if self._advanced_mode else self.BASIC_MAX_CONCURRENT

    def is_advanced(self) -> bool:
        return self._advanced_mode

    def set_advanced_mode(self, enabled: bool) -> None:
        self._advanced_mode = enabled
        self._save_state()

    def set_active_model(self, name: str) -> bool:
        if not self.get_model(name):
            return False
        self._active_model = name
        if name not in self._concurrent_models:
            if len(self._concurrent_models) < self.get_max_concurrent():
                self._concurrent_models.append(name)
            elif self._concurrent_models:
                self._concurrent_models[0] = name
        self._save_state()
        return True

    def add_concurrent_model(self, name: str) -> bool:
        if not self.get_model(name):
            return False
        if name in self._concurrent_models:
            return True
        if len(self._concurrent_models) >= self.get_max_concurrent():
            return False
        self._concurrent_models.append(name)
        self._save_state()
        return True

    def remove_concurrent_model(self, name: str) -> None:
        if name in self._concurrent_models:
            self._concurrent_models.remove(name)
        if self._active_model == name:
            self._active_model = self._concurrent_models[0] if self._concurrent_models else ""
        self._save_state()

    def clear_concurrent_models(self) -> None:
        self._concurrent_models = []
        self._active_model = ""
        self._save_state()

    def recommend_for_use_case(self, use_case: str) -> LocalModelInfo | None:
        uc = use_case.lower()
        prefs: list[ModelCategory] = []
        if any(k in uc for k in ["code", "program", "debug", "api", "script"]):
            prefs.append(ModelCategory.CODER)
        if any(k in uc for k in ["plan", "orchestrat", "manage", "coordinate"]):
            prefs.append(ModelCategory.PLANNER)
        if any(k in uc for k in ["image", "vision", "ocr", "photo"]):
            prefs.append(ModelCategory.VISION)
        if any(k in uc for k in ["chat", "write", "research", "creative", "summarize", "email"]):
            prefs.append(ModelCategory.CHAT)
        prefs.append(ModelCategory.SMALL)
        for pref in prefs:
            candidates = [m for m in self._models if m.category == pref]
            if candidates:
                return min(candidates, key=lambda m: m.size_mb)
        return self._models[0] if self._models else None

    def recommend_for_capability(self, capability_id: str) -> LocalModelInfo | None:
        cap_map = {
            "chat": "chat conversation", "codegen": "code generation programming",
            "codereview": "code review programming", "creative": "creative writing",
            "research": "research analysis", "academic": "academic research",
            "email": "email writing", "planner": "planning task management",
            "tutor": "teaching education chat", "language": "language translation chat",
            "vision": "image vision analysis", "organizer": "organization planning",
            "taskmgr": "task management planning",
        }
        return self.recommend_for_use_case(cap_map.get(capability_id.lower(), capability_id))

    def get_system_ram_mb(self) -> int:
        try:
            import psutil
            return int(psutil.virtual_memory().total / (1024 * 1024))
        except ImportError:
            pass
        try:
            if os.name == "nt":
                import ctypes
                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("sullAvailExtendedVirtual", ctypes.c_ulonglong)]
                stat = MEMORYSTATUSEX()
                stat.dwLength = ctypes.sizeof(stat)
                ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
                return int(stat.ullTotalPhys / (1024 * 1024))
        except Exception:
            pass
        return 8192

    def get_cpu_cores(self) -> int:
        try:
            import multiprocessing
            return multiprocessing.cpu_count()
        except Exception:
            return 4

    def can_run_model(self, model: LocalModelInfo) -> bool:
        system_ram = self.get_system_ram_mb()
        estimated_ram = int(model.size_mb * 1.3)
        return estimated_ram < system_ram * 0.7

    def estimate_concurrent_capacity(self) -> int:
        system_ram = self.get_system_ram_mb()
        usable = system_ram * 0.6
        if not self._models:
            return 0
        smallest = min(self._models, key=lambda m: m.size_mb)
        per_model = smallest.size_mb * 1.3
        if per_model <= 0:
            return 1
        return max(1, int(usable / per_model))

    def get_model_path(self, name: str) -> str:
        model = self.get_model(name)
        return model.path if model else ""

    # ─── Advanced Model Manager features ──────────────────────────────

    def set_model_routing(self, capability: str, model_name: str) -> bool:
        """Route a specific capability to a specific model (Advanced only)."""
        if not self._advanced_mode:
            return False
        if not self.get_model(model_name):
            return False
        state = self._load_full_state()
        routing = state.get("model_routing", {})
        routing[capability] = model_name
        state["model_routing"] = routing
        self._save_full_state(state)
        return True

    def get_model_routing(self) -> dict[str, str]:
        """Get the capability-to-model routing map."""
        state = self._load_full_state()
        return state.get("model_routing", {})

    def clear_model_routing(self) -> None:
        """Clear all model routing."""
        state = self._load_full_state()
        state["model_routing"] = {}
        self._save_full_state(state)

    def get_routed_model(self, capability: str) -> str:
        """Get the model name routed for a specific capability, or empty string."""
        routing = self.get_model_routing()
        return routing.get(capability, "")

    def benchmark_model(self, model_name: str) -> dict[str, Any]:
        """
        Run a quick benchmark on a model (Advanced only).
        Returns dict with tokens/sec, load_time_ms, and memory_usage_mb.
        """
        if not self._advanced_mode:
            return {"error": "Advanced mode required for benchmarking"}
        model = self.get_model(model_name)
        if not model:
            return {"error": f"Model '{model_name}' not found"}

        import time
        result: dict[str, Any] = {
            "model": model_name,
            "size_mb": model.size_mb,
            "category": model.category.value,
            "timestamp": "",
        }

        try:
            from datetime import datetime
            result["timestamp"] = datetime.now().isoformat()

            # Try loading with llama-cpp-python for benchmark
            try:
                from llama_cpp import Llama
                start = time.time()
                llm = Llama(model_path=model.path, n_ctx=512, verbose=False)
                load_time = time.time() - start
                result["load_time_ms"] = round(load_time * 1000, 0)

                # Generate a short prompt to measure tokens/sec
                start = time.time()
                output = llm("Hello", max_tokens=10, echo=False)
                gen_time = time.time() - start
                tokens_generated = len(output.get("choices", [{}])[0].get("text", "").split())
                if gen_time > 0 and tokens_generated > 0:
                    result["tokens_per_sec"] = round(tokens_generated / gen_time, 1)
                else:
                    result["tokens_per_sec"] = 0.0

                # Memory usage estimate
                import os
                try:
                    import psutil
                    proc = psutil.Process()
                    result["memory_usage_mb"] = round(proc.memory_info().rss / (1024 * 1024), 1)
                except ImportError:
                    result["memory_usage_mb"] = int(model.size_mb * 1.3)

                del llm
            except ImportError:
                result["error"] = "llama-cpp-python not installed — cannot benchmark"
                result["load_time_ms"] = 0
                result["tokens_per_sec"] = 0
                result["memory_usage_mb"] = int(model.size_mb * 1.3)
        except Exception as e:
            result["error"] = str(e)

        # Save benchmark result
        state = self._load_full_state()
        benchmarks = state.get("benchmarks", {})
        benchmarks[model_name] = result
        state["benchmarks"] = benchmarks
        self._save_full_state(state)

        return result

    def get_benchmark(self, model_name: str) -> dict[str, Any] | None:
        """Get the last benchmark result for a model."""
        state = self._load_full_state()
        return state.get("benchmarks", {}).get(model_name)

    def get_all_benchmarks(self) -> dict[str, Any]:
        """Get all benchmark results."""
        state = self._load_full_state()
        return state.get("benchmarks", {})

    def download_model(self, repo_id: str, filename: str, progress_callback=None) -> bool:
        """
        Download a model from HuggingFace Hub (Advanced only).
        repo_id: e.g. "Qwen/Qwen2.5-7B-Instruct-GGUF"
        filename: e.g. "qwen2.5-7b-instruct-q4_k_m.gguf"
        """
        if not self._advanced_mode:
            return False
        try:
            from huggingface_hub import hf_hub_download
            # Download to the first available search dir
            target_dir = self.SEARCH_DIRS[0] if self.SEARCH_DIRS[0].exists() else self.SEARCH_DIRS[1]
            target_dir.mkdir(parents=True, exist_ok=True)

            local_path = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                local_dir=str(target_dir),
            )
            # Rescan to pick up the new model
            self.scan_models()
            return True
        except ImportError:
            return False
        except Exception:
            return False

    def get_download_candidates(self) -> list[dict[str, Any]]:
        """Return a curated list of recommended models for download."""
        return [
            {"repo_id": "Qwen/Qwen2.5-7B-Instruct-GGUF", "filename": "qwen2.5-7b-instruct-q4_k_m.gguf", "name": "Qwen2.5-7B Chat", "category": "chat", "size_gb": 4.4},
            {"repo_id": "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF", "filename": "qwen2.5-coder-7b-instruct-q4_k_m.gguf", "name": "Qwen2.5-Coder-7B", "category": "coder", "size_gb": 4.4},
            {"repo_id": "Qwen/Qwen2.5-Coder-3B-Instruct-GGUF", "filename": "qwen2.5-coder-3b-instruct-q4_k_m.gguf", "name": "Qwen2.5-Coder-3B", "category": "coder", "size_gb": 1.8},
            {"repo_id": "Qwen/Qwen2.5-0.5B-Instruct-GGUF", "filename": "qwen2.5-0.5b-instruct-q4_k_m.gguf", "name": "Qwen2.5-0.5B Small", "category": "small", "size_gb": 0.4},
            {"repo_id": "Qwen/Qwen2.5-VL-3B-Instruct-GGUF", "filename": "qwen2.5-vl-3b-instruct-q4_k_m.gguf", "name": "Qwen2.5-VL-3B Vision", "category": "vision", "size_gb": 1.8},
        ]

    def delete_model(self, model_name: str) -> bool:
        """Delete a model file from disk (Advanced only, with confirmation)."""
        if not self._advanced_mode:
            return False
        model = self.get_model(model_name)
        if not model:
            return False
        try:
            Path(model.path).unlink()
            # Remove from concurrent and active
            if model_name in self._concurrent_models:
                self._concurrent_models.remove(model_name)
            if self._active_model == model_name:
                self._active_model = ""
            self.scan_models()
            self._save_state()
            return True
        except Exception:
            return False

    def get_model_stats(self) -> dict[str, Any]:
        """Get comprehensive model statistics."""
        models = self.list_models()
        by_category: dict[str, int] = {}
        total_size = 0.0
        for m in models:
            cat = m.category.value
            by_category[cat] = by_category.get(cat, 0) + 1
            total_size += m.size_mb
        return {
            "total_models": len(models),
            "by_category": by_category,
            "total_size_gb": round(total_size / 1024, 2),
            "active_model": self._active_model,
            "concurrent_count": len(self._concurrent_models),
            "max_concurrent": self.get_max_concurrent(),
            "advanced_mode": self._advanced_mode,
            "routing_count": len(self.get_model_routing()),
            "benchmarks_count": len(self.get_all_benchmarks()),
        }

    # ─── Extended persistence ─────────────────────────────────────────

    def _load_full_state(self) -> dict[str, Any]:
        """Load the full state including routing and benchmarks."""
        p = self._state_path()
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}

    def _save_full_state(self, state: dict[str, Any]) -> None:
        """Save the full state."""
        p = self._state_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        # Merge with current state
        current = {
            "active_model": self._active_model,
            "concurrent_models": self._concurrent_models,
            "advanced_mode": self._advanced_mode,
        }
        current.update(state)
        p.write_text(json.dumps(current, indent=2), encoding="utf-8")
