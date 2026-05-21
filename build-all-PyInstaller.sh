#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

./CrimsonGameMods/build-cli-PyInstaller.sh
./CrimsonGameMods/build-full-PyInstaller.sh
./CrimsonGameMods/build-lite-PyInstaller.sh
./CrimsonSaveEditor/build-PyInstaller.sh
