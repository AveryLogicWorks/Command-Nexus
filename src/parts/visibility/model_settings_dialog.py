"""
AI / Intelligence model settings dialog.

Lets the user choose the model backend and enter credentials without touching
environment variables:
- Offline (Ollama): a local model that runs on the user's machine and works
  without internet. It "learns with the user" via each AI's Knowledge/Memory,
  which Command Nexus injects into every prompt.
- Cloud (OpenAI): full reasoning using the user's own API key.
- Auto: try the offline model first, fall back to cloud.

Settings persist via SettingsManager (~/CommandNexus/config.json) and are read
by NexusAIRuntime on its next run.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QCheckBox, QMessageBox,
)

from ...core.settings_manager import SettingsManager

_BACKENDS = [
    ("auto", "Auto — offline first, then cloud"),
    ("offline", "Offline only (Ollama, no internet)"),
    ("cloud", "Cloud only (OpenAI)"),
]


class ModelSettingsDialog(QDialog):
    """Configure the AI model backend and credentials."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Command Nexus™ — AI / Intelligence Model Settings")
        self.setMinimumWidth(560)
        self._mgr = SettingsManager()
        self._settings = self._mgr.get()
        self._build_ui()
        self._apply_theme()
        self._load_values()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = QLabel("AI / Intelligence Model")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #58a6ff;")
        layout.addWidget(title)

        blurb = QLabel(
            "Choose how your AIs think. Offline uses a local model (Ollama) that "
            "works without internet and learns from each AI's Knowledge. Cloud uses "
            "OpenAI with your own key. Your AIs always inject their Knowledge and "
            "memory into every request, so they adapt to you on either backend."
        )
        blurb.setWordWrap(True)
        blurb.setStyleSheet("color: #8b949e;")
        layout.addWidget(blurb)

        form = QFormLayout()
        form.setSpacing(8)

        self._backend = QComboBox()
        for value, label in _BACKENDS:
            self._backend.addItem(label, value)
        form.addRow("Backend:", self._backend)

        self._openai_key = QLineEdit()
        self._openai_key.setEchoMode(QLineEdit.EchoMode.Password)
        self._openai_key.setPlaceholderText("sk-... (stored locally, never shared)")
        self._show_key = QCheckBox("Show")
        self._show_key.toggled.connect(
            lambda on: self._openai_key.setEchoMode(
                QLineEdit.EchoMode.Normal if on else QLineEdit.EchoMode.Password
            )
        )
        key_row = QHBoxLayout()
        key_row.addWidget(self._openai_key, stretch=1)
        key_row.addWidget(self._show_key)
        form.addRow("OpenAI API key:", self._wrap(key_row))

        self._openai_model = QLineEdit()
        self._openai_model.setPlaceholderText("gpt-4o-mini")
        form.addRow("OpenAI model:", self._openai_model)

        self._ollama_url = QLineEdit()
        self._ollama_url.setPlaceholderText("http://127.0.0.1:11434")
        form.addRow("Ollama URL:", self._ollama_url)

        self._ollama_model = QLineEdit()
        self._ollama_model.setPlaceholderText("llama3.2:1b")
        form.addRow("Ollama model:", self._ollama_model)

        layout.addLayout(form)

        self._status = QLabel("")
        self._status.setWordWrap(True)
        self._status.setStyleSheet("color: #8b949e; font-style: italic;")
        layout.addWidget(self._status)

        btn_row = QHBoxLayout()
        self._test_btn = QPushButton("Test Connection")
        self._test_btn.clicked.connect(self._test_connection)
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(self._test_btn)
        btn_row.addStretch(1)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _wrap(self, inner_layout):
        from PyQt6.QtWidgets import QWidget
        w = QWidget()
        w.setLayout(inner_layout)
        return w

    def _load_values(self):
        s = self._settings
        idx = max(0, self._backend.findData(getattr(s, "model_backend", "auto")))
        self._backend.setCurrentIndex(idx)
        self._openai_key.setText(getattr(s, "openai_api_key", "") or "")
        self._openai_model.setText(getattr(s, "openai_model", "") or "gpt-4o-mini")
        self._ollama_url.setText(getattr(s, "ollama_url", "") or "http://127.0.0.1:11434")
        self._ollama_model.setText(getattr(s, "ollama_model", "") or "llama3.2:1b")

    def _save(self):
        self._mgr.update(
            model_backend=self._backend.currentData(),
            openai_api_key=self._openai_key.text().strip(),
            openai_model=self._openai_model.text().strip() or "gpt-4o-mini",
            ollama_url=self._ollama_url.text().strip() or "http://127.0.0.1:11434",
            ollama_model=self._ollama_model.text().strip() or "llama3.2:1b",
        )
        QMessageBox.information(
            self, "Saved",
            "Model settings saved. New AI requests will use the selected backend.",
        )
        self.accept()

    def _test_connection(self):
        """Run a tiny request through the runtime using the currently entered values."""
        self._status.setText("Testing...")
        self._test_btn.setEnabled(False)
        try:
            from ...core.nexus_ai_runtime import NexusAIRuntime
            rt = NexusAIRuntime()
            rt._manual_config = True  # test the values entered here, not the saved ones
            rt.model_backend = self._backend.currentData()
            rt.openai_api_key = self._openai_key.text().strip() or rt.openai_api_key
            rt.openai_model = self._openai_model.text().strip() or rt.openai_model
            rt.ollama_url = (self._ollama_url.text().strip() or rt.ollama_url).rstrip("/")
            rt.ollama_model = self._ollama_model.text().strip() or rt.ollama_model
            reply = rt._call_model("Reply with exactly: NEXUS_OK")
            if reply and "error" not in reply.lower():
                self._status.setText(f"Connection OK — model replied: {reply[:120]}")
            elif reply:
                self._status.setText(f"Backend responded with an error: {reply[:160]}")
            else:
                self._status.setText(
                    "No model reachable. For Offline, install/run Ollama and pull the model. "
                    "For Cloud, check your OpenAI key."
                )
        except Exception as exc:
            self._status.setText(f"Test failed: {exc}")
        finally:
            self._test_btn.setEnabled(True)

    def _apply_theme(self):
        self.setStyleSheet(
            "QDialog { background-color: #0d1117; color: #c9d1d9; }"
            "QLabel { color: #c9d1d9; }"
            "QLineEdit, QComboBox { background-color: #161b22; color: #c9d1d9;"
            " border: 1px solid #30363d; padding: 5px; border-radius: 4px; }"
            "QPushButton { background-color: #21262d; color: #c9d1d9;"
            " border: 1px solid #30363d; padding: 6px 14px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #30363d; }"
            "QCheckBox { color: #8b949e; }"
        )
