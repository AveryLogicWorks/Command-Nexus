import sys, os, faulthandler, traceback

# Enable faulthandler to catch segfaults
faulthandler.enable()

log_file = open("crash_log.txt", "w", encoding="utf-8")

def excepthook(exc_type, exc_value, exc_tb):
    msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    log_file.write(f"UNHANDLED EXCEPTION:\n{msg}\n")
    log_file.flush()
    print(f"UNHANDLED EXCEPTION: {msg}")

sys.excepthook = excepthook

# Also capture Qt messages
from PySide6.QtCore import qInstallMessageHandler, QtMsgType
def qt_message_handler(mode, context, message):
    log_file.write(f"QT MESSAGE [{mode}]: {message}\n")
    log_file.flush()
qInstallMessageHandler(qt_message_handler)

log_file.write("=== Command Nexus crash log started ===\n")
log_file.flush()

try:
    from src.main import CommandNexusApp
    app = CommandNexusApp()
    log_file.write("App created successfully. Starting event loop...\n")
    log_file.flush()
    exit_code = app.run()
    log_file.write(f"Event loop ended with code: {exit_code}\n")
    log_file.flush()
    sys.exit(exit_code)
except SystemExit as e:
    log_file.write(f"SystemExit: {e}\n")
    log_file.flush()
    sys.exit(e.code if hasattr(e, 'code') else 0)
except Exception as e:
    msg = "".join(traceback.format_exception(type(e), e, e.__traceback__))
    log_file.write(f"FATAL EXCEPTION:\n{msg}\n")
    log_file.flush()
    print(f"FATAL: {msg}")
    sys.exit(1)
