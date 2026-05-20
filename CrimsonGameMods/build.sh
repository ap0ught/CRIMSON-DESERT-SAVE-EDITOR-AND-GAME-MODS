#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "Clearing caches..."
find . -type d -name '__pycache__' -prune -exec rm -rf '{}' +
rm -rf build-output

extra_backend_args=()
if [[ -f dmm_parser/dmm_parser.abi3.so ]]; then
  extra_backend_args+=(--include-data-file=dmm_parser/dmm_parser.abi3.so=dmm_parser/dmm_parser.abi3.so)
elif [[ -f dmm_parser/dmm_parser.pyd ]]; then
  extra_backend_args+=(--include-data-file=dmm_parser/dmm_parser.pyd=dmm_parser/dmm_parser.pyd)
fi

echo "Building with Nuitka..."
python3 -m nuitka \
  --standalone \
  --onefile \
  --assume-yes-for-downloads \
  --enable-plugin=pyside6 \
  --include-package=crimson_rs \
  --output-dir=build-output \
  --output-filename=CrimsonGameMods \
  --include-data-dir=data=data \
  --include-data-dir=locale=locale \
  --include-data-dir=knowledge_packs=knowledge_packs \
  --include-data-dir=/home/jack/Documents/SWISS-CrimsonDesert/CRIMSON-DESERT-SAVE-EDITOR-AND-GAME-MODS/quest_packs=quest_packs \
  --include-data-dir=dropset_packs=dropset_packs \
  --include-data-file=crimson_data.db.gz=crimson_data.db.gz \
  --include-data-file=vfx_equip_attachments.json=vfx_equip_attachments.json \
  --include-data-file=localizationstring_eng_items.tsv=localizationstring_eng_items.tsv \
  --include-data-file=crimson_rs/crimson_rs.pyd=crimson_rs/crimson_rs.pyd \
  --include-data-file=dmm_parser/dmm_parser.pyd=dmm_parser/dmm_parser.pyd \
  --include-data-file=/home/jack/.local/lib/python3.14/site-packages/PySide6/libpyside6.abi3.so.6.11=PySide6/libpyside6.abi3.so.6.11 \
  --include-data-file=/home/jack/.local/lib/python3.14/site-packages/PySide6/libpyside6qml.abi3.so.6.11=PySide6/libpyside6qml.abi3.so.6.11 \
  --include-data-file=/home/jack/.local/lib/python3.14/site-packages/shiboken6/libshiboken6.abi3.so.6.11=shiboken6/libshiboken6.abi3.so.6.11 \
  --include-data-file=parc_parser.dll=parc_parser.dll \
  --include-data-file=app_icon.ico=app_icon.ico \
  "${extra_backend_args[@]}" \
  main.py

echo
echo "Done. Output: build-output/CrimsonGameMods"
