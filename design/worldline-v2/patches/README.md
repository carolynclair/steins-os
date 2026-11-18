# V2 source snapshot

Four runtime source files implement three small corrections: Reduced/Off meter motion (two files), bounded recovery from transient wallpaper-service startup errors, and mode-aware Plymouth status text. The fifth file adds meaningful private-bus recovery regression tests. `FILEMAP.json` maps every snapshot to its repository source and SHA-256.

The meter and worldline service were hotfixed and tested only in the isolated V2 fork, with guest originals backed up. Plymouth remains a source-only correction, awaiting separate packaging/initramfs and real boot/prompt/shutdown qualification. The working prototype and existing ISO were preserved.

This is a review snapshot, not a complete distribution build or installer. No file in this folder installs itself. Do not copy these over a personal system. Patches and pre-change source copies are retained in the review startup/engineering/evidence folders. The guarded fork replay helper requires the original repository and prepared local VM checkpoint; it applies meter/service files only, not Plymouth.
