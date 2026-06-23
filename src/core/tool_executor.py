from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .settings_manager import SettingsManager


@dataclass
class ToolResult:
    ok: bool
    action: str
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    error: str = ""


class ToolExecutor:
    """
    Honest local tool executor for file and shell operations.

    All destructive operations are gated by the caller (usually CommandRouter /
    ApprovalGate). The executor itself refuses to leave the configured workspace
    unless explicitly allowed.
    """

    def __init__(self, settings: SettingsManager | None = None, allow_outside_workspace: bool = False):
        self._settings = settings or SettingsManager()
        # Do not force initialize here; the caller may have already configured
        # in-memory settings. SettingsManager.get() will lazily initialize if needed.
        self._workspace = Path(self._settings.get().workspace_path or os.getcwd()).resolve()
        self._allow_outside_workspace = allow_outside_workspace

    def _safe_path(self, path: str | Path) -> Path:
        raw = Path(path)
        if not raw.is_absolute():
            raw = self._workspace / raw
        target = raw.expanduser().resolve()
        if not self._allow_outside_workspace:
            try:
                target.relative_to(self._workspace)
            except ValueError as exc:
                raise PermissionError(
                    f"Path {target} is outside workspace {self._workspace}. "
                    "Enable allow_outside_workspace to override."
                ) from exc
        return target

    def read_file(self, path: str | Path, *, offset: int = 0, limit: int | None = 5000) -> ToolResult:
        try:
            target = self._safe_path(path)
            if not target.exists():
                return ToolResult(False, "read_file", f"File not found: {target}")
            text = target.read_text(encoding="utf-8", errors="replace")
            if offset:
                text = text[offset:]
            if limit is not None and len(text) > limit:
                text = text[:limit] + "\n... [truncated]"
            return ToolResult(True, "read_file", f"Read {target}", {"path": str(target), "content": text})
        except Exception as e:
            return ToolResult(False, "read_file", f"Failed to read {path}: {e}", error=str(e))

    def write_file(self, path: str | Path, content: str) -> ToolResult:
        try:
            target = self._safe_path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            return ToolResult(True, "write_file", f"Wrote {target}", {"path": str(target), "bytes": len(content)})
        except Exception as e:
            return ToolResult(False, "write_file", f"Failed to write {path}: {e}", error=str(e))

    def list_dir(self, path: str | Path = ".") -> ToolResult:
        try:
            target = self._safe_path(path)
            if not target.is_dir():
                return ToolResult(False, "list_dir", f"Not a directory: {target}")
            entries = []
            for item in sorted(target.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
                entries.append({
                    "name": item.name,
                    "type": "file" if item.is_file() else "dir" if item.is_dir() else "other",
                    "size": item.stat().st_size if item.is_file() else None,
                })
            return ToolResult(True, "list_dir", f"Listed {len(entries)} entries in {target}", {"path": str(target), "entries": entries})
        except Exception as e:
            return ToolResult(False, "list_dir", f"Failed to list {path}: {e}", error=str(e))

    def move_file(self, src: str | Path, dst: str | Path) -> ToolResult:
        try:
            source = self._safe_path(src)
            destination = self._safe_path(dst)
            if not source.exists():
                return ToolResult(False, "move_file", f"Source not found: {source}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(destination))
            return ToolResult(True, "move_file", f"Moved {source} -> {destination}", {"src": str(source), "dst": str(destination)})
        except Exception as e:
            return ToolResult(False, "move_file", f"Failed to move {src} -> {dst}: {e}", error=str(e))

    def delete_file(self, path: str | Path) -> ToolResult:
        try:
            target = self._safe_path(path)
            if target.is_dir():
                shutil.rmtree(target)
            elif target.exists():
                target.unlink()
            else:
                return ToolResult(False, "delete_file", f"Not found: {target}")
            return ToolResult(True, "delete_file", f"Deleted {target}", {"path": str(target)})
        except Exception as e:
            return ToolResult(False, "delete_file", f"Failed to delete {path}: {e}", error=str(e))

    def run_shell(self, command: str, *, cwd: str | Path | None = None, timeout: int = 30) -> ToolResult:
        try:
            workdir = self._safe_path(cwd) if cwd else self._workspace
            proc = subprocess.run(
                command,
                shell=True,
                cwd=str(workdir),
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return ToolResult(
                ok=proc.returncode == 0,
                action="run_shell",
                message=f"Shell command finished (exit {proc.returncode})",
                data={
                    "command": command,
                    "cwd": str(workdir),
                    "returncode": proc.returncode,
                    "stdout": proc.stdout,
                    "stderr": proc.stderr,
                },
            )
        except Exception as e:
            return ToolResult(False, "run_shell", f"Failed to run shell command: {e}", error=str(e))
