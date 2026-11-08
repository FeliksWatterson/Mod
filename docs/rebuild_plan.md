# Proposed test-only Developer Edition

**Status: proposal for independent review. Phase 1 stops here. No APK was patched, rebuilt, signed or installed; no purchase or entitlement was changed.** Read [architecture.md](architecture.md) and [entitlement_analysis.md](entitlement_analysis.md) for recovered evidence. The steps below are future work, not completed actions.

## Build constraints established by the artifact

| Constraint | Confidence and exact evidence | Consequence |
|---|---|---|
| Missing source/project | Confirmed archive inventory: `analysis/inventory.json`; product AOT snapshots in `analysis/elf_inventory.json` | Decompilation is not a Flutter project. Reconstruct a maintainable project or recover another source backup before promising a source build. |
| Runtime compatibility | Confirmed `libflutter.so:0x1edad9` identifies Dart 3.12.2; `libapp.so:0x354` identifies snapshot hash `ace654289f5abc240509fc941453ebc5` and compressed-pointer ARM64 product flags | Existing AOT bytes depend on the matching engine ABI/snapshot format. Exact Flutter framework version remains unverified; replacing only the engine is not a validated recovery path. |
| Device floor / ABI | Confirmed `analysis/manifests/base.xml`: min SDK 32, target/compile 36; native split inventory supplies only `arm64-v8a` | Match the original baseline for first parity tests. x86 and ARM32 support cannot be inferred or reconstructed from the supplied native binaries. |
| Split packaging | Confirmed base manifest requires ABI/density splits and Play splits metadata; six entries in `analysis/inventory.json` | Base-only installation is not a valid package-equivalence test. Any future split set must have consistent package/version/signing identity. |
| Signing | Confirmed `analysis/signatures/*.txt`: all six APKs verify with v3 and signer certificate SHA-256 `6648201f62392c24a7896d6fcc2804573c985c64f7ea144e11bed717272542f4`; source stamps also verify | Private signing material is not recovered from the public certificate. A separate developer key does not provide an in-place update under the original identity. Use a separate application ID and test installation. |
| Play license startup | Confirmed `analysis/jadx/sources/com/pairip/application/Application.java`, `attachBaseContext`; `com/pairip/licensecheck/LicenseClient.java`, package name constant and `checkLicense`; `LicenseResponseHelper.validateResponse` checks RS256 and package name | A repackaged production artifact may fail acquisition/license checks. Prefer a reconstructed app's normal test build configuration. Do not assume resigning preserves startup. Phase 1 does not bypass this code. |
| Native packaging | Confirmed manifest `extractNativeLibs=false`; ELF load alignment 16 KiB or 64 KiB in `analysis/elf_inventory.json`; `analysis/zipalign-arm64.txt` passes `zipalign -c -P 16 -v 4` | Preserve uncompressed, aligned native library packaging. Verify rebuilt output independently. Existing alignment alone does not prove device compatibility. |
| Native UI integration | Confirmed `s90.java`, orientation and atlas-image channels; `GeneratedPluginRegistrant.java`, platform adapters | Reimplement these contracts along with the Flutter UI and bundled web assets. |
| Local web origin | Confirmed `analysis/jadx/resources/res/xml/atlas_network_security.xml`: cleartext only for loopback | Preserve the local asset-server and WebView origin contract; do not broaden network policy to work around an untraced failure. |
| Build-tool hints | Confirmed packaged `kotlin-tooling-metadata.json` reports Gradle 9.3.1, Kotlin 2.4.0 and Java 17; top-level attribution unverified | Treat these as leads, not a recovered build lockfile. Capture actual plugin/NDK/SDK constraints during reconstruction. |
| Engine/data provenance | Confirmed `sky_atlas/engine-manifest.json`, `NOTICE.txt`, `LICENSE.txt`; packaged engine checksums match in `analysis/asset_inventory.json` | Retain notices and record source/patch provenance as part of any future distribution review. The referenced mobile patch and build scripts are absent. |

## Proposed implementation boundary

