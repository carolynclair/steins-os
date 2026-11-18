# Source publication

The GitHub repository is a curated source snapshot of the development project.
It includes the live-image inputs, package builders, Plasma experiments, original
artwork, selected real VM screenshots and documented test results.

ISO files, compiled packages, VM images and backing chains, firmware variables,
host networking inventories, private handoff notes and build caches are omitted.
Historical design boards are generated outputs; their generators and art remain.
Recorded `dist/` and raw `evidence/` paths in historical ledgers refer to local
development artifacts, rather than downloadable files in this repository.

`SOURCE-MANIFEST.json` records hashes of the exported files. Personal home
directory names are generalized in public Markdown and artwork provenance;
program code and artwork bytes are preserved. This snapshot starts a clean Git
history without rewriting the original development checkout.

From the full development checkout, prepare another new export with:

```sh
python3 build-tools/export_source.py /absolute/path/to/new-source-export
```

The destination must not exist and must be outside the development checkout.
Inspect the export, run its source checks and review the diff before publishing
updates. The exporter does not install software, control a VM, modify a desktop,
authenticate to a service or push to GitHub.

This source publication is not an ISO release. The latest screenshot milestone
is V4 Plasma; the recorded installable image uses XFCE. See
[project status](PROJECT-STATUS.md) and [licensing](../LICENSING.md).
