# Reproduce Phase 1 static analysis

Run from `D:\Mod` in PowerShell. Original APKs/APKS are read-only inputs to these scripts. No script installs the app, patches its code, launches it, or calls its backend. Downloads below fetch analysis tools/source packages only.

## Windows preparation

Requires Python 3.12, Java 21 and Git on PATH. `rg` is useful for reviewing outputs. The performed run used JADX 1.5.6, Android build-tools 36.0.0, Androguard 4.1.4, pyelftools 0.33 and Capstone 5.0.9.

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r scripts/requirements.lock.txt
python scripts/setup_tools.py
./scripts/run_static.ps1 -Decompile
python scripts/verify_integrity.py
```

`setup_tools.py` pins download URLs and SHA-256 for JADX/build-tools and Blutter commit `4a60ac648bf448c5a7596437243bcd0b9376fdf0`. It changes only Blutter's tool-build invocations to limit Ninja to four jobs. No target APK or `.so` is changed. Tool extraction overwrites tool files, never evidence. Python dependency pins are in `requirements.lock.txt`.

`extract_inventory.py` extracts the SAI into `analysis/splits/`, then APK members into `analysis/unpacked/<split>/`. It checks ZIP paths/CRCs and refuses to replace an existing evidence file with different bytes. `inventory.json` records the input/split hashes and every ZIP entry. You may supply an explicit APKS path, but `verify_integrity.py` intentionally pins this analyzed backup's filename and digest.

`static_report.py` writes decoded manifests, APK/DEX/ELF metadata, native strings with hexadecimal file offsets, DEX strings and relevant `const-string` references. DEX instruction offsets are bytes relative to the method instruction stream; the method code file offset is separate. It also extracts entitlement-related localization text as candidates, not proof of reachability.

`asset_report.py` inventories assets and nested ZIP members, validates the three engine checksums and extracts the exact embedded feature-policy JSON with its file offset.

`verify_signatures.ps1` runs apksigner verification against all six splits and retains full output. `run_static.ps1` also records native ZIP alignment. `decompile.py` records JADX's true exit status, including partial-success runs. Review incomplete Java methods even if the status is zero. To refresh the marker inventory after decompiling:

```powershell
rg -n 'JADX ERROR|Method not decompiled' analysis/jadx/sources |
    Set-Content -Encoding utf8 analysis/jadx_incomplete_methods.txt
```

## Static AOT analysis in WSL Ubuntu 24.04

The performed run used GCC 13.3.0 and Blutter's reconstructed Dart 3.12.2 AOT reader. This compiles a desktop analysis tool; it does not rebuild or run SkyRadar. WSL Git transport stalled during the original SDK fetch, so the pinned Dart source archive is prepared on Windows instead.

Install WSL analysis prerequisites if missing (this changes WSL tool packages only):

```powershell
wsl -u root -e apt-get update
wsl -u root -e apt-get install -y python3-pyelftools python3-requests git cmake ninja-build build-essential pkg-config libicu-dev libcapstone-dev
python scripts/prepare_blutter_sdk.py
wsl -e sh /mnt/d/Mod/scripts/run_aot.sh
python scripts/aot_index.py
.\.venv\Scripts\python scripts/verify_native_sites.py
```

For another workspace location, adjust the WSL path to `run_aot.sh`; the script resolves its own repository root. Building on the Windows-mounted volume can take several minutes. The Dart archive URL, SHA-256 and snapshot hash are pinned in `prepare_blutter_sdk.py` and recorded in `analysis/dart_sdk_source.json`. `version.cc` is generated from the upstream template with the observed snapshot hash and display-only git metadata set to `archive`. This modifies analyzer tool sources only.

Blutter writes symbolic disassembly to `analysis/blutter/asm/`, pool objects to `pp.txt`/`objs.txt`, and a log to `analysis/blutter.log`. It also automatically generates Frida/IDA helper templates. Those templates were neither loaded nor executed; runtime instrumentation is outside Phase 1. `.dart` filenames in `asm/` are library names, not recovered compilable source. Some tool output includes process-specific host addresses; use ELF addresses and original bytes for review.

```powershell
# List indexed app methods in entitlement-related libraries.
python scripts/aot_query.py 'account_access|auth_service|feature_policy'
# Print symbolic comments for one predicate; open the indexed file for full ARM64.
python scripts/aot_query.py account_access 'proFor|validFor'
python scripts/aot_query.py feature_policy 'allows|fetchDays'
```

`verify_native_sites.py` translates ELF virtual addresses to file offsets, checks selected branch destinations and records complete independent instruction ranges. It explicitly documents the tagged Smi 14 at `0x721478`; raw Blutter immediate labels are not always semantic integers.

## Evidence to review

| Output | Purpose |
|---|---|
| `analysis/inventory.json` | Original/split hashes and archive entries |
| `analysis/apk_metadata.json`, `analysis/manifests/` | Identity, SDK and permissions |
| `analysis/dex_inventory.json`, `analysis/dex_string_references.json` | Both DEX inventories and string consumers |
| `analysis/elf_inventory.json`, `analysis/strings/` | Native headers, symbols, alignments and raw strings |
| `analysis/asset_inventory.json`, `analysis/embedded_feature_policy.json` | Bundled web assets, nested ZIPs, checksums and policy |
| `analysis/jadx/`, status/log/marker files | Decompiled Java/resources with known gaps |
| `analysis/blutter/`, `analysis/aot_methods.json`, `analysis/aot_calls.json` | AOT symbolic evidence and direct-call index |
| `analysis/native_verified_sites.json` | Independent raw ARM64 checks |
| `analysis/signatures/`, `analysis/zipalign-arm64.txt` | Cryptographic package verification and alignment |
| `docs/*.md` | Architecture, entitlement traces, findings and proposed rebuild plan |

Run `.\.venv\Scripts\python scripts/record_validation.py` at the end to retain the final checks in `analysis/validation.json`, including document hashes. It reruns `verify_integrity.py` and the independent native-site checks and checks the retained signature/alignment/asset reports. For this artifact the integrity check must report the unchanged pinned SHA-256 and 323 identical unpacked APK members. This proves evidence preservation, not feature functionality. Stop after the report and independent review; the rebuild plan is not implemented by these scripts.
