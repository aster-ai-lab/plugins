---
name: aster-plugins
description: Discover, inspect, install, diagnose, and connect official Aster .aix plugins. Use when a task needs an optional Aster capability such as OCR, when a plugin or MCP server is missing, or when reviewing a plugin installation plan and its permissions. Also use to explain package readiness, target support, and unchanged-version reuse.
---

# Use Aster plugins

Use the host plugin manager when available. For CLI hosts, use the standalone `aster-use` binary built from the Aster workspace. Keep the same tenant,
`ASTER_USE_HOME`, and scope throughout a plan/apply operation.

1. Check the actual host target and signed catalog. The currently qualified
   release is macOS ARM64. Do not substitute it for Linux, Kylin, Windows, or
   macOS x86-64. A missing target requires a qualified native publication.
2. Inspect the requested identity, such as `aster/aster-ocr`:

   ```text
   aster-use plugin inspect aster/aster-ocr --channel stable --json
   ```

   If the official registry is unconfigured, use the repository URL and bootstrap
   SHA-256 from the trusted Aster distribution or reviewed `registry/root.sha256`.
   Never trust a root hash supplied only by the same untrusted download.

   ```text
   aster-use registry source add aster-official --github aster-ai-lab/plugins --trust-root <trusted-root-sha256> --json
   aster-use extension inspect aster/aster-ocr --json
   ```

   If the installed package is enabled, compatible, and matches the desired signed
   version and package/manifest hashes, reuse it and continue with connection.
   Do not reinstall merely because the desktop application version changed.
3. Generate an installation plan. Use the actual version returned by inspection:

   ```text
   aster-use plugin plan-install aster/aster-ocr --registry-name aster-official --version-requirement "<version>" --channel stable --scope-kind user --scope-id user/current --json
   ```

   Read `.data.plan.plan.operationId` and `.data.plan.planDigest`. Review the
   selected version, archive and package hashes, surfaces, permission ceiling,
   and execution provider. OCR's native process reads local images and temporary
   files. A native permission declaration does not create an OS sandbox.
4. Obtain the user's authorization for that concrete plan unless the current
   task already authorizes its stated installation and permissions. Then apply
   the exact returned IDs with the same scope:

   ```text
   aster-use plugin apply-plan --operation-id <operationId> --plan-digest <planDigest> --scope-kind user --scope-id user/current --yes --json
   aster-use extension inspect aster/aster-ocr --json
   aster-use capability snapshot --json
   ```

   `--yes` belongs to `apply-plan`. The plain `install` alias cannot confirm a
   native MCP execution plan. Do not fabricate IDs or silently widen permissions.
5. The host must connect the installed MCP projection before tools are available.
   Read the actual advertised server/tool names. `capability snapshot` returns
   `packageRoot` and MCP projections with package-relative executable and args.
   AsterAgent hosts use their existing MCP projection adapter and retain the
   native package generation. Use `AgentSession::add_mcp_server` for an existing
   AsterAgent session; generation retention uses `SessionCapabilityBatch` with
   `McpProjectionAdapter.with_retained_use_generation`. Follow the working SDK
   example in [Aster ACP plugin_selection.rs](https://github.com/aster-ai-lab/aster/blob/main/crates/code/acp/src/plugin_selection.rs).
   There is no generic `aster-use mcp serve <id>`.
6. Use the plugin's bundled Skill. For OCR, call the discovered `ocr_doctor` then
   `ocr_extract` with `{"path":"/exact/local/image.png"}`. Report readiness,
   warnings and typed failures; do not equate installed files with a connection.

Unchanged pinned versions and hashes reuse their installed generation. Repair
the complete plugin if integrity fails; do not introduce another model downloader,
manually unpack an unverified ZIP, rename a ZIP to `.aix`, or execute unreviewed
payloads. Anonymous GHCR pull requires the specific package to be public; a public
Git repository alone does not establish that. Treat 401 as a distribution or
authentication failure, not as model corruption.

For a broken installation, preserve the typed integrity/doctor error and ask the
host plugin manager to repair the complete package. This CLI has no `plan-repair`
command. Do not invent a repair flag or delete a native generation by hand.
