#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EDITOR_DIR="$ROOT/CrimsonSaveEditor"
VENV="$ROOT/.venv-py311"
PYTHON_BIN="${PYTHON_BIN:-}"
LOG_DIR="$HOME/crimson-desert-saves"
RUN_LOG="$LOG_DIR/editor-watchdog-run.log"
DIST_DIR="$EDITOR_DIR/dist"
BUILD_DIR="$EDITOR_DIR/build/hermes-build-nosplash"
APP="$DIST_DIR/CrimsonSaveEditorStandalone"

mkdir -p "$LOG_DIR"

if [[ -z "$PYTHON_BIN" ]]; then
  for candidate in "$HOME/.local/bin/python3.11" python3.11 python3.12 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
      version="$($candidate - <<'PY'
import sys
print(f"{sys.version_info.major}.{sys.version_info.minor}")
PY
)"
      case "$version" in
        3.11|3.12|3.13)
          PYTHON_BIN="$(command -v "$candidate")"
          break
          ;;
      esac
    fi
  done
fi

if [[ -z "$PYTHON_BIN" ]]; then
  echo "Could not find Python 3.11-3.13 for PySide6==6.8.3. Set PYTHON_BIN=/path/to/python3.11" >&2
  exit 1
fi

if [[ ! -x "$VENV/bin/python" ]]; then
  "$PYTHON_BIN" -m venv "$VENV"
fi

"$VENV/bin/python" -m pip install --upgrade pip
"$VENV/bin/python" -m pip install PySide6==6.8.3 lz4 cryptography pyinstaller Pillow

SPEC="$(mktemp /tmp/hermes-verify-build-CrimsonSaveEditor-XXXXXX.spec)"
cleanup() {
  rm -f "$SPEC"
}
trap cleanup EXIT

cat > "$SPEC" <<PY
from pathlib import Path
base = Path(r"$EDITOR_DIR")
a = Analysis(
    [str(base / 'main.py')],
    pathex=[str(base)],
    binaries=[],
    datas=[
        (str(base / 'parc_parser.dll'), '.'),
        (str(base / 'item_names.json'), '.'),
        (str(base / 'store_names.json'), '.'),
        (str(base / 'item_templates.json'), '.'),
        (str(base / 'master_templates.json'), '.'),
        (str(base / 'item_limits.json'), '.'),
        (str(base / 'item_category_map.json'), '.'),
        (str(base / 'max_enchant_map.json'), '.'),
        (str(base / 'waypoint_templates_community.json'), '.'),
        (str(base / 'abyss_gimmick_templates.json'), '.'),
        (str(base / 'knowledge_keys_all.json'), '.'),
        (str(base / 'community_knowledge_keys.json'), '.'),
        (str(base / 'quest_names.json'), '.'),
        (str(base / 'quest_database.json'), '.'),
        (str(base / 'mission_names.json'), '.'),
        (str(base / 'quest_stage_map.json'), '.'),
        (str(base / 'stage_names.json'), '.'),
        (str(base / 'gimmick_respawn_timers.json'), '.'),
        (str(base / 'quest_chains.json'), '.'),
        (str(base / 'dye_slot_counts.json'), '.'),
        (str(base / 'buff_skill_descriptions.json'), '.'),
        (str(base / 'game_map.json'), '.'),
        (str(base / 'localizationstring_eng_items.tsv'), '.'),
        (str(base / 'editor_version_standalone.json'), '.'),
        (str(base / 'locale'), 'locale'),
        (str(base / 'knowledge_packs'), 'knowledge_packs'),
    ],
    hiddenimports=[
        'lz4', 'lz4.block', 'cryptography',
        'cryptography.hazmat.primitives.ciphers',
        'cryptography.hazmat.primitives.ciphers.algorithms',
        'iteminfo_parser', 'parc_inserter3', 'parc_inserter2', 'parc_serializer',
        'save_parser', 'save_pet_rename', 'quest_deep_parser', 'questinfo_parser',
        'item_template_db', 'ben_save_decrypt',
    ],
    hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=['PyQt5', 'pyi_splash'],
    noarchive=False, optimize=0,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='CrimsonSaveEditorStandalone',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    icon=str(base / 'app_icon.ico'),
    codesign_identity=None,
    entitlements_file=None,
)
PY

"$VENV/bin/python" -m PyInstaller "$SPEC" --noconfirm --clean --distpath "$DIST_DIR" --workpath "$BUILD_DIR"
chmod +x "$APP"

echo "Built: $APP"
echo "Run log: $RUN_LOG"
echo "Editor log: $LOG_DIR/editor.log"
echo "Launching with CRIMSON_HANG_WATCHDOG=1..."

CRIMSON_HANG_WATCHDOG=1 "$APP" "$@" >"$RUN_LOG" 2>&1 &
pid=$!
echo "PID: $pid"
echo "Tail logs with: tail -f '$LOG_DIR/editor.log' '$RUN_LOG'"
