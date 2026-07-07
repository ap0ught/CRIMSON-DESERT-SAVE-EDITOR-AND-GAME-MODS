from __future__ import annotations

import logging
import os
import sys
import threading
from typing import Callable, Dict, Optional, Set
from urllib.request import urlopen, Request

from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import QSize, Qt

log = logging.getLogger(__name__)

ICON_SIZE = 32

_GITHUB_ICON_BASE = "https://raw.githubusercontent.com/NattKh/CRIMSON-DESERT-SAVE-EDITOR/main/icons_local"


def _get_local_icons_dir():
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(os.path.abspath(sys.executable))
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "icons_local")


class IconCache:

    def __init__(self, icon_urls_path: Optional[str] = None):
        self._pixmaps: Dict[int, QPixmap] = {}
        self._pending: set = set()
        self._lock = threading.Lock()
        self._local_dir = _get_local_icons_dir()
        os.makedirs(self._local_dir, exist_ok=True)
        self._local_icon_keys: Set[int] = self._scan_local_icon_keys()

    def _scan_local_icon_keys(self) -> Set[int]:
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

    def _mark_local_icon(self, item_key: int) -> None:
        self._local_icon_keys.add(item_key)

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

    def request_icon(self, item_key: int, callback: Callable[[int, Optional[QPixmap]], None]) -> None:
        if item_key in self._pixmaps:
            callback(item_key, self._pixmaps[item_key])
            return

        local_path = self._local_path(item_key)
        if self._has_local_icon(item_key):
            px = QPixmap(local_path)
            if not px.isNull():
                self._pixmaps[item_key] = px
                callback(item_key, px)
                return
            self._local_icon_keys.discard(item_key)

        with self._lock:
            if item_key in self._pending:
                return
            self._pending.add(item_key)

        url = f"{_GITHUB_ICON_BASE}/{item_key}.webp"
        thread = threading.Thread(
            target=self._download_icon,
            args=(item_key, url, callback),
            daemon=True,
        )
        thread.start()

    def download_icon_sync(self, item_key: int) -> Optional[QPixmap]:
        if item_key in self._pixmaps:
            return self._pixmaps[item_key]

        local_path = self._local_path(item_key)
        if self._has_local_icon(item_key):
            px = QPixmap(local_path)
            if not px.isNull():
                self._pixmaps[item_key] = px
                return px
            self._local_icon_keys.discard(item_key)

        url = f"{_GITHUB_ICON_BASE}/{item_key}.webp"
        try:
            req = Request(url, headers={"User-Agent": "CrimsonSaveEditor"})
            with urlopen(req, timeout=15) as resp:
                img_data = resp.read()

            with open(local_path, 'wb') as f:
                f.write(img_data)
            self._mark_local_icon(item_key)

            px = QPixmap(local_path)
            if not px.isNull():
                self._pixmaps[item_key] = px
                return px
        except Exception as e:
            log.debug("Icon download failed for key %d: %s", item_key, e)

        return None

    def _download_icon(self, item_key: int, url: str, callback) -> None:
        local_path = self._local_path(item_key)

        if self._has_local_icon(item_key):
            try:
                px = QPixmap(local_path)
                if not px.isNull():
                    self._pixmaps[item_key] = px
                    callback(item_key, px)
            except Exception:
                pass
            finally:
                with self._lock:
                    self._pending.discard(item_key)
            return

        try:
            req = Request(url, headers={"User-Agent": "CrimsonSaveEditor"})
            with urlopen(req, timeout=15) as resp:
                img_data = resp.read()

            if not img_data or len(img_data) < 100:
                return

            with open(local_path, 'wb') as f:
                f.write(img_data)
            self._mark_local_icon(item_key)

            qimg = QImage()
            qimg.loadFromData(img_data)
            if qimg.isNull():
                return

            px = QPixmap.fromImage(qimg)
            self._pixmaps[item_key] = px
            callback(item_key, px)

        except Exception as e:
            log.debug("Icon download failed for key %d: %s", item_key, e)
        finally:
            with self._lock:
                self._pending.discard(item_key)

    def preload_keys(self, keys: list, callback: Callable[[int, Optional[QPixmap]], None]) -> None:
        for key in keys:
            if key not in self._pixmaps:
                self.request_icon(key, callback)

    def bulk_download_all(self, progress_callback=None) -> dict:
        from urllib.request import urlopen, Request
        import json as _json

        stats = {'downloaded': 0, 'skipped': 0, 'errors': 0}

        folders = [
            ("icons_local", self._local_dir),
            ("icons_mercenary", os.path.join(os.path.dirname(self._local_dir), "icons_mercenary")),
        ]

        for folder_name, local_dir in folders:
            os.makedirs(local_dir, exist_ok=True)
            base_url = f"https://raw.githubusercontent.com/NattKh/CRIMSON-DESERT-SAVE-EDITOR/main/{folder_name}"

            api_url = f"https://api.github.com/repos/NattKh/CRIMSON-DESERT-SAVE-EDITOR/contents/{folder_name}"
            try:
                req = Request(api_url, headers={"User-Agent": "CrimsonSaveEditor"})
                with urlopen(req, timeout=30) as resp:
                    files = _json.loads(resp.read())
            except Exception as e:
                log.warning("Failed to list %s from GitHub: %s", folder_name, e)
                stats['errors'] += 1
                continue

            for i, entry in enumerate(files):
                fname = entry.get('name', '')
                if not fname.endswith('.webp'):
                    continue

                local_path = os.path.join(local_dir, fname)
                if os.path.isfile(local_path):
                    if local_dir == self._local_dir:
                        try:
                            self._mark_local_icon(int(fname[:-5]))
                        except ValueError:
                            pass
                    stats['skipped'] += 1
                    continue

                try:
                    dl_url = f"{base_url}/{fname}"
                    req = Request(dl_url, headers={"User-Agent": "CrimsonSaveEditor"})
                    with urlopen(req, timeout=15) as resp:
                        data = resp.read()
                    if data and len(data) > 100:
                        with open(local_path, 'wb') as f:
                            f.write(data)
                        if local_dir == self._local_dir:
                            try:
                                self._mark_local_icon(int(fname[:-5]))
                            except ValueError:
                                pass
                        stats['downloaded'] += 1
                    else:
                        stats['errors'] += 1
                except Exception:
                    stats['errors'] += 1

                if progress_callback and (stats['downloaded'] + stats['errors']) % 50 == 0:
                    progress_callback(folder_name, stats['downloaded'], stats['skipped'],
                                      stats['errors'], len(files))

        return stats

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
