# Phase 1 findings and review handoff

Completed 2026-11-08, Asia/Saigon. Static analysis only. No APK modification, installation, runtime patch, purchase/receipt forgery, backend request or subscription change was performed. No feature is claimed unlocked.

## Main findings

| ID | Finding | Confidence | Evidence |
|---|---|---|---|
| F01 | The SAI backup contains six APKs for package `com.duychris.sky_radar`, version 0.6.14 / 20433162. Supplied native code is ARM64 only. | Confirmed | `analysis/inventory.json`; `analysis/manifests/*.xml`; `analysis/elf_inventory.json` |
| F02 | Business/UI logic is Flutter product AOT in `libapp.so`; Android adapters and Play acquisition licensing are in DEX. | Confirmed | `libapp.so` exported `_kDart*Snapshot*` symbols; `analysis/jadx/sources/io/flutter/plugins/GeneratedPluginRegistrant.java`; `com/pairip/application/Application.java`, `attachBaseContext` |
| F03 | The engine identifies Dart 3.12.2 with compressed pointers; a framework release pin is not established. | Confirmed Dart; unverified Flutter release | `analysis/unpacked/split_config.arm64_v8a/lib/arm64-v8a/libflutter.so:0x1edad9`; `libapp.so:0x354`, hash `ace654289f5abc240509fc941453ebc5` |
| F04 | Foreground Pro is derived from a current-user-bound, time-checked account-access object, not a profile role string alone. | Confirmed client logic | `analysis/blutter/asm/sky_radar/data/auth_service.dart`, `isPaid` `0x721664`; `data/account_access.dart`, `validFor` `0x721998`, `proFor` `0x7216ec` |
| F05 | Account access is requested from Supabase `get_account_access`; local accepted responses receive a local verification timestamp. | Confirmed request/parser path; server rules unverified | `data/auth_service.dart`, `fetchProfile`: RPC `0x82dfc8`, parser `0x82e15c`, store `0x82e16c` |
| F06 | Access checks include user matching, a 24-hour freshness window, a five-minute future-clock tolerance, Pro expiry and an admin branch. | Confirmed client predicates | `data/account_access.dart`, `validFor` / `proFor`; `analysis/blutter/pp.txt`, `[pp+0x448]`, `[pp+0x21d0]`; `analysis/native_verified_sites.json` |
| F07 | Feature access and numerical limits are separate from paid status. Policy can be replaced through cached/remote configuration. | Confirmed client path; live policy unverified | `data/feature_policy.dart`, `defaults` `0x721610`, `_refresh` `0x82ecb8`, `apply` `0x82ee44`, `allows` `0x744018`; `analysis/embedded_feature_policy.json` |
| F08 | Defaults: 3/7 forecast days, 3/unlimited favorites, 100/500 km scans. Several tools are free, several Pro, contributions/AI off. Pro does not override off. | Confirmed defaults and predicate | Embedded JSON at `libapp.so:0xc616c`; `data/feature_policy.dart`, `allows`; full table in `docs/entitlement_analysis.md` |
| F09 | Forecast fetch size differs from visible forecast entitlement: default free and Pro both request at least eight days. Admin visible limit is 14 and fetch size 15. | Confirmed decoded client path | `FeaturePolicy.limit` `0x721434` / Smi immediate at `0x721478`; `fetchDays` `0x7213bc`; `OpenMeteoClient.fetchRaw` call `0x7260c8` |
| F10 | Hive `cached_account_access` feeds background daily/target notifications, with parsing and Pro checks. | Confirmed | `data/auth_service.dart`, `refreshRole`; `data/daily_noti_service.dart`, `0x8f1884`/`0x8f18a8`; `data/opportunity_alert_service.dart`, `0x8ee930`/`0x8ee96c` |
| F11 | Atlas H-alpha/framing rights are computed by Flutter and passed into JS, including later access updates. JS gates framing, plans and exports. | Confirmed client chain | `widgets/sky_atlas_view.dart`, `_atlasAccess` `0x7f0a64`, `_configure` `0x7eff68`, timer closure `0x8ad3a0`; `analysis/unpacked/base/assets/flutter_assets/assets/sky_atlas/atlas.js`, `setAccess`, `premium`, lines 425/461/611 |
| F12 | Purchase processing sends a token to an authenticated verifier, checks its response and refreshes account access. A successful purchase callback alone is not the traced final Pro grant. | Confirmed client sequence; actual server validation unverified | `data/play_billing_service.dart`, `HttpPlayBillingBackend.verify` `0x8b6c54`, `_process` call `0x8b61a8`, `verified` check `0x8b61cc`, `refreshRole` `0x8b6520` |
| F13 | A distinct Play application-license startup check validates RS256 license data/package name. Resigning/repackaging may affect startup independently of Pro. | Confirmed code; future startup behavior unverified | `analysis/jadx/sources/com/pairip/application/Application.java`; `licensecheck/LicenseClient.java`; `LicenseResponseHelper.validateResponse` |
| F14 | Every supplied APK verifies with v3 and the same signer. The original signing private key is not present in the archive inventory. | Confirmed | `analysis/signatures/*.txt`; signer SHA-256 `6648201f62392c24a7896d6fcc2804573c985c64f7ea144e11bed717272542f4`; `analysis/inventory.json` |
| F15 | Native split packaging passes a 16 KiB ZIP alignment check; ELF load alignments are 16/64 KiB. This does not establish functional compatibility. | Confirmed static check; runtime unverified | `analysis/zipalign-arm64.txt`; `analysis/elf_inventory.json`, `load_segments` |
| F16 | The sky engine and data pack match the hashes in their packaged provenance manifest. Missing source patch/build scripts prevent a claim of source reproducibility. | Confirmed packaged hashes; rebuild unverified | `analysis/asset_inventory.json`, `engine_checksums`; `sky_atlas/engine-manifest.json`, `NOTICE.txt` |
| F17 | Localization contains older “free upgrade” and staging-preview strings. No working developer-mode switch was established. | Confirmed text; reachability unverified | `analysis/unpacked/base/assets/flutter_assets/assets/i18n/en.json`; `analysis/localization_entitlement_candidates.json` |

