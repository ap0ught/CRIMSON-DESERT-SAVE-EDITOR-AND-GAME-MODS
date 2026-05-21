#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

./CrimsonGameMods/build-cli-Nuitka.sh
./CrimsonGameMods/build-full-Nuitka.sh
./CrimsonGameMods/build-lite-Nuitka.sh
./CrimsonSaveEditor/build-Nuitka.sh
