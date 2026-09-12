# JobBubble Android

JobBubble is a U.S.-focused Android job-search app that presents live job listings on an interactive map and in a list view.

## Build structure

The repository currently uses a legacy Android project ZIP as its source seed. CI extracts that project and applies the current application changes before compiling.

Use **`scripts/apply_current.py <project_dir>`** as the single patch entry point. It applies the maintained patch sequence and the dead-code cleanup pass. Workflows should call this entry point instead of invoking individual version patch scripts directly.

Generated APK/AAB files are CI artifacts and should not be committed to source control. The legacy source ZIP remains in the repository only until the source-seed architecture is migrated to normal tracked Android source files.

## Verification

A release is not considered ready solely because it compiles. The release workflow verifies the requested source transformations, builds the release APK, signs it, and validates its signature. Running-app verification is maintained separately for live job-provider and UI behavior, including The Muse.

## Current cleanup

The V9.4.47 cleanup pass removes Java helpers only when they are demonstrably unreferenced in `MainActivity.java`. It also keeps a checkpoint branch before cleanup so the change can be compared or reverted safely.
