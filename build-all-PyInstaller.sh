#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

./CrimsonGameMods/build.sh --target=cli --backend=pyinstaller
./CrimsonGameMods/build.sh --target=full --backend=pyinstaller
./CrimsonGameMods/build.sh --target=lite --backend=pyinstaller
./CrimsonSaveEditor/build.sh --backend=pyinstaller
