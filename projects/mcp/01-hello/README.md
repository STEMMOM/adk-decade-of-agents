# MCP-01 — Hello MCP (stdio)  
# MCP-01 —— Hello MCP（stdio）

Goal 目标: run a stdio MCP server and complete the minimal protocol loop (`initialize` → `tools/list` → `tools/call`).  
Scope is small but enforces invariants for Capability Bus → Policy Gate → Replay/Regression. | 范围很小，但为能力总线→策略门控→重放/回归锁定不变量。

---

## Files 文件
- `main.py` — `server` mode: MCP stdio server; `client` mode: spawns server and runs smoke loop. | `server` 模式：MCP stdio 服务器；`client` 模式：拉起服务器并跑冒烟循环。  
- `tests/test_mcp01_hello_smoke.py` — minimal regression for the loop. | 最小回归测试。

## Tools 工具
- `echo(text: str) -> str`  
- `add(a: int, b: int) -> int`  
- `now() -> str` (UTC ISO-8601)  
Note: server returns both `content` and sometimes `structured`; client/tests normalize via `extract_structured`. | 服务器可能返回 `content` 或 `structured`，客户端/测试通过 `extract_structured` 归一化。

---

## Invariants 不变量
- Stdout discipline: in stdio mode, stdout reserved for protocol; logs go to stderr. | stdio 模式下 stdout 仅供协议，日志写 stderr。  
- Tool results must be replayable as dict: `{"result": <value>}`; normalization order: structuredContent/structured_content → JSON from TextContent. | 工具结果可回放为字典，先读 structured*，再尝试从文本解析 JSON。

---

## Run 运行
### Server 服务器
```bash
python projects/mcp/01-hello/main.py server
```
### Client 客户端
```bash
python projects/mcp/01-hello/main.py client
```
### Tests 测试
```bash
python tests/test_mcp01_hello_smoke.py
```
