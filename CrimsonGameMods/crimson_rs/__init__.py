"""crimson_rs compatibility shim for the packaged Nuitka build.

Prefer the native parser backend for the current platform so we do not
accidentally bind to the empty `dmm_parser` namespace package in this checkout.
"""

from __future__ import annotations

import importlib.util
import platform
from pathlib import Path

from .enums import Compression, Crypto, Language


def _load_extension(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load backend from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_here = Path(__file__).resolve().parent
_backend_candidates = []
if platform.system().lower().startswith("win"):
    _backend_candidates.extend([
        ("dmm_parser", _here.parent / "dmm_parser" / "dmm_parser.pyd"),
        ("crimson_rs", _here / "crimson_rs.pyd"),
    ])
else:
    _backend_candidates.extend([
        ("dmm_parser", _here.parent / "dmm_parser" / "dmm_parser.abi3.so"),
        ("dmm_parser", _here.parent / "dmm_parser" / "dmm_parser.so"),
    ])

_backend = None
for _module_name, _candidate in _backend_candidates:
    if not _candidate.is_file():
        continue
    try:
        _backend = _load_extension(_module_name, _candidate)
        break
    except ImportError:
        continue

if _backend is None:
    raise ImportError(
        "No native backend found for this platform; expected dmm_parser or "
        "crimson_rs extension modules to be present."
    )

for _name in dir(_backend):
    if _name.startswith("__"):
        continue
    globals()[_name] = getattr(_backend, _name)

del _backend, _here, _backend_candidates, _load_extension
