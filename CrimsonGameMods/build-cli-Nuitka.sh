#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

repo_root="$(pwd)"
quest_packs_dir="$repo_root/../quest_packs"
qt_libs="$(python3 - <<'PY'
import glob
import os
import site

paths = site.getsitepackages() + [site.getusersitepackages()]
for base in paths:
    if not base:
        continue
    pyside = sorted(glob.glob(os.path.join(base, 'PySide6', 'libpyside6*.so*')))
    shiboken = sorted(glob.glob(os.path.join(base, 'shiboken6', 'libshiboken6*.so*')))
    if pyside and shiboken:
        print(pyside[0])
        print(shiboken[0])
        break
else:
    raise SystemExit('Unable to locate PySide6/shiboken6 shared libraries')
PY
)"

read -r pyside_lib shiboken_lib <<<"$qt_libs"

echo "Clearing caches..."
find . -type d -name '__pycache__' -prune -exec rm -rf '{}' +
rm -rf build-output

extra_backend_args=()
case "$(uname -s)" in
  Linux)
    if [[ -f dmm_parser/dmm_parser.abi3.so ]]; then
      extra_backend_args+=(--include-data-file=dmm_parser/dmm_parser.abi3.so=dmm_parser/dmm_parser.abi3.so)
    fi
    ;;
  MINGW*|MSYS*|CYGWIN*|Windows_NT)
    if [[ -f dmm_parser/dmm_parser.pyd ]]; then
      extra_backend_args+=(--include-data-file=dmm_parser/dmm_parser.pyd=dmm_parser/dmm_parser.pyd)
    fi
    ;;
esac

echo "Building with Nuitka..."
python3 -m nuitka \
  --standalone \
  --assume-yes-for-downloads \
  --enable-plugin=pyside6 \
  --include-package=crimson_rs \
  --output-dir=build-nuitka-cli  \
  --output-filename=CrimsonCLI \
  --include-data-dir=data=data \
  --include-data-dir=locale=locale \
  --include-data-dir=knowledge_packs=knowledge_packs \
  --include-data-dir="$quest_packs_dir=quest_packs" \
  --include-data-dir=dropset_packs=dropset_packs \
  --include-data-file=crimson_data.db.gz=crimson_data.db.gz \
  --include-data-file=vfx_equip_attachments.json=vfx_equip_attachments.json \
  --include-data-file=localizationstring_eng_items.tsv=localizationstring_eng_items.tsv \
  --include-data-file=crimson_rs/crimson_rs.pyd=crimson_rs/crimson_rs.pyd \
  --include-data-file="$pyside_lib=PySide6/$(basename "$pyside_lib")" \
  --include-data-file="$shiboken_lib=shiboken6/$(basename "$shiboken_lib")" \
  "${extra_backend_args[@]}" \
  cli.py

echo
echo "Done. Output: build-output/CrimsonCLI"
