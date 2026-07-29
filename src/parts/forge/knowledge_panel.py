# Copyright (c) 2026 Avery Logic Works - Command Nexus(TM) - All Rights Reserved
# Unauthorized copying, modification, or distribution is prohibited.
# --- IP Watermark ---
# ALW-CN-7F3A-2026-AVERYLOGICWORKS
# AVERY_LOGIC_WORKS_COMMAND_NEXUS_PROPRIETARY_v0.2.0

"""
Knowledge Panel — UI for the RAG Document Knowledge Base.

Drag and drop documents, manage indexed files, test retrieval,
and configure chunking settings.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QGridLayout, QFrame, QProgressBar, QCheckBox,
    QDialog, QDialogButtonBox, QMessageBox, QComboBox, QGroupBox,
    QSpinBox, QSizePolicy, QTextEdit, QFileDialog, QListWidget,
    QListWidgetItem, QSplitter, QTabWidget,
)
from PySide6.QtCore import Qt, Signal, QTimer, QMimeData
from PySide6.QtGui import QFont, QColor, QDragEnterEvent, QDropEvent

from ...core.rag_engine import RAGEngine, DocumentRecord, RetrievedChunk


class DocumentListWidget(QListWidget):
    """List widget showing indexed documents with enable/disable toggles."""

    document_remove_requested = Signal(str)  # doc_id
    document_toggle_requested = Signal(str, bool)  # doc_id, enabled

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setStyleSheet("""
            QListWidget {
                 border: 1px solid #30363d;
                border-radius: 6px; padding: 4px;
            }
            QListWidget::item {
                padding: 8px; border-bottom: 1px solid #21262d;
            }
            QListWidget::item:selected {
                background-color: #1f6feb;
            }
        """)
        self._docs: dict[str, DocumentRecord] = {}

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        # Forward to parent panel
        parent = self.parent()
        while parent and not hasattr(parent, '_on_files_dropped'):
            parent = parent.parent()
        if parent and hasattr(parent, '_on_files_dropped'):
            urls = event.mimeData().urls()
            files = [url.toLocalFile() for url in urls if url.isLocalFile()]
            if files:
                parent._on_files_dropped(files)
        event.acceptProposedAction()

    def refresh_documents(self, docs: list[DocumentRecord]):
        """Rebuild the document list."""
        self.clear()
        self._docs = {}
        for doc in docs:
            self._docs[doc.doc_id] = doc
            item = QListWidgetItem()
            widget = self._create_doc_widget(doc)
            item.setSizeHint(widget.sizeHint())
            self.addItem(item)
            self.setItemWidget(item, widget)

    def _create_doc_widget(self, doc: DocumentRecord) -> QWidget:
        widget = QFrame()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        # Enable/disable checkbox
        chk = QCheckBox()
        chk.setChecked(doc.enabled)
        chk.setStyleSheet("QCheckBox { spacing: 0; }")
        chk.toggled.connect(lambda checked, did=doc.doc_id: self.document_toggle_requested.emit(did, checked))
        layout.addWidget(chk)

        # Document info
        info = QVBoxLayout()
        name_label = QLabel(doc.filename)
        name_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #e6edf3;")
        info.addWidget(name_label)

        meta = f"{doc.chunk_count} chunks"
        if doc.date_added:
            meta += f"  |  Added: {doc.date_added[:10]}"
        meta_label = QLabel(meta)
        meta_label.setStyleSheet("font-size: 10px; color: #8b949e;")
        info.addWidget(meta_label)
        layout.addLayout(info, 1)

        # Remove button
        btn_remove = QPushButton("Remove")
        btn_remove.setStyleSheet("""
            QPushButton {
                background-color: #da3633; color: white;
                border-radius: 4px; padding: 2px 10px; font-size: 11px;
            }
            QPushButton:hover { background-color: #f85149; }
        """)
        btn_remove.clicked.connect(lambda _, did=doc.doc_id: self.document_remove_requested.emit(did))
        layout.addWidget(btn_remove)

        return widget


class KnowledgePanel(QWidget):
    """Main panel for the RAG Document Knowledge Base."""

    def __init__(self, rag_engine: RAGEngine, parent=None):
        super().__init__(parent)
        self._rag = rag_engine
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Title
        title = QLabel("Knowledge Base")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #e6edf3;")
        layout.addWidget(title)

        subtitle = QLabel("Drop documents here and your AI will use them when answering questions.")
        subtitle.setStyleSheet("font-size: 12px; color: #8b949e;")
        layout.addWidget(subtitle)

        # Supported formats
        formats_label = QLabel("Supported: PDF, TXT, MD, DOCX, CSV, RTF, PY, JS, JSON, XML, HTML, YAML")
        formats_label.setStyleSheet("font-size: 10px; color: #768390; font-style: italic;")
        layout.addWidget(formats_label)

        # Action buttons
        btn_row = QHBoxLayout()
        self._btn_add = QPushButton("+ Add Files")
        self._btn_add.setStyleSheet("""
            QPushButton {
                background-color: #238636; color: white;
                border-radius: 4px; padding: 6px 16px; font-weight: bold;
            }
            QPushButton:hover { background-color: #2ea043; }
        """)
        self._btn_add.clicked.connect(self._on_add_files)
        btn_row.addWidget(self._btn_add)

        self._btn_clear = QPushButton("Remove All")
        self._btn_clear.setStyleSheet("""
            QPushButton {
                background-color: #da3633; color: white;
                border-radius: 4px; padding: 6px 16px; font-weight: bold;
            }
            QPushButton:hover { background-color: #f85149; }
        """)
        self._btn_clear.clicked.connect(self._on_clear_all)
        btn_row.addWidget(self._btn_clear)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Stats bar
        self._lbl_stats = QLabel()
        self._lbl_stats.setStyleSheet("font-size: 11px; color: #8b949e; padding: 4px 0;")
        layout.addWidget(self._lbl_stats)

        # Document list
        self._doc_list = DocumentListWidget()
        self._doc_list.document_remove_requested.connect(self._on_remove_doc)
        self._doc_list.document_toggle_requested.connect(self._on_toggle_doc)
        layout.addWidget(self._doc_list, 1)

        # Test retrieval section
        test_group = QGroupBox("Test Retrieval")
        test_layout = QVBoxLayout(test_group)

        query_row = QHBoxLayout()
        self._txt_query = QLineEdit()
        self._txt_query.setPlaceholderText("Type a question to test knowledge retrieval...")
        self._txt_query.setStyleSheet("background-color: #0f172a; color: #e2e8f0; border: 1px solid #334155; padding: 6px; border-radius: 4px;")
        self._txt_query.returnPressed.connect(self._on_test_query)
        query_row.addWidget(self._txt_query, 1)

        self._btn_test = QPushButton("Search")
        self._btn_test.setStyleSheet("""
            QPushButton {
                background-color: #1f6feb; color: white;
                border-radius: 4px; padding: 6px 16px; font-weight: bold;
            }
            QPushButton:hover { background-color: #388bfd; }
        """)
        self._btn_test.clicked.connect(self._on_test_query)
        query_row.addWidget(self._btn_test)
        test_layout.addLayout(query_row)

        self._txt_results = QTextEdit()
        self._txt_results.setReadOnly(True)
        self._txt_results.setPlaceholderText("Retrieved knowledge chunks will appear here...")
        self._txt_results.setStyleSheet(" color: #e6edf3; border: 1px solid #30363d; border-radius: 4px; padding: 8px;")
        self._txt_results.setMaximumHeight(200)
        test_layout.addWidget(self._txt_results)

        layout.addWidget(test_group)

        # Settings section
        settings_group = QGroupBox("Settings")
        settings_layout = QHBoxLayout(settings_group)

        settings_layout.addWidget(QLabel("Chunk Size:"))
        self._spin_chunk = QSpinBox()
        self._spin_chunk.setRange(64, 2048)
        self._spin_chunk.setValue(512)
        self._spin_chunk.setStyleSheet("padding: 2px 6px;")
        self._spin_chunk.valueChanged.connect(self._on_chunk_size_changed)
        settings_layout.addWidget(self._spin_chunk)

        settings_layout.addWidget(QLabel("Overlap:"))
        self._spin_overlap = QSpinBox()
        self._spin_overlap.setRange(0, 1024)
        self._spin_overlap.setValue(64)
        self._spin_overlap.setStyleSheet("padding: 2px 6px;")
        self._spin_overlap.valueChanged.connect(self._on_overlap_changed)
        settings_layout.addWidget(self._spin_overlap)

        settings_layout.addWidget(QLabel("Top K:"))
        self._spin_topk = QSpinBox()
        self._spin_topk.setRange(1, 20)
        self._spin_topk.setValue(5)
        self._spin_topk.setStyleSheet("padding: 2px 6px;")
        self._spin_topk.valueChanged.connect(self._on_topk_changed)
        settings_layout.addWidget(self._spin_topk)

        settings_layout.addStretch()
        layout.addWidget(settings_group)

    def _refresh(self):
        """Refresh the document list and stats."""
        docs = self._rag.list_documents()
        self._doc_list.refresh_documents(docs)
        config = self._rag.get_config()
        self._lbl_stats.setText(
            f"Documents: {len(docs)}  |  Total chunks: {config['total_chunks']}  |  "
            f"Storage: {config['storage_mb']:.2f} MB  |  Backend: {config['embedder_backend']}"
        )

    def _on_add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Documents",
            "",
            "Documents (*.pdf *.txt *.md *.docx *.csv *.rtf *.log *.py *.js *.json *.xml *.html *.yaml *.yml);;All Files (*.*)"
        )
        if files:
            self._on_files_dropped(files)

    def _on_files_dropped(self, files: list[str]):
        """Handle dropped or selected files."""
        if not files:
            return
        progress = QProgressDialog("Ingesting documents...", "Cancel", 0, len(files), self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setStyleSheet(" color: #e6edf3;")
        progress.show()

        success_count = 0
        error_count = 0
        for i, file_path in enumerate(files):
            if progress.wasCanceled():
                break
            progress.setValue(i)
            try:
                doc = self._rag.ingest_file(file_path)
                if doc:
                    success_count += 1
                else:
                    error_count += 1
            except Exception as e:
                error_count += 1
                print(f"RAG ingest error for {file_path}: {e}")

        progress.setValue(len(files))
        progress.close()

        if success_count:
            self._refresh()
            QMessageBox.information(
                self, "Documents Added",
                f"Successfully indexed {success_count} document(s)."
                + (f"\n{error_count} file(s) failed." if error_count else "")
            )
        elif error_count:
            QMessageBox.warning(
                self, "Ingestion Failed",
                f"Could not index {error_count} file(s).\n"
                "Make sure the files are valid and in a supported format."
            )

    def _on_remove_doc(self, doc_id: str):
        reply = QMessageBox.question(
            self, "Remove Document",
            "Remove this document from the knowledge base? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._rag.remove_document(doc_id)
            self._refresh()

    def _on_toggle_doc(self, doc_id: str, enabled: bool):
        self._rag.set_document_enabled(doc_id, enabled)

    def _on_clear_all(self):
        docs = self._rag.list_documents()
        if not docs:
            return
        reply = QMessageBox.question(
            self, "Remove All Documents",
            f"Remove all {len(docs)} documents from the knowledge base? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            for doc in docs:
                self._rag.remove_document(doc.doc_id)
            self._refresh()

    def _on_test_query(self):
        query = self._txt_query.text().strip()
        if not query:
            return
        chunks = self._rag.retrieve(query)
        if not chunks:
            self._txt_results.setPlainText("No relevant knowledge found. Add documents or try a different query.")
            return
        parts: list[str] = []
        for i, chunk in enumerate(chunks, 1):
            parts.append(f"[{i}] From '{chunk.source_doc}' (score: {chunk.score:.3f}):")
            parts.append(chunk.text[:500])
            parts.append("")
        self._txt_results.setPlainText("\n".join(parts))

    def _on_chunk_size_changed(self, value: int):
        self._rag.set_chunk_size(value)

    def _on_overlap_changed(self, value: int):
        self._rag.set_chunk_overlap(value)

    def _on_topk_changed(self, value: int):
        self._rag.set_top_k(value)


# Need QLineEdit import
from PySide6.QtWidgets import QLineEdit


class KnowledgeDialog(QDialog):
    """Dialog wrapper for the Knowledge Base panel."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Knowledge Base — Command Nexus(TM)")
        self.setMinimumSize(700, 700)
        self.setStyleSheet(" color: #e6edf3;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        from ...core.rag_engine import RAGEngine
        self._rag = RAGEngine()
        self._panel = KnowledgePanel(self._rag, self)
        layout.addWidget(self._panel)

        btn_close = QPushButton("Close")
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #30363d; color: #e6edf3;
                border-radius: 4px; padding: 6px 20px; font-weight: bold;
            }
            QPushButton:hover { background-color: #424a53; }
        """)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignCenter)
