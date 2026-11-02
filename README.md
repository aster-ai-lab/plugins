# Aster plugins

Official Aster plugins are native `.aix` packages stored in this repository's
[GitHub Packages](https://github.com/orgs/aster-ai-lab/packages?repo_name=plugins).
Git contains recipes, catalog records and public TUF metadata; native binaries
and models stay in GHCR. Aster installs immutable OCI digests after TUF verification.

```
domains.acl                            # Explicit domain ownership and admission
plugins/<publisher>/<name>/             # Stable plugin source identity
recipes/runtime/<target>.py             # Qualified runtime input/build recipes
registry/catalog/<publisher>/<name>/
  <version>/<channel>/<target>.json     # Exact native package and OCI identities
registry/locks/runtime/<target>.json    # Selected desktop component pins
registry/targets/                      # Hash-prefixed native MCP planning bytes
registry/metadata/                     # Generated public TUF metadata
registry/root.sha256                   # Desktop trust anchor
skills/aster-plugins/                   # AI installation and connection workflow
scripts/                               # Publication, catalog and signing tools
tests/                                 # Repository contract checks
docs/                                  # Layout and maintenance decisions
```

Runtime components use a content version independent from desktop versions.
The version uses a SHA-256 prefix within the frozen 64-character selector limit;
archive, expanded-package and manifest integrity retain complete SHA-256 digests.
Catalog files retain every published component version needed by supported bases.
Publishing refuses a different archive for an existing version. The desktop
consumes an already published target lock. An unchanged package version
and digest reuse the installed receipt and immutable generation.

Domains are explicit metadata, not part of package identity or storage addresses.
See [layout and maintenance](docs/layout.md) for each directory's owner, generated
boundaries and retention rules, and [contributing](CONTRIBUTING.md) for checks.

## Distribution status

All four official GHCR packages are public. On 2026-11-02, a fresh profile passed
anonymous native SDK inspection, exact-version planning, installation and enabled
package verification for every component, including TUF and content-digest checks.
The installed OCR package also passed real MCP discovery, readiness and recognition
of a fixed test image. The anonymous-install prerequisite for a slim desktop
release has passed; a complete new signed desktop archive still needs its release
qualification. The qualified target remains macOS ARM64.

## Available capabilities

| Package | Contents | Desktop installation |
| --- | --- | --- |
| `aster/aster-sandbox` | Sandbox executable, native companions and system image | Required, installed after the base |
| `aster/aster-document` | PDFium and document fonts | Required, installed after the base |
| `aster/aster-office` | Office companion | Optional |
| `aster/aster-ocr` | OCR executable, ONNX Runtime, PP-OCRv6 models, MCP and Skill | Optional; installed on first OCR use |

Only **macOS ARM64** currently has a qualified target lock. Linux (including
Kylin x86-64), Windows and macOS x86-64 need their own native packages and runtime
qualification. A portable Rust source tree does not qualify a binary target.

For AI hosts, load [the Aster plugins Skill](skills/aster-plugins/SKILL.md).
The OCR package carries its own canonical `aster-use-ocr` Skill. Tools are exposed
only after the host connects the installed MCP projection; use actual discovered
names, not a hardcoded server prefix.

## Install and connect

The desktop host supplies its pinned signing root and component lock. A CLI host
first checks `aster-use registry source list --json`. If the official source is
missing, register it using the **independently trusted** root digest
from its Aster distribution (`registry/root.sha256` in a reviewed checkout):

```text
aster-use registry source add aster-official --github aster-ai-lab/plugins --trust-root <trusted-root-sha256> --json
```

Preserve existing trust roots and default-source choices. Once the source is
configured, inspect the release and plan the exact content version:

```text
aster-use plugin inspect aster/aster-ocr --channel stable --json
aster-use plugin plan-install aster/aster-ocr --registry-name aster-official --version-requirement "<inspected-version>" --channel stable --scope-kind user --scope-id user/current --json
```

Review the exact selected package, surfaces and permissions. After authorizing
the plan, use the returned `.data.plan.plan.operationId` and
`.data.plan.planDigest`, in the same profile and scope:

```text
aster-use plugin apply-plan --operation-id <operationId> --plan-digest <planDigest> --scope-kind user --scope-id user/current --yes --json
aster-use extension inspect aster/aster-ocr --json
aster-use capability snapshot --json
```

These commands use the native `aster-use` developer binary; normal desktop users
install through the host plugin manager.
The host connects the resulting MCP projection and retains its native generation
for the process lifetime. OCR exposes `ocr_doctor` and `ocr_extract`; extraction
input is `{"path":"/exact/local/image.png"}` and the structured result contains
text, blocks, source evidence and warnings. Native execution permission is a
review contract; it is not a claim of OS sandboxing.

GitHub repository visibility and GHCR package visibility are separate. Every
released package must pass an anonymous pull check; a 401 prevents first-run
installation even when this source repository is public.

## Publish runtime components

1. Build and qualify a complete desktop bundle using Aster's release workflow.
   Its native `package_runtime_components.py` producer uses
   `aster-use registry package build/check/prepare` and writes AIX, exact OCI
   manifests, publication evidence and a target lock. Native source staging is
   `repository/<target>/plugins/<publisher>/<name>`.
2. Authenticate ORAS to GHCR with package write permission, then run
   `python3 scripts/publish-runtime.py CANDIDATES --aster-use-bin ASTER_USE --oras ORAS`.
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

The bootstrap runtime recipe uses the verified macOS ARM64 desktop v0.1.11 assets
and a newly built OCR executable; models and ONNX Runtime move into the OCR AIX.
`recipes/runtime/darwin-arm64.py` validates that upstream archive before invoking the
native producer from an Aster source checkout. Its native package content,
membership and permissions match the published packages. Rebuilding can change
ZIP bytes; retain the original published AIX and target lock for a released
version instead of replacing its archive with a rebuild.
Linux, Windows and other architectures require their own native builds and runtime
qualification before adding target locks. No target compatibility is inferred from
architecture names alone.
