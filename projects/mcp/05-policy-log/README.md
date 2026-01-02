# MCP-05 — Policy Decision Logging (Resources)

Goal: every resource access must produce an **auditable policy decision record**
(`ALLOW` / `DENY`) in **JSONL**.

This turns the Resource Policy Gate into an evidence-producing subsystem, enabling:
- replay (what was accessed)
- regression (did decisions change)
- governance audits (why allowed/denied)

---

## Config

### Allowed roots (inherited from MCP-04)
- `MCP04_ROOTS="projects/mcp,docs"` (comma-separated, repo-relative)
- Default when unset/empty: `projects/mcp`

### Logging
- `MCP05_LOG_ENABLED="1"` (default; set `0` to disable)
- `MCP05_LOG_PATH="runtime_data/mcp05_policy_decisions.jsonl"`
  - Default above
  - If relative, it is treated as repo-relative

---

## Resources

### Policy (inspectable constitution)
- `mcpfs://repo/policy` (JSON)
  - `allowed_roots`
  - `roots_hash` (sha256 of allowed_roots list)
  - encoded-path contract (`{path}` URL-encoding)
  - logging config

### Policy-filtered index
- `mcpfs://repo/index` (JSON)
  - lists only allowed roots

### Governed templates (decision is logged)
- `mcpfs://repo/dir/{path}` (JSON)
- `mcpfs://repo/file/{path}` (text; errors returned as JSON text)

---

## Critical invariant: encoded path contract

In this repo’s FastMCP template support, `{path}` is a **single URI segment**.
Clients MUST URL-encode full repo-relative paths into one segment (`/` → `%2F`).

Example:

- rel: `projects/mcp/05-policy-log/main.py`
- encoded: `projects%2Fmcp%2F05-policy-log%2Fmain.py`
- uri: `mcpfs://repo/file/projects%2Fmcp%2F05-policy-log%2Fmain.py`

Server will `unquote()` before applying policy + safe resolution.

---

## Decision log (JSONL)

Each resource access appends **one JSON line** with schema:

- `schema`: `mcp-policy-decision/v1`
- `ts`, `request_id`, `uri`
- `resource_kind`: `"file"` or `"dir"`
- `path_param_raw` (encoded segment)
- `path_decoded` (decoded repo-relative path)
- `decision`: `"ALLOW"` or `"DENY"`
- `reason.code`, `reason.message`
- `policy.allowed_roots`, `policy.roots_hash`

### Why `idempotentHint` is false
Even though reads don’t mutate repo content, they **append a decision record**.
So from an observability standpoint, resource reads have a side-effect.

---

## Run

```bash
python projects/mcp/05-policy-log/main.py client
python tests/test_mcp05_policy_log_smoke.py

Inspect logs (default path)
tail -n 10 runtime_data/mcp05_policy_decisions.jsonl
You should see at least:
one ALLOW record (reading under projects/mcp)
one DENY record (e.g. reading .gitignore)