1. Reconstruct the minimal Flutter shell, navigation, account/feature domain models and atlas host first. Maintain a table of behavior recovered from the package versus newly implemented behavior. Pin the chosen Flutter/Dart/Android toolchain in the new project; preserve this evidence workspace separately.
2. Use a dedicated application ID such as `com.duychris.sky_radar.dev`, visible `Developer Edition` branding, a separate key and isolated app storage. Update provider authorities, app links, Firebase options, callback routing, backend URLs and package-dependent integrations together. Evidence for existing dependencies: base manifest provider authorities and `io.supabase.skyradar://login-callback`, `GeneratedPluginRegistrant.java`, AOT endpoint references in the entitlement report.
3. Introduce an explicit injectable entitlement provider in reconstructed source. The developer build selects a deterministic local test provider with test account/access values. Release builds select the real provider. Keep paid entitlement and feature-policy modes separate: an `off` feature must remain off unless a separate developer-only policy fixture intentionally enables it. Preserve the original policy fixture for comparison.
4. Give the test provider no purchase-verification, profile-update, RPC-write or subscription-management capability. Test access must not be serialized into production credentials or account caches. Disable live billing in the developer configuration. If payment integration is tested later, use genuine platform test tooling and the owner's staging verifier; do not fabricate transactions, tokens, signatures or receipts.
5. Connect the test provider to every recovered consumer: feature visibility, route/analysis and target gates, numeric limits, saved favorites, scan requests and the atlas host `access` payload. A JavaScript-only flag change cannot establish that Flutter or remote-data features work.
6. Route all network features to local fixtures or an owner-controlled staging environment before launching the developer build. Provide reproducible forecast, route, account and feature-policy fixtures. Use a mock service for server-protected data; a client flag cannot establish server authorization. Production endpoint strings recovered from AOT code are evidence, not approved test targets.
7. Reconstruct Play licensing and purchase integrations through supported build/distribution configuration only if required for staging. Confirm what the test build actually needs before carrying over production-added startup code. Keep app acquisition licensing distinct from account Pro access.

This boundary is a proposed engineering design, not a claim that dependency injection points already exist in the original source. Exact future implementation should follow the confirmed call sites listed in the entitlement report.

## Functional acceptance plan for a later authorized phase

No row below has been executed. All feature states are **unverified** until successful functional tests on the resulting build.

| Scenario | Required evidence |
|---|---|
| Install, cold start and restart | APK hash, signer, application ID, split consistency, device ABI/SDK, logs showing startup and the selected test environment |
| Free / Pro / admin / expired / missing account fixtures | Captured input fixture and observed UI/limit behavior; ensure Pro testing does not grant administrative operations |
| Policy values `free`, `pro`, `off`, plus absent/malformed policy | Feature visibility and access outcomes; preserve off-mode behavior and document fallback rules |
| Forecast and scan limits | Observe allowed days and actual query/request limits for free and Pro fixtures, including radius boundaries |
| Favorite limit | Attempt the fourth save as free; test Pro storage and reload, including an existing list above the free cap |
| Target, analysis, route and tracker tools | Open the actual function, generate a meaningful output and test errors; badges and dismissed paywalls are insufficient |
| Atlas H-alpha and framing | Verify the host payload, rendered overlay and camera frame, restored preferences and saved plans |
| Atlas image/export | Produce and open a nonempty valid image; exercise save/share destination, cancellation and access loss during export |
| Offline and session changes | Restart without network, expire/logout/switch accounts, restore cached state and ensure a prior account's access does not leak |
| Backend separation | Captured test traffic/environment logs demonstrate no production writes or purchase-verifier calls; mock/staging denials are handled explicitly |
| Signing and compatibility | Run apksigner/zipalign on rebuilt artifacts, then install and functionally test on the supported SDK/ABI matrix, including a 16 KiB page-size device if targeted |

Record expected/observed results, environment, logs, output artifacts and pass/fail for each scenario. A later report may say a feature is enabled only after the corresponding functional test passes. Phase 1's static evidence does not satisfy these acceptance criteria.

## Independent review handoff

Review the confirmed entitlement graph, unresolved server behavior, cache semantics and source-reconstruction cost before authorizing implementation. The signing key, exact Flutter framework pin, backend source/schema/RLS, production subscription state and functional behavior are not recovered by this analysis. No further phase is started automatically.
