#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

./CrimsonGameMods/build.sh --target=cli --backend=nuitka
./CrimsonGameMods/build.sh --target=full --backend=nuitka
./CrimsonGameMods/build.sh --target=lite --backend=nuitka
./CrimsonSaveEditor/build.sh --backend=nuitka