For F05–F12, abbreviated `data/` / `widgets/` paths in the evidence column are under `analysis/blutter/asm/sky_radar/`. Hex values identify static ELF virtual addresses, not offsets suitable for another build. See [entitlement_analysis.md](entitlement_analysis.md) for source-to-consumer traces and raw-instruction caveats.

## Static verification performed

- Re-extracted safely with CRC validation and refusal to overwrite different evidence. The original backup still has SHA-256 `07671a93371ebaa1e6aa31cf2bd8ab8d64c2ffd27c5087baa92be45abc0d2b84`.
- Compared every SAI member and all **323 unpacked APK file members** byte-for-byte with the original archive. Reproduce with `python scripts/verify_integrity.py`.
- Parsed six manifests, both DEX files and seven ELF libraries; indexed **524 relevant DEX string references**, **2,052 app AOT method bodies** and **3,346 direct app-to-app calls**. Indirect/inlined calls are not covered by that direct-call index.
- Independently decoded nine key ARM64 direct calls and four code ranges from the ELF bytes using Capstone (`scripts/verify_native_sites.py`). This validates call destinations and instruction evidence, not application behavior.
- Verified signatures and source stamps for all six APKs with Android build-tools 36.0.0's apksigner; checked native split ZIP alignment with zipalign.
- Compared packaged engine.js, engine.wasm and skydata.zip against all three declared engine checksums; all match.

No Android functional tests were run, as required by this phase's scope.

## Tooling limits and unresolved questions

JADX initially reported 29 errors. Its repeat run returned 0, while 16 generated Java files still contain incomplete-method/error markers. The marker inventory is `analysis/jadx_incomplete_methods.txt`; the repeat status/log are `analysis/jadx_status.json` and `analysis/jadx.log`. A successful decompiler exit must not be equated with complete source recovery.

Blutter's output preserves useful symbols, object-pool values and branches but is disassembly. Some inferred signatures are missing, some calls are indirect, and raw tagged constants can be misleading. Exact revision-comparison semantics in `FeaturePolicy.apply` remain probable; no conclusion depends on a presumed live policy revision. Capstone cross-checks cover the listed sites, not the entire snapshot.

The artifact cannot establish backend RLS, server authorization, actual purchase validation, current subscription state, accepted live policy, token revocation, network availability or complete offline behavior. Exact Flutter framework version, original project dependencies/NDK pin, private signing keys and missing upstream patches are also unresolved. Strings alone do not prove live services or reachable features.

The rebuilt Developer Edition remains a proposal. [rebuild_plan.md](rebuild_plan.md) specifies a separate package/key, a local entitlement provider, distinct feature-policy fixtures, staging/mock network services and functional acceptance tests. **Phase 1 ends here for independent review.**
