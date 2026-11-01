# Repository layout and maintenance

The stable package identity is `<publisher>/<name>`. Source paths, catalog
paths and GHCR repositories follow that identity. A domain describes what a
plugin does and who reviews its publication; changing an admitted domain does
not move its source or artifact. The native SDK receives the domain explicitly
and checks `domains.acl`. No name or directory is used to guess a category.

| Path | Maintained by | Contract |
| --- | --- | --- |
| `domains.acl` | Domain maintainers | Explicit owner/publisher admission, parsed by native `aster-acl` |
| `plugins/<publisher>/<name>/` | Plugin maintainers | One source unit per package; README and licenses stay with it |
| `recipes/runtime/<target>.py` | Runtime maintainers | Pinned inputs and an executable build recipe for a qualified target |
| `registry/catalog/<publisher>/<name>/<version>/<channel>/<target>.json` | Native publisher | One generated release record for the complete selection identity |
| `registry/locks/runtime/<target>.json` | Runtime publisher | The currently selected component set for desktop packaging |
| `registry/metadata/` | TUF signer | Generated signed metadata consumed by clients |
| `registry/root.sha256` | Root initialization/rotation | Public trust anchor; never an online refresh output |
| `scripts/` | Registry maintainers | Small operational entry points and their shared catalog/signing code |
| `tests/` | Registry maintainers | Storage, signing-input and selected-lock contract checks |
| `.github/workflows/` | Repository maintainers | Read-only validation and a separate secret-bearing refresh job |

`.github/CODEOWNERS` names an actual repository maintainer for code review;
domain owner identifiers do not grant GitHub repository or package permissions.
`.gitattributes` keeps source text LF and preserves signed metadata as exact bytes.

## Plugin source and build ownership

Keep each plugin's manifest, source, assets and tests together when it has
handwritten extension sources. Create optional subdirectories only when used.
Do not repeat the domain in the source path, add per-version source copies,
or commit native payloads alongside the source.

The three runtime plugins currently contain documentation and licenses here.
Their generated `aster-use-extension.acl`, `runtime.acl` and payload membership
are owned by Aster's `apps/studio/scripts/package_runtime_components.py`, using
the owning native crates and `studio-runtime-files.txt`. The shared target
recipe invokes that producer, which stages a complete source tree outside Git
and verifies it against the archive through the native SDK. These directories
are not presented as independently buildable handwritten implementations.
The producer lives in the private Studio submodule; building needs an authorized
Aster checkout, while consuming published packages does not.

`recipes/runtime/darwin-arm64.py` describes the current approved bootstrap
input: a digest-pinned desktop archive. It qualifies only macOS ARM64. Add a
new target recipe after its native libraries, ABI, files and runtime behavior
have been checked. Do not infer Linux, Kylin, Windows or other CPU support
from a similar directory name. Do not duplicate the producer's component
membership in a second recipe format or parser.

## Catalog and lock lifecycle

The catalog includes the publisher namespace to prevent equal plugin names
from colliding. Version, channel and target are separate path components;
business domains stay in the record's categories. A channel may select
multiple immutable versions, so it is not a single mutable release file.
The publisher and signer share one path function. The signer recursively
loads records and refuses misplaced records, duplicate TUF targets and an
empty catalog. CI compares these inputs with the current signed target set.

After release, retain catalog versions needed by supported clients and mark
withdrawn releases explicitly. Never replace a released archive under the
same version. Unreleased bootstrap experiments need not remain in the active
catalog; their changes remain in Git history.

A runtime lock is a generated selection for one target, not another package
catalog or a build recipe. The desktop release copies and seals its selected
lock. The Aster parent pins this repository's exact Git revision; `main` is
not an immutable release identity. Update catalog records, locks and their
signed metadata in the same publication commit. Historical release inputs
remain identifiable by commit and by their archive/package/manifest digests.

## Signed metadata and binary storage

`registry/metadata/` follows the client's TUF repository contract. It contains
the current role aliases and versioned roots, targets and snapshots. Do not
nest role files by publisher, hand-edit signed JSON, remove generations as
cosmetic cleanup, or reset versions. Metadata paths and consistent snapshots
are protocol decisions: see the [TUF specification](https://theupdateframework.github.io/specification/latest/).

The logical package target is:

```text
extensions/<publisher>/<name>/<version>/<channel>/<target>/oci-ghcr-v1/<manifest-sha256>/<name>.aix
```

Its OCI repository is `ghcr.io/aster-ai-lab/plugins/<publisher>/<name>`.
Installation uses the signed immutable manifest and AIX digests. Tags aid
discovery; neither a business category nor a mutable tag defines artifact
identity. Associate packages with this GitHub repository and qualify anonymous
pull before claiming public first-run installation.

Native archives, models, extraction trees, credentials and private keys stay
out of Git. Build candidates use an explicit output directory, normally under
the parent checkout's `target/`. Root keys remain offline/in Keychain; online
keys are CI secrets. No `keys/`, binary cache, release-copy tree or unused
future target folders are added here. If catalog growth reaches the native
metadata byte/work limits, introduce measured TUF delegation and hosting
changes together; a deeper source directory does not shard signed metadata.
