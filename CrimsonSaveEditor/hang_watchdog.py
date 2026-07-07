"""
Hang/freeze watchdog for the Qt main thread.

How it works
------------
A QTimer fires on the Qt event loop every HEARTBEAT_MS and updates a
timestamp. A plain (non-Qt) background thread wakes up every
CHECK_INTERVAL_S and checks how long it's been since the last heartbeat.
If the event loop hasn't beat in longer than STALL_THRESHOLD_S, the GUI is
blocked (something running on the main thread -- a slow scan, a network
call, a modal dialog, whatever) and we dump every thread's current Python
stack to the log. That tells us exactly which line the UI was stuck on.

Usage (in main.py, after creating QApplication):

    from hang_watchdog import HangWatchdog
    watchdog = HangWatchdog()
    watchdog.start()

Nothing else required -- it self-registers a QTimer on whichever thread
starts it (must be the Qt main thread) and spins up one daemon thread.
"""
from __future__ import annotations

import faulthandler
import logging
import sys
import threading
import time

from PySide6.QtCore import QTimer

log = logging.getLogger(__name__)

HEARTBEAT_MS = 500          # how often the Qt timer beats
CHECK_INTERVAL_S = 1.0      # how often the watchdog thread checks
STALL_THRESHOLD_S = 3.0     # how long without a beat counts as "unresponsive"
RECOVERY_LOG_LEVEL = logging.WARNING


class HangWatchdog:
    def __init__(
        self,
        stall_threshold_s: float = STALL_THRESHOLD_S,
        heartbeat_ms: int = HEARTBEAT_MS,
        check_interval_s: float = CHECK_INTERVAL_S,
    ) -> None:
        self._stall_threshold_s = stall_threshold_s
        self._heartbeat_ms = heartbeat_ms
        self._check_interval_s = check_interval_s
        self._last_beat = time.monotonic()
        self._stalled = False
        self._stall_started_at: float | None = None
        self._timer: QTimer | None = None
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Call from the Qt main thread after QApplication is constructed."""
        self._timer = QTimer()
        self._timer.setInterval(self._heartbeat_ms)
        self._timer.timeout.connect(self._beat)
        self._timer.start()

        self._thread = threading.Thread(
            target=self._watch_loop, name="hang-watchdog", daemon=True
        )
        self._thread.start()
        log.info(
            "HangWatchdog started (heartbeat=%dms, stall_threshold=%.1fs)",
            self._heartbeat_ms, self._stall_threshold_s,
        )

    def stop(self) -> None:
        self._stop_event.set()
        if self._timer is not None:
            self._timer.stop()

    def _beat(self) -> None:
        now = time.monotonic()
        if self._stalled:
            stall_duration = now - (self._stall_started_at or now)
            log.log(
                RECOVERY_LOG_LEVEL,
                "UI RECOVERED after %.1fs unresponsive", stall_duration,
            )
            self._stalled = False
            self._stall_started_at = None
        self._last_beat = now

    def _watch_loop(self) -> None:
        while not self._stop_event.wait(self._check_interval_s):
            now = time.monotonic()
            gap = now - self._last_beat
            if gap >= self._stall_threshold_s and not self._stalled:
                self._stalled = True
                self._stall_started_at = self._last_beat
                self._dump_hang(gap)

    def _dump_hang(self, gap: float) -> None:
        log.critical(
            "UI UNRESPONSIVE for %.1fs (no heartbeat) -- dumping all thread stacks:",
            gap,
        )
        # faulthandler.dump_traceback() needs a real fileno(), so we can't
        # hand it a StringIO/logging stream directly -- write to a scratch
        # file, then read it back into the logger.
        import os
        import tempfile
        fd, path = tempfile.mkstemp(prefix="hang-watchdog-", suffix=".txt")
        try:
            with os.fdopen(fd, "w") as f:
                faulthandler.dump_traceback(file=f, all_threads=True)
            with open(path) as f:
                dump_text = f.read()
        finally:
            try:
                os.remove(path)
            except OSError:
                pass
        for line in dump_text.splitlines():
            log.critical("  %s", line)
