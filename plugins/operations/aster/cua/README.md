# CUA

`aster/cua` 0.9.0 references the complete macOS ARM64 CLI release from
`trycua/cua` at `cua-sdk-v0.9.0`, including its native virtualization and
Linux guest helpers. No upstream installer runs. The MIT root license covers
this Aster acquisition recipe; UPSTREAM-LICENSE preserves the producer notice.

This maintained source currently targets macOS ARM64. It downloads the exact
external archive declared in `toolchain.acl`, retains all four declared commands,
and uses Aster's owned generations for installation and removal. No binary or
upstream installer is stored here.

From the repository root, build and prepare with Aster's native tools:

```sh
aster use registry package build plugins/operations/aster/cua --output /path/to/build/cua.aix --json
aster use registry package prepare /path/to/build/cua.aix --repository . --domain operations --catalog-metadata recipes/cua/darwin-arm64.json --output /path/to/build/cua.oci.json --json
```

The output directory must already exist. This source is not a published release.
Only acquisition, primary-version and package-lifecycle checks are qualified;
other platforms, CUA GUI/VM operation and marketplace installation still require
acceptance. The pinned checksum does not establish upstream Sigstore provenance.
