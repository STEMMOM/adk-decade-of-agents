
# MCP-03 — Resource FS (repo-root, read-only)

Goal: expose **repo content** via MCP **Resources**, with strict safety boundaries and a stable, regression-friendly access pattern.

This project provides a minimal read-only “resource filesystem” for the repo.

---

## Resources

### Static resource
- `mcpfs://repo/index`
  - JSON index of repo root (top-level entries, limited)

### Resource templates
- `mcpfs://repo/dir/{path}`
  - Directory listing under repo root (JSON)
- `mcpfs://repo/file/{path}`
  - Read a text file under repo root (text)

---

## Critical invariant: encoded path contract

⚠️ **Important**: In this repo’s FastMCP version, the URI template system does **not** support `{path*}` (multi-segment capture) or `{?path}` query templates.

Therefore, `{path}` is treated as a **single URI segment**.

To pass a multi-segment filesystem path like:

- `projects/mcp/03-resource-fs/main.py`

the client MUST URL-encode it into a single segment:

- `projects%2Fmcp%2F03-resource-fs%2Fmain.py`

The server will `unquote()` it before filesystem resolution.

If you forget to encode, you may see:
- `Unknown resource: mcpfs://repo/file/projects/mcp/...`

---

## Safety invariants

1) **Repo root boundary**
All paths must remain under repo root.
- No absolute paths
- No `..` traversal
- Enforced via `safe_resolve_under(ROOT, path)`

2) **Read-only / idempotent**
Resources must not mutate state.
Same URI should be safe to read repeatedly.

3) **Size cap**
File reads are capped (currently 512KB) to prevent huge payloads.

---

## Run

```bash
python projects/mcp/03-resource-fs/main.py client
python tests/test_mcp03_resource_fs_smoke.py
````

Expected client output includes:

* `resources/templates/list -> ['mcpfs://repo/dir/{path}', 'mcpfs://repo/file/{path}']`
* `read index mime -> application/json`
* `read file chars -> <non-zero>`

```


```
