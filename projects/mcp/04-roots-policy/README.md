
# MCP-04 — Roots + Policy Gate (Resources)

Goal: add **governance** to ResourceFS by enforcing an **allowlist of repo-relative roots**.
Anything outside the allowed roots must be denied.

This is the first “constitutional” step for MCP Resources in this repo:
**context exposure is policy-bound**.

---

## Config

Environment variable:

- `MCP04_ROOTS="projects/mcp,docs"` (comma-separated, repo-relative)
- Default (when unset/empty): `projects/mcp`

Notes:
- Roots are normalized (`./` trimmed, backslashes normalized to `/`, leading/trailing `/` removed).
- Access is granted if and only if the requested relative path is:
  - exactly a root, or
  - a descendant of a root.

---

## Resources

### Policy (inspectable constitution)
- `mcpfs://repo/policy` (JSON)
  - `allowed_roots`
  - `{path}` encoding contract + examples

### Index (policy-filtered)
- `mcpfs://repo/index` (JSON)
  - lists only the allowed roots (as directory URIs)

### Governed templates
- `mcpfs://repo/dir/{path}` (JSON)
  - list directory under allowed roots
- `mcpfs://repo/file/{path}` (text)
  - read text file under allowed roots
  - on denial/error, returns JSON text with `ok=false`

---

## Critical invariant: encoded path contract

⚠️ This repo’s FastMCP template support treats `{path}` as a **single URI segment** and does not support
multi-segment captures. Therefore clients MUST URL-encode the full relative path into one segment.

Example:

- Relative path: `projects/mcp/04-roots-policy/main.py`
- Encoded: `projects%2Fmcp%2F04-roots-policy%2Fmain.py`
- URI: `mcpfs://repo/file/projects%2Fmcp%2F04-roots-policy%2Fmain.py`

Server will `unquote()` before applying policy + safe resolution.

---

## Policy behavior

### Allowed
Reading under `allowed_roots` succeeds.

### Forbidden
Reading outside `allowed_roots` is denied and returns JSON text like:

```json
{
  "ok": false,
  "error": {
    "code": "FORBIDDEN",
    "message": "path is outside allowed_roots",
    "path": ".gitignore"
  },
  "generated_at": "..."
}
````

Other error codes you may see:

* `BAD_PATH` (invalid / traversal / escapes repo root)
* `NOT_FOUND`
* `NOT_A_DIR`
* `TOO_LARGE` (size cap)

---

## Safety invariants

1. **Allowlist roots**
   All requests must be under an allowed root; otherwise `FORBIDDEN`.

2. **Repo root boundary**
   All paths are resolved under repo root and must not escape it.

3. **Read-only + idempotent**
   Resources do not mutate state.

---

## Run

```bash
python projects/mcp/04-roots-policy/main.py client
python tests/test_mcp04_roots_policy_smoke.py
```

Expected client output includes:

* `policy mime -> application/json`
* `read allowed chars -> <non-zero>`
* `read forbidden -> {"ok": false, "error": {"code":"FORBIDDEN", ...}}`

```
::contentReference[oaicite:0]{index=0}
```
