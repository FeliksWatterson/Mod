#!/bin/sh
# Run from WSL: wsl -e sh /mnt/d/Mod/scripts/run_aot.sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$root/tools/blutter"
python3 -u blutter.py "$root/analysis/unpacked/split_config.arm64_v8a/lib/arm64-v8a" \
    "$root/analysis/blutter" > "$root/analysis/blutter.log" 2>&1
