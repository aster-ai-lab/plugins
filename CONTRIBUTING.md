# Contributing

Read [the layout contract](docs/layout.md) before adding paths. Keep package
identity stable and declare domain admission in `domains.acl`; do not classify
plugins by their names. Use LF and UTF-8 without BOM for source text.

Run the repository checks from this directory:

```sh
python3 -m unittest discover -s tests -v
```

Runtime publication uses the native `aster-use registry package` commands
from the accompanying Aster checkout. Build through a qualified target recipe
and publish its existing AIX/OCI bytes with `scripts/publish-runtime.py`.
Do not edit generated catalog, lock or TUF files by hand. Refresh metadata
with `scripts/registry.py refresh --keychain` on the signing Mac, or the online
refresh workflow for an already consistent registry. Local signing requires
Swift/CryptoKit and OpenSSL 3; CI signing uses OpenSSL 3 and the three online
role secrets. Root initialization and rotation are separate operations.

Before landing a publication, verify that catalog records match signed
targets and that every selected lock entry has the exact available catalog
version and archive/package/manifest digests. Qualify payload completeness and
execution natively for each affected OS/CPU. A source-layout check does not
prove that a binary runs on that target.

Use signed commits with DCO sign-off. Land the plugins commit first, then
update the parent Aster gitlink and the consuming release's sealed lock.
Never commit credentials, signing seeds, native binaries or user state.
