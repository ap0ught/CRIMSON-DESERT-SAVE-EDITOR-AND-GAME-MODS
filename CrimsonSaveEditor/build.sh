#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

export PYTHONPATH="$(cd .. && pwd)/CrimsonGameMods:${PYTHONPATH:-}"

echo "Clearing caches..."
find . -type d -name '__pycache__' -prune -exec rm -rf '{}' +
rm -rf build-output

extra_backend_args=()
if [[ -f ../CrimsonGameMods/dmm_parser/dmm_parser.abi3.so ]]; then
  extra_backend_args+=(--include-data-file=../CrimsonGameMods/dmm_parser/dmm_parser.abi3.so=dmm_parser/dmm_parser.abi3.so)
elif [[ -f ../CrimsonGameMods/dmm_parser/dmm_parser.pyd ]]; then
  extra_backend_args+=(--include-data-file=../CrimsonGameMods/dmm_parser/dmm_parser.pyd=dmm_parser/dmm_parser.pyd)
fi

extra_crimson_args=()
if [[ -f ../CrimsonGameMods/crimson_rs/crimson_rs.abi3.so ]]; then
  extra_crimson_args+=(--include-data-file=../CrimsonGameMods/crimson_rs/crimson_rs.abi3.so=crimson_rs/crimson_rs.abi3.so)
elif [[ -f ../CrimsonGameMods/crimson_rs/crimson_rs.pyd ]]; then
  extra_crimson_args+=(--include-data-file=../CrimsonGameMods/crimson_rs/crimson_rs.pyd=crimson_rs/crimson_rs.pyd)
fi

echo "Building with Nuitka..."
python3 -m nuitka \
  --standalone \
  --onefile \
  --assume-yes-for-downloads \
  --enable-plugin=pyside6 \
  --include-package=crimson_rs \
  --output-dir=build-output \
  --output-filename=CrimsonSaveEditor \
  --include-data-file=parc_parser.dll=parc_parser.dll \
  --include-data-file=item_names.json=item_names.json \
  --include-data-file=store_names.json=store_names.json \
  --include-data-file=item_templates.json=item_templates.json \
  --include-data-file=master_templates.json=master_templates.json \
  --include-data-file=item_limits.json=item_limits.json \
  --include-data-file=item_category_map.json=item_category_map.json \
  --include-data-file=max_enchant_map.json=max_enchant_map.json \
  --include-data-file=waypoint_templates_community.json=waypoint_templates_community.json \
  --include-data-file=abyss_gimmick_templates.json=abyss_gimmick_templates.json \
  --include-data-file=knowledge_keys_all.json=knowledge_keys_all.json \
  --include-data-file=community_knowledge_keys.json=community_knowledge_keys.json \
  --include-data-file=quest_names.json=quest_names.json \
  --include-data-file=quest_database.json=quest_database.json \
  --include-data-file=mission_names.json=mission_names.json \
  --include-data-file=quest_stage_map.json=quest_stage_map.json \
  --include-data-file=stage_names.json=stage_names.json \
  --include-data-file=gimmick_respawn_timers.json=gimmick_respawn_timers.json \
  --include-data-file=quest_chains.json=quest_chains.json \
  --include-data-file=dye_slot_counts.json=dye_slot_counts.json \
  --include-data-file=buff_skill_descriptions.json=buff_skill_descriptions.json \
  --include-data-file=game_map.json=game_map.json \
  --include-data-file=localizationstring_eng_items.tsv=localizationstring_eng_items.tsv \
  --include-data-file=editor_version_standalone.json=editor_version_standalone.json \
  --include-data-dir=locale=locale \
  --include-data-dir=knowledge_packs=knowledge_packs \
  --include-data-file=/home/jack/.local/lib/python3.14/site-packages/PySide6/libpyside6.abi3.so.6.11=PySide6/libpyside6.abi3.so.6.11 \
  --include-data-file=/home/jack/.local/lib/python3.14/site-packages/PySide6/libpyside6qml.abi3.so.6.11=PySide6/libpyside6qml.abi3.so.6.11 \
  --include-data-file=/home/jack/.local/lib/python3.14/site-packages/shiboken6/libshiboken6.abi3.so.6.11=shiboken6/libshiboken6.abi3.so.6.11 \
  "${extra_backend_args[@]}" \
  "${extra_crimson_args[@]}" \
  main.py

echo
echo "Done. Output: build-output/CrimsonSaveEditor"
