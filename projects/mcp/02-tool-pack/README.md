
# MCP-02 — Tool Pack + Envelope v1

Goal: provide a reusable ToolPack where **every tool returns a stable envelope** suitable for governance and replay.

---

## Envelope (toolpack-envelope/v1)

Success:

```json
{
  "ok": true,
  "result": "<any>",
  "error": null,
  "meta": {
    "schema": "toolpack-envelope/v1",
    "tool": "<tool_name>",
    "ts": "<utc-iso>"
  }
}
````

Failure:

```json
{
  "ok": false,
  "result": null,
  "error": {
    "code": "<CODE>",
    "message": "<HUMAN_MESSAGE>",
    "detail": {}
  },
  "meta": {
    "schema": "toolpack-envelope/v1",
    "tool": "<tool_name>",
    "ts": "<utc-iso>"
  }
}
```

---

## Tools

* `echo(text)` -> ok(text)
* `add(a,b)` -> ok(a+b)
* `now()` -> ok(utc_iso)
* `uuid()` -> ok(uuid4)
* `divide(a,b)` -> ok(a/b) or fail(DIV_BY_ZERO)

---

## Invariants

1. **Replayable Output**
   All tool results must be normalizable into a dict envelope. We do not rely on SDK-specific structured fields.

2. **SDK-Tolerant Extraction**
   Client/test must use `extract_structured()`:

* prefer `structuredContent` / `structured_content`
* fallback to JSON parsing from `TextContent.text`

This guarantees stable regression signals across MCP SDK versions.

---

## Run

```bash
python projects/mcp/02-tool-pack/main.py client
python tests/test_mcp02_tool_pack_smoke.py
```

```



MCP-02 的“结构承诺”
这一集真正的承诺是：

> **从此以后，任何能力都必须返回 envelope。**  
> 这使得 Capability Bus 能做：  
> - policy check（ok/err 统一口径）  
> - replay regression（result 对比）  
> - observability（meta 中追加 run_id / latency / cost）

---


