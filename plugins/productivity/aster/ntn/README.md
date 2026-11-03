# Notion CLI

`aster/ntn@0.23.25` acquires the immutable `npm:ntn` native bundle without
running its npm bootstrap installer. One schema-v2 declaration selects the
explicit upstream command for macOS ARM64/x86-64, Linux ARM64/x86-64 or Windows
x86-64. The complete tarball, byte length, SHA-256 and upstream MIT license
remain unchanged from the qualified candidate. Package identity stays
`aster/ntn`; domain `productivity` organizes source and catalog review.

From this repository root:

```text
aster-use registry package build plugins/productivity/aster/ntn --output /path/to/output/ntn-0.23.25.aix --json
aster-use registry package check /path/to/output/ntn-0.23.25.aix --json
aster-use registry package prepare /path/to/output/ntn-0.23.25.aix --repository . --domain productivity --catalog-metadata recipes/ntn/darwin-arm64.json --output /path/to/output/ntn.oci.json --json
```

Prepare the same AIX separately for each declared catalog target. Only macOS
ARM64 has native execution evidence. Installation does not register an AI Tool
or authorize account access. The source remains unpublished; signed catalog
metadata and immutable GHCR artifacts are required for official installation.
