# JobBubble Android

JobBubble is an Android job-search app that displays live job listings on a map and in a list, with saved profile data, source/category filters, distance/pay filters, clustering, approximate-location handling, and Firebase-backed account/profile features.

## Current build

The current cleanup target is **V9.4.48**. The repository keeps the last complete Android source ZIP as a reproducible base, then applies the current patch chain during CI:

1. `scripts/v943_patch.py` — settings/source and map baseline updates.
2. `scripts/v944_patch.py` — The Muse source, salary handling, and large-cluster behavior.
3. `scripts/v947_patch.py` — dark-map and interface-theme corrections.
4. `scripts/v948_cleanup.py` — source cleanup, validation, filter-theme cleanup, stale-file removal, and structural checks.

The release workflow validates the patch scripts, cleans and validates the extracted source, runs Android Lint, builds the release APK, signs it, verifies the signature, and uploads the signed APK as a GitHub Actions artifact.

## CI workflows

- **Build JobBubble APK**: lint, build, sign, and package the current release.
- **Verify Running JobBubble App**: boots an Android emulator, selects The Muse and a 100-mile radius, then confirms multiple live Muse jobs are visible in the running app.
- **Inspect JobBubble Source Logic**: audits source structure, filter/source logic, clustering, theme remnants, and live Muse backend data.
- **Export JobBubble Source**: exports the cleaned, fully patched current source tree as an artifact.

## Secrets

The Google Maps API key is injected by GitHub Actions from `GOOGLE_MAPS_API_KEY`; it should not be committed directly into the Android source. Local developer-specific paths and credentials should remain outside version control.
