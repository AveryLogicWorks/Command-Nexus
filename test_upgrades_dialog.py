#!/usr/bin/env python3
"""Test the Upgrades dialog in isolation to capture crashes."""
import sys
import faulthandler
import traceback

faulthandler.enable()

def excepthook(exc_type, exc_value, exc_tb):
    msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print(f"UNHANDLED EXCEPTION:\n{msg}", file=sys.stderr, flush=True)

sys.excepthook = excepthook

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import qInstallMessageHandler, QtMsgType

def qt_message_handler(mode, context, message):
    print(f"QT MESSAGE [{mode}]: {message}", flush=True)

qInstallMessageHandler(qt_message_handler)

app = QApplication(sys.argv)
print("App created", flush=True)

try:
    from src.parts.visibility.upgrades_panel import UpgradesDialog
    print("UpgradesDialog imported", flush=True)

    dlg = UpgradesDialog(None)
    print("Dialog created", flush=True)

    dlg.show()
    print("Dialog shown, entering event loop...", flush=True)

    # Auto-close after 3 seconds for testing
    from PySide6.QtCore import QTimer
    QTimer.singleShot(3000, dlg.close)

    app.exec()
    print("Event loop ended normally", flush=True)

except Exception as e:
    msg = "".join(traceback.format_exception(type(e), e, e.__traceback__))
    print(f"FATAL EXCEPTION:\n{msg}", file=sys.stderr, flush=True)
    sys.exit(1)
