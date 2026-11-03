# gh

Native Aster acquisition plugin `aster/gh@2.103.3`.

The schema-v2 `toolchain.acl` preserves five verified upstream archive declarations
in one maintained source unit. Each platform declares an exact URL, byte length,
SHA-256, complete command layout and executable mode. The native installer validates
every declaration and selects only the exact host. Upstream installers are not run.
Recipe and upstream licenses stay with this source. Target-specific upstream notice
bytes, including line endings, are retained under `upstream-licenses/`.

Supported source targets: `darwin-arm64`, `darwin-x86_64`, `linux-arm64`,
`linux-x86_64` and `windows-x86_64`. Declared archive metadata does not qualify
native execution on every target. macOS ARM64 is the current native test host.

From this repository root:

```text
aster-use registry package build plugins/development/aster/gh --output /path/to/output/gh-2.103.3.aix --json
aster-use registry package check /path/to/output/gh-2.103.3.aix --json
aster-use registry package prepare /path/to/output/gh-2.103.3.aix --repository . --domain development --catalog-metadata recipes/gh/darwin-arm64.json --output /path/to/output/gh.oci.json --json
```

The same AIX source is prepared separately for each explicit catalog target.
This plugin remains unpublished. A signed catalog and exact GHCR artifact are
required for official-market installation. Installing a toolchain does not
register an AI Tool or grant permission to execute it.
