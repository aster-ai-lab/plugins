# aster-office

Office companion. Installed on first Office use.

The native producer is `apps/studio/scripts/package_runtime_components.py` in Aster.
The complete staged source includes `aster-use-extension.acl`, `runtime.acl`,
`README.md`, `LICENSE` and `payload/`; the SDK validates that staged source against
the AIX archive before publication. Generated payloads stay out of Git.

Published target: `darwin-arm64`, using verified Aster desktop v0.1.11 assets.
See the exact signed catalog in `registry/catalog/` and target pins in
`registry/locks/runtime/`. Other targets require native qualification.
