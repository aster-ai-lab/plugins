# Aster OCR

Local image recognition packaged as one native `.aix` plugin. It includes
`aster-use-ocr`, ONNX Runtime, PP-OCRv6 detection and recognition models,
third-party notices, the `ocr` stdio MCP surface, and the `aster-use-ocr` Skill.

The desktop host renders scanned PDF pages separately. This plugin accepts
bounded local images; it does not fetch models or send images off the device.
The document MCP profile limits the detection edge to 1536 pixels; the standalone
general profile retains the 4000-pixel limit.

`aster-use-extension.acl` is the release source template. The Aster workspace's
`crates/ocr/scripts/package_plugin.py` supplies verified native build inputs,
copies the canonical Skill from `crates/ocr/skills/aster-use-ocr`, and generates a
content version before invoking the native AIX builder and catalog preparer.
Only targets present in the signed catalog are released and supported.
