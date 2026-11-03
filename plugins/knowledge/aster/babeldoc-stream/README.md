# BabelDOC Stream

`aster/babeldoc-stream` recipe 0.1.0 packages BabelDOC Stream 0.6.4.post4
with its own CPython 3.12.14, pinned wheels, native libraries and upstream notices.
The source identity remains `pipx:babeldoc-stream`; installation runs neither
pipx nor an upstream installer. The recipe requires the independently qualified
macOS ARM64 runtime archive with its exact length and SHA-256. Native payloads
stay outside Git and are embedded in the produced AIX for GHCR distribution.

From this repository root:

```text
python3 recipes/babeldoc-stream/darwin-arm64.py /path/to/babeldoc-stream-darwin-arm64.tar.gz --aster-use-bin /path/to/aster-use --out /path/to/build-output
```

The recipe stages `repository/plugins/knowledge/aster/babeldoc-stream` in the
output directory, generates `toolchain.acl`, and runs native AIX build, check
and catalog preparation. This maintained source directory is input to that
recipe; it is not a standalone package without its qualified runtime archive.
It refuses changed runtime bytes and existing output directories.

`SOURCE.json`, the exact generated `requirements.lock`, and `launcher.py` retain
the candidate provenance. The lock pins bitstring below 5 because BabelDOC
imports BitStream. The archive includes the multiprocessing-safe launcher and
all runtime notices. LICENSE and NOTICE preserve upstream AGPL-3.0 terms;
ASTER-RECIPE-LICENSE covers the Aster recipe and launcher. The upstream NOTICE
is retained verbatim, including its corresponding-source reference.

Only macOS ARM64 is qualified for native installation/version startup. This
source is unpublished. PDF translation, GUI use, other platforms, complete
consumer integration and signed official publication remain unverified.
