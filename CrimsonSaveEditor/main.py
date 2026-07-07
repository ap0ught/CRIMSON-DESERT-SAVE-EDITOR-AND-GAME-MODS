import sys
import os
import logging
from logging.handlers import RotatingFileHandler


def _splash(text: str) -> None:
    try:
        import pyi_splash
        pyi_splash.update_text(text)
    except Exception:
        pass


def _splash_close() -> None:
    try:
        import pyi_splash
        pyi_splash.close()
    except Exception:
        pass


_splash("Starting up...")

_log_dir = os.path.expanduser("~/crimson-desert-saves")
os.makedirs(_log_dir, exist_ok=True)
_log_file = os.path.join(_log_dir, "editor.log")

_log_formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

_stream_handler = logging.StreamHandler(sys.stdout)
_stream_handler.setFormatter(_log_formatter)

_file_handler = RotatingFileHandler(
    _log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
)
_file_handler.setFormatter(_log_formatter)

logging.basicConfig(level=logging.INFO, handlers=[_stream_handler, _file_handler])
logging.getLogger(__name__).info("Logging to %s", _log_file)

_splash("Loading Qt framework...")
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

_splash("Loading editor modules...")
from gui import MainWindow


def main() -> None:
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    from updater import APP_VERSION
    app.setApplicationName("Crimson Desert Save Editor")
    app.setApplicationVersion(APP_VERSION)

    watchdog = None
    if os.environ.get("CRIMSON_HANG_WATCHDOG") == "1":
        from hang_watchdog import HangWatchdog
        watchdog = HangWatchdog()
        watchdog.start()

    font = QFont("Consolas", 10)
    font.setStyleHint(QFont.Monospace)
    app.setFont(font)

    _splash("Building main window...")
    window = MainWindow()
    _splash_close()
    window.show()

    if len(sys.argv) > 1:
        path = sys.argv[1]
        if os.path.isfile(path):
            if path.lower().endswith(".save"):
                window._load_save(path)
            elif path.lower().endswith(".bin"):
                from save_crypto import load_raw_stream
                try:
                    window._save_data = load_raw_stream(path)
                    window._loaded_path = path
                    window._scan_and_populate()
                    window._update_status(f"Loaded: {os.path.basename(path)}")
                except Exception as e:
                    print(f"Error loading {path}: {e}")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
