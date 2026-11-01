# Aster plugins

Official Aster plugins are native `.aix` packages stored in this repository's
[GitHub Packages](https://github.com/orgs/aster-ai-lab/packages?repo_name=plugins).
Git contains recipes, catalog records and public TUF metadata; native binaries
and models stay in GHCR. Aster installs immutable OCI digests after TUF verification.

```
domains.acl
plugins/operations/aster/{aster-sandbox,aster-document,aster-office}/
scripts/                 # Native publication and TUF signing
registry/catalog/        # Exact native package and OCI identities
registry/runtime-locks/  # Host-independent component pins by target
registry/metadata/       # Public signed TUF generations
registry/root.sha256     # Desktop trust anchor
```

Runtime components use a payload content version independent from desktop versions.
The version uses a SHA-256 prefix within the frozen 64-character selector limit;
archive, expanded-package and manifest integrity retain complete SHA-256 digests.
Catalog files retain every published component version needed by supported bases.
Publishing refuses a different archive for an existing version. The desktop
consumes an already published target lock. An unchanged package version
and digest reuse the installed receipt and immutable generation.

## Publish runtime components

1. Build and qualify a complete desktop bundle using Aster's release workflow.
   Its native `package_runtime_components.py` producer uses
   `aster-use registry package build/check/prepare` and writes AIX, exact OCI
   manifests, publication evidence and a target lock. Native source staging is
   `repository/<target>/plugins/<domain>/<publisher>/<name>`.
2. Authenticate ORAS to GHCR with package write permission, then run
   `python3 scripts/publish.py CANDIDATES --aster-use-bin ASTER_USE --oras ORAS`.
   The script rechecks the staged source with the native SDK and copies the exact
   OCI manifest. Set each new GHCR package public and verify anonymous pull before
   publishing the catalog. Publication does not run the payload or qualify a target.
3. Run `python3 scripts/registry.py refresh --keychain` on the signing Mac, or
   dispatch **Refresh signed registry** after committing catalog changes.
   Commit the catalog, lock and metadata together. Copy the released lock into
   the desktop build and set `ASTER_PLUGIN_ROOT_SHA256` from `registry/root.sha256`.

The initial root key stays in macOS Keychain (`dev.aster.plugins.tuf.v1`, account
`root`). Only targets/snapshot/timestamp keys are GitHub Actions secrets. Root
rotation requires an explicit old-root and new-root signing ceremony before the
root's expiry; `init-root` refuses an existing root. Online metadata refreshes daily.
The root starts with one key and threshold one; maintainers must back up the signing
Mac's Keychain through their approved key recovery process.

The initial runtime recipes use the verified macOS ARM64 desktop v0.1.11 assets.
`scripts/build-runtime.py` validates that upstream archive before invoking the
native producer from an Aster source checkout. Its native package content,
membership and permissions match the published packages. Rebuilding can change
ZIP bytes; retain the original published AIX and target lock for a released
version instead of replacing its archive with a rebuild.
Linux, Windows and other architectures require their own native builds and runtime
qualification before adding target locks. No target compatibility is inferred from
architecture names alone.
