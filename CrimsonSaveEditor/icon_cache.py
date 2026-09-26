from __future__ import annotations

import logging
import os
import sys
from typing import Callable, Dict, Optional, Set

from PySide6.QtGui import QPixmap
from PySide6.QtCore import QSize, Qt

log = logging.getLogger(__name__)

ICON_SIZE = 32

def _get_local_icons_dir():
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(os.path.abspath(sys.executable))
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "icons_local")


class IconCache:

    def __init__(self, icon_urls_path: Optional[str] = None):
        self._pixmaps: Dict[int, QPixmap] = {}
        self._local_dir = _get_local_icons_dir()
        os.makedirs(self._local_dir, exist_ok=True)
        self._local_icon_keys: Set[int] = self._scan_local_icon_keys()

    def _scan_local_icon_keys(self) -> Set[int]:
        # One scandir pass instead of a per-row os.path.isfile() probe; the
        # item tables call has_icon()/get_pixmap() once per row on the UI thread.
        keys: Set[int] = set()
        try:
            with os.scandir(self._local_dir) as entries:
                for entry in entries:
                    if not entry.name.endswith('.webp'):
                        continue
                    try:
                        keys.add(int(entry.name[:-5]))
                    except ValueError:
                        continue
        except OSError as e:
            log.debug("Icon directory scan failed for %s: %s", self._local_dir, e)
        return keys

    def _local_path(self, item_key: int) -> str:
        return os.path.join(self._local_dir, f"{item_key}.webp")

    def _has_local_icon(self, item_key: int) -> bool:
        return item_key in self._local_icon_keys

    def has_icon(self, item_key: int) -> bool:
        return self._has_local_icon(item_key)

    def get_pixmap(self, item_key: int) -> Optional[QPixmap]:
        if item_key in self._pixmaps:
            return self._pixmaps[item_key]

        if not self._has_local_icon(item_key):
            return None

        local_path = self._local_path(item_key)
        px = QPixmap(local_path)
        if not px.isNull():
            self._pixmaps[item_key] = px
            return px

        self._local_icon_keys.discard(item_key)
        return None

    def request_icon(self, item_key: int, callback: Callable[[int, QPixmap], None]) -> None:
        if item_key in self._pixmaps:
            callback(item_key, self._pixmaps[item_key])
            return

        if self._has_local_icon(item_key):
            local_path = self._local_path(item_key)
            px = QPixmap(local_path)
            if not px.isNull():
                self._pixmaps[item_key] = px
                callback(item_key, px)
                return
            self._local_icon_keys.discard(item_key)

        # Icons are deliberately local-only in this build.
        return

    def preload_keys(self, keys: list, callback: Callable[[int, QPixmap], None]) -> None:
        for key in keys:
            if key not in self._pixmaps:
                self.request_icon(key, callback)

    def get_merc_pixmap(self, char_key: int) -> Optional[QPixmap]:
        cache_key = f"merc_{char_key}"
        if cache_key in self._pixmaps:
            return self._pixmaps[cache_key]

        merc_dir = os.path.join(os.path.dirname(self._local_dir), "icons_mercenary")
        local_path = os.path.join(merc_dir, f"{char_key}.webp")
        if os.path.isfile(local_path):
            px = QPixmap(local_path)
            if not px.isNull():
                self._pixmaps[cache_key] = px
                return px
        return None

    @property
    def coverage(self) -> int:
        return len(self._local_icon_keys)
