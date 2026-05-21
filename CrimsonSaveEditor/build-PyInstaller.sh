#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

export PYTHONPATH="$(cd .. && pwd)/CrimsonGameMods:${PYTHONPATH:-}"

echo "Clearing caches..."
find . -type d -name '__pycache__' -prune -exec rm -rf '{}' +
rm -rf build dist

echo "Building with PyInstaller..."
python3 -m PyInstaller CrimsonSaveEditor.spec --noconfirm

echo
echo "Done. Output: dist/CrimsonSaveEditorStandalone"